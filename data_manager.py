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