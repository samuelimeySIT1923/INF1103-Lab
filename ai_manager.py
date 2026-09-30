import json
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Tuple

from google import genai
from google.genai import errors as genai_errors
from google.genai import types


logger = logging.getLogger(__name__)


#-----------------------------------------------------------------------------------#
#Establish models

default_model = "gemini-3.8-flash"
fallback_models = ["gemini-3.7-flash", "gemini-3.5-flash-lite"]
retryable_codes = {429, 500, 502, 503, 504}


#-----------------------------------------------------------------------------------#
#Establish columns, allowed values, and fallback values

model_columns = [
    "date_and_time",
    "retailer",
    "category",
    "transaction_amount",
    "transaction_type",
]

output_columns = ["transaction_id"] + model_columns

fallback_id_prefix = "TXN-ERR"

allowed_categories = [
    "Food",
    "Transport",
    "Groceries",
    "Entertainment",
    "Bills",
    "Shopping",
    "Misc",
]

allowed_types = ["Outgoing", "Incoming"]

fallback_category = "Misc"
fallback_type = "Outgoing"


#-----------------------------------------------------------------------------------#
#Establish validation and cleaning functions

def validate_schema(data: Any) -> Tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Record is not a JSON object."

    for col in model_columns:
        if col not in data:
            return False, f"Missing required column: '{col}'"

    if data["transaction_type"] not in allowed_types:
        return False, (
            f"Invalid transaction_type '{data['transaction_type']}'; "
            f"must be one of {allowed_types}."
        )

    try:
        if float(data["transaction_amount"]) < 0.0:
            return False, "transaction_amount must be non-negative."
    except (ValueError, TypeError):
        return False, "transaction_amount must be a valid number."

    for col in ("retailer", "category"):
        value = data[col]
        if not isinstance(value, str) or not value.strip():
            return False, f"Column '{col}' must be a non-empty string."

    if data["category"] not in allowed_categories:
        return False, (
            f"Invalid category '{data['category']}'; "
            f"must be one of {allowed_categories}."
        )

    return True, "Schema validated"


def _fallback_id() -> str:
    return f"{fallback_id_prefix}-{uuid.uuid4().hex[:6].upper()}"


def create_fallback_record(raw_record: Any) -> Dict[str, Any]:
    return {
        "transaction_id": _fallback_id(),
        "date_and_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "retailer": "Unknown Merchant",
        "category": fallback_category,
        "transaction_amount": 0.0,
        "transaction_type": fallback_type,
    }


def _normalise(record: Dict[str, Any]) -> Dict[str, Any]:
    clean = {"transaction_id": ""}
    clean.update({col: record[col] for col in model_columns})
    clean["transaction_amount"] = round(abs(float(clean["transaction_amount"])), 2)
    return clean


def is_fallback_record(record: Dict[str, Any]) -> bool:
    return str(record.get("transaction_id", "")).startswith(fallback_id_prefix)


#common "fancy" characters found in bank/PDF exports, mapped to plain ASCII
_char_map = str.maketrans({
    "\u2022": "*",   
    "\u00b7": "*",
    "\u2013": "-",
    "\u2014": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00a0": " ",
})


def _ascii_safe(text: str) -> str:
    return text.translate(_char_map).encode("ascii", "backslashreplace").decode("ascii")


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {_ascii_safe(str(k)): _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    if isinstance(value, str):
        return _ascii_safe(value)
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return _ascii_safe(str(value))


#-----------------------------------------------------------------------------------#
#Establish prompt templates

_schema_block = """{{
  "source_index": <the integer index of the input record>,
  "date_and_time": "YYYY-MM-DD HH:MM:SS or YYYY-MM-DD",
  "retailer": "Merchant or entity name (e.g. NTUC FairPrice, Grab, Employer)",
  "category": "Exactly one of: {categories}",
  "transaction_amount": <positive float>,
  "transaction_type": "Exactly one of: {types}"
}}"""

_rules = """Rules:
1. Convert dates to ISO format ('YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS').
2. Strip currency symbols (S$, $) and commas; amount is a positive float with 2 decimals.
3. 'category' must be exactly one of the allowed categories. If nothing fits clearly, use 'Misc'.
   Use 'Groceries' for supermarkets/food shopping and 'Food' for restaurants, cafes and delivery.
   Use 'Bills' for utilities, rent, phone, insurance and recurring payments.
   Use 'Shopping' for clothing, electronics, online shopping, personal care and other retail purchases.
4. 'transaction_type' is 'Outgoing' when money leaves the account and 'Incoming' when money is received
   (salary, refunds, cashback, incoming transfers)."""


def _schema_text() -> str:
    categories = ", ".join(f"'{c}'" for c in allowed_categories)
    types_ = ", ".join(f"'{t}'" for t in allowed_types)
    return _schema_block.format(categories=categories, types=types_)


def build_batch_prompt(indexed_records: List[Tuple[int, Any]]) -> str:
    payload = [{"index": i, "record": _sanitize(r)} for i, r in indexed_records]

    return f"""You are an expert financial transaction extraction engine.
Convert ALL of the raw bank statement entries below into a single JSON ARRAY.
Each element MUST match this exact schema:

{_schema_text()}

{_rules}
5. Return exactly one object per input record, echoing its 'index' as 'source_index'.
6. Output ONLY the JSON array, nothing else.

Raw input records:
{json.dumps(payload, indent=2, ensure_ascii=True)}
"""


def build_single_prompt(raw_record: Any) -> str:
    schema = _schema_text().replace(
        '  "source_index": <the integer index of the input record>,\n', ""
    )
    return f"""You are an expert financial transaction extraction engine.
Convert this bank statement record into ONE JSON object matching this exact schema:

{schema}

{_rules}
5. Output ONLY valid JSON.

Raw input record:
{json.dumps(_sanitize(raw_record))}
"""


#-----------------------------------------------------------------------------------#
#Establish gemini call function with retry logic

def _call_gemini(
    prompt: str,
    api_key: str,
    model_name: str,
    max_retries: int = 3,
) -> Any:
    api_key = (api_key or "").strip()
    if not api_key.isascii():
        raise ValueError(
            "The API key contains non-ASCII characters (for example pasted '\u2022' "
            "password dots). Re-copy the key from Google AI Studio."
        )
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(thinking_level="low"),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    if not prompt.isascii():
        prompt = _ascii_safe(prompt)

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name, contents=prompt, config=config
            )
            return json.loads(response.text or "")
        except (genai_errors.APIError, json.JSONDecodeError) as exc:
            if not _is_transient(exc) or attempt == max_retries:
                raise
            wait = min(60, 5 * 2 ** attempt) + random.uniform(0, 3)
            logger.warning(
                "%s call failed (attempt %d/%d): %s. Retrying in %.0fs.",
                model_name, attempt, max_retries, exc, wait,
            )
            time.sleep(wait)


def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, json.JSONDecodeError):
        return True
    return getattr(exc, "code", None) in retryable_codes


def _call_with_fallback(prompt: str, api_key: str, model_name: str) -> Any:
    models = [model_name] + [m for m in fallback_models if m != model_name]
    last_exc: Exception = RuntimeError("No models to try")

    for i, model in enumerate(models):
        try:
            return _call_gemini(prompt, api_key, model, max_retries=4 if i == 0 else 2)
        except Exception as exc:
            if not _is_transient(exc):
                raise
            last_exc = exc
            if i + 1 < len(models):
                logger.warning("%s is unavailable (%s). Switching to %s.",
                               model, exc, models[i + 1])

    raise last_exc


#-----------------------------------------------------------------------------------#
#Establish batch extraction function

def _extract_chunk(
    indexed_records: List[Tuple[int, Any]],
    api_key: str,
    model_name: str,
) -> Dict[int, Dict[str, Any]]:
    results: Dict[int, Dict[str, Any]] = {}
    expected = {i for i, _ in indexed_records}

    try:
        data = _call_with_fallback(build_batch_prompt(indexed_records), api_key, model_name)
    except Exception:
        logger.exception("Gemini batch call failed")
        return results

    if not isinstance(data, list):
        data = [data]

    for item in data:
        if not isinstance(item, dict):
            continue
        idx = item.pop("source_index", None)
        if idx not in expected or idx in results:
            logger.warning("Ignoring item with unexpected/duplicate source_index=%r", idx)
            continue

        ok, msg = validate_schema(item)
        if ok:
            results[idx] = _normalise(item)
        else:
            logger.warning("Record %s failed validation: %s", idx, msg)

    return results


def extract_batch_standardized_transactions(
    raw_records: List[Any],
    api_key: str,
    model_name: str = default_model,
    chunk_size: int = 50,
    delay_between_calls: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Convert raw records into standardised transactions (see output_columns).

    Records are sent in chunks of `chunk_size` (one API call per chunk) so large
    statements don't exceed output token limits. Set `delay_between_calls`
    (e.g. 12.5 seconds for a 5 RPM limit) to space out calls.

    The returned list always has the same length and order as `raw_records`;
    any record that could not be parsed gets a fallback record.
    """
    if not raw_records:
        return []

    logger.info("Extracting %d records with %s (chunk size %d)...",
                len(raw_records), model_name, chunk_size)

    indexed = list(enumerate(raw_records))
    results: Dict[int, Dict[str, Any]] = {}

    for start in range(0, len(indexed), chunk_size):
        if start > 0 and delay_between_calls > 0:
            time.sleep(delay_between_calls)
        chunk = indexed[start:start + chunk_size]
        results.update(_extract_chunk(chunk, api_key, model_name))

    output = []
    failed = 0
    for i, raw in enumerate(raw_records):
        if i in results:
            output.append(results[i])
        else:
            failed += 1
            logger.warning("No valid result for record %d: %s", i, str(raw)[:80])
            output.append(create_fallback_record(raw))

    logger.info("Extraction complete: %d succeeded, %d fell back.",
                len(raw_records) - failed, failed)
    return output


#-----------------------------------------------------------------------------------#
#Establish single-record extraction function

def extract_standardized_transaction(
    raw_record: Any,
    api_key: str,
    model_name: str = default_model,
) -> Dict[str, Any]:
    try:
        data = _call_with_fallback(build_single_prompt(raw_record), api_key, model_name)
        ok, msg = validate_schema(data)
        if ok:
            return _normalise(data)
        logger.warning("Single record failed validation: %s", msg)
    except Exception:
        logger.exception("Single record Gemini call failed")

    return create_fallback_record(raw_record)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )