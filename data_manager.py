import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


logger = logging.getLogger(__name__)


#-----------------------------------------------------------------------------------#
#Establish columns and data path for collated data

columns = [
    "transaction_id",
    "date_and_time",
    "retailer",
    "category",
    "transaction_amount",
    "transaction_type",
]

data_path = Path("data/collated_data.csv")
audit_path = Path("data/audit_trail.csv")

fallback_id_prefix = "TXN-ERR"
id_width = 5
legacy_type_map = {"Expense": "Outgoing", "Income": "Incoming"}


#-----------------------------------------------------------------------------------#
#Establish helper functions for IDs and file handling

def empty_records() -> pd.DataFrame:
    """Return an empty DataFrame with the standard columns."""
    return pd.DataFrame(columns=columns)


def assign_sequential_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Give every row a zero-padded numeric ID, keeping IDs that are already numeric."""
    df = df.copy()
    ids = df["transaction_id"].astype(str).str.strip()
    is_numeric = ids.str.isdigit()

    next_id = int(ids[is_numeric].astype(int).max()) + 1 if is_numeric.any() else 1

    new_ids = ids.copy()
    new_ids[is_numeric] = ids[is_numeric].astype(int).map(lambda n: f"{n:0{id_width}d}")
    for idx in df.index[~is_numeric]:
        new_ids[idx] = f"{next_id:0{id_width}d}"
        next_id += 1

    df["transaction_id"] = new_ids
    return df


def write_records(df: pd.DataFrame, path: Path = data_path) -> None:
    """Write the DataFrame to CSV through a temp file so a failed write cannot corrupt the data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    df[columns].to_csv(temp_path, index=False)
    os.replace(temp_path, path)


def quarantine_corrupt_file(path: Path = data_path) -> Optional[Path]:
    """Rename an unreadable data file so it is kept for inspection instead of overwritten."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.stem}.corrupt-{stamp}{path.suffix}")
    try:
        os.replace(path, backup_path)
    except OSError:
        logger.exception("Could not move corrupt data file %s", path)
        return None
    logger.warning("Corrupt data file moved to %s", backup_path)
    return backup_path



#-----------------------------------------------------------------------------------#
#Establish functions to load and save collated data

def load_collated_data(path: Path = data_path) -> pd.DataFrame:
    """Load all saved records, creating the file if missing and recovering if it is corrupt."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists() or path.stat().st_size == 0:
            df = empty_records()
            write_records(df, path)
            return df

        try:
            raw_df = pd.read_csv(path, dtype={"transaction_id": str})
        except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError, ValueError):
            logger.exception("Data file %s could not be parsed", path)
            raw_df = None

        if raw_df is None or not any(col in raw_df.columns for col in columns):
            quarantine_corrupt_file(path)
            df = empty_records()
            write_records(df, path)
            return df

        df = raw_df.copy()
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]

        df = df[~df["transaction_id"].astype(str).str.startswith(fallback_id_prefix)]
        df = df.reset_index(drop=True)

        df["transaction_type"] = df["transaction_type"].replace(legacy_type_map)

        df = assign_sequential_ids(df)

        if not df.equals(raw_df):
            write_records(df, path)
        return df

    except OSError:
        logger.exception("Could not access data file %s", path)
        return empty_records()


def save_collated_data(
    new_records: List[Dict[str, Any]],
    path: Path = data_path,
) -> pd.DataFrame:
    """Append new standardized records to the CSV and return the updated DataFrame."""
    existing_df = load_collated_data(path)
    if not new_records:
        return existing_df

    new_df = pd.DataFrame(new_records, columns=columns)
    new_df["transaction_id"] = ""  # real IDs are assigned below

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = assign_sequential_ids(combined_df)

    try:
        write_records(combined_df, path)
    except OSError:
        logger.exception("Could not save records to %s", path)
        return existing_df
    return combined_df

def record_audit(
        transaction_id: str,
        action: str,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        path: Path = audit_path,
) -> None:
    """Record a transaction edit/archive in the audit trail"""

    audit_columns = [
        "audit_id",
        "transaction_id",
        "action",
        "timestamp",
        "old_date_and_time",
        "old_retailer",
        "old_category",
        "old_transaction_amount",
        "old_transaction_type",
        "new_date_and_time",
        "new_retailer",
        "new_category",
        "new_transaction_amount",
        "new_transaction_type",
    ]

    if path.exists() and path.stat().st_size > 0:
        audit_df = pd.read_csv(path)
    else:
        audit_df = pd.DataFrame(columns=audit_columns)

    # Now it is safe to use audit_df
    if audit_df.empty:
        next_id = 1
    else:
        next_id = len(audit_df) + 1
    old_data = old_data or {}
    new_data = new_data or {}

    audit_record = {
        "audit_id": f"{next_id:05d}",
        "transaction_id": transaction_id,
        "action": action,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        "old_date_and_time": old_data.get("date_and_time", ""),
        "old_retailer": old_data.get("retailer", ""),
        "old_category": old_data.get("category", ""),
        "old_transaction_amount": old_data.get("transaction_amount", ""),
        "old_transaction_type": old_data.get("transaction_type", ""),

        "new_date_and_time": new_data.get("date_and_time", ""),
        "new_retailer": new_data.get("retailer", ""),
        "new_category": new_data.get("category", ""),
        "new_transaction_amount": new_data.get("transaction_amount", ""),
        "new_transaction_type": new_data.get("transaction_type", ""),
    }

    audit_df = pd.concat(
        [audit_df, pd.DataFrame([audit_record])],
        ignore_index=True,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    audit_df.to_csv(path, index=False)

#-----------------------------------------------------------------------------------#
#Establish filter and query functions

def get_available_months(df: pd.DataFrame) -> List[int]:
    """Return the sorted month numbers (1-12) that appear in the records."""
    dates = pd.to_datetime(df["date_and_time"], errors="coerce")
    return sorted(int(m) for m in dates.dt.month.dropna().unique())


def filter_records(
    df: pd.DataFrame,
    month: Optional[int] = None,
    year: Optional[int] = None,
    category: Optional[str] = None,
    transaction_type: Optional[str] = None,
    retailer: Optional[str] = None,
) -> pd.DataFrame:
    """
    Return the records matching every filter that is given (None means no filter).

    `retailer` is a case-insensitive partial match; the others are exact.
    Records with an unreadable date are dropped when filtering by month or year.
    """
    mask = pd.Series(True, index=df.index)

    if month is not None or year is not None:
        dates = pd.to_datetime(df["date_and_time"], errors="coerce")
        if month is not None:
            mask &= dates.dt.month == month
        if year is not None:
            mask &= dates.dt.year == year

    if category is not None:
        mask &= df["category"] == category

    if transaction_type is not None:
        mask &= df["transaction_type"] == transaction_type

    if retailer is not None:
        mask &= df["retailer"].astype(str).str.contains(retailer, case=False, regex=False)

    return df[mask].reset_index(drop=True)