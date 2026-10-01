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