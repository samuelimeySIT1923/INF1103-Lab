import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import data_manager


sample_records = [
    {
        "date_and_time": "2026-08-03 12:30:00",
        "retailer": "NTUC FairPrice",
        "category": "Groceries",
        "transaction_amount": 42.5,
        "transaction_type": "Outgoing",
    },
    {
        "date_and_time": "2026-08-15",
        "retailer": "Grab",
        "category": "Transport",
        "transaction_amount": 18.0,
        "transaction_type": "Outgoing",
    },
    {
        "date_and_time": "2025-09-01",
        "retailer": "Employer",
        "category": "Misc",
        "transaction_amount": 2500.0,
        "transaction_type": "Incoming",
    },
]


def test_load_creates_missing_file(tmp_path):
    path = tmp_path / "data" / "collated_data.csv"
    df = data_manager.load_collated_data(path)
    assert df.empty
    assert list(df.columns) == data_manager.columns
    assert path.exists()


def test_save_then_load_round_trip(tmp_path):
    path = tmp_path / "collated_data.csv"
    saved = data_manager.save_collated_data(sample_records, path)
    loaded = data_manager.load_collated_data(path)
    assert len(saved) == 3
    assert list(loaded["transaction_id"]) == ["00001", "00002", "00003"]
    assert list(loaded["retailer"]) == ["NTUC FairPrice", "Grab", "Employer"]


def test_save_appends_and_continues_ids(tmp_path):
    path = tmp_path / "collated_data.csv"
    data_manager.save_collated_data(sample_records[:2], path)
    df = data_manager.save_collated_data(sample_records[2:], path)
    assert list(df["transaction_id"]) == ["00001", "00002", "00003"]


def test_save_empty_list_changes_nothing(tmp_path):
    path = tmp_path / "collated_data.csv"
    data_manager.save_collated_data(sample_records, path)
    df = data_manager.save_collated_data([], path)
    assert len(df) == 3


def test_update_overwrites_file(tmp_path):
    path = tmp_path / "collated_data.csv"
    df = data_manager.save_collated_data(sample_records, path)
    df = df[df["retailer"] != "Grab"]

    data_manager.update_collated_data(df, path)

    loaded = data_manager.load_collated_data(path)
    assert list(loaded["retailer"]) == ["NTUC FairPrice", "Employer"]
    assert list(loaded["transaction_id"]) == ["00001", "00003"]


def test_corrupt_file_is_quarantined_not_lost(tmp_path):
    path = tmp_path / "collated_data.csv"
    garbage = b"\xff\xfe\x00not a csv\x00\x9d\x81"
    path.write_bytes(garbage)

    df = data_manager.load_collated_data(path)

    assert df.empty
    backups = list(tmp_path.glob("collated_data.corrupt-*.csv"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == garbage


def test_file_with_wrong_columns_is_quarantined(tmp_path):
    path = tmp_path / "collated_data.csv"
    path.write_text("foo,bar\n1,2\n", encoding="utf-8")

    df = data_manager.load_collated_data(path)

    assert df.empty
    assert len(list(tmp_path.glob("collated_data.corrupt-*.csv"))) == 1


def test_load_drops_fallback_rows_and_maps_legacy_types(tmp_path):
    path = tmp_path / "collated_data.csv"
    path.write_text(
        "transaction_id,date_and_time,retailer,category,transaction_amount,transaction_type\n"
        "00001,2026-08-03,Grab,Transport,12.0,Expense\n"
        "TXN-ERR-ABC123,2026-08-04,Unknown Merchant,Misc,0.0,Outgoing\n"
        "00002,2026-08-05,Employer,Misc,2500.0,Income\n",
        encoding="utf-8",
    )

    df = data_manager.load_collated_data(path)

    assert list(df["transaction_id"]) == ["00001", "00002"]
    assert list(df["transaction_type"]) == ["Outgoing", "Incoming"]


def test_filter_records(tmp_path):
    df = data_manager.save_collated_data(sample_records, tmp_path / "collated_data.csv")

    assert len(data_manager.filter_records(df)) == 3
    assert len(data_manager.filter_records(df, month=8)) == 2
    assert len(data_manager.filter_records(df, month=8, year=2025)) == 0
    assert len(data_manager.filter_records(df, month=9, year=2025)) == 1
    assert len(data_manager.filter_records(df, category="Transport")) == 1
    assert len(data_manager.filter_records(df, transaction_type="Incoming")) == 1
    assert len(data_manager.filter_records(df, retailer="ntuc")) == 1
    assert len(data_manager.filter_records(df, month=8, category="Groceries")) == 1


def test_filter_handles_mixed_date_formats_and_bad_dates(tmp_path):
    records = sample_records + [dict(sample_records[0], date_and_time="not a date")]
    df = data_manager.save_collated_data(records, tmp_path / "collated_data.csv")

    assert len(data_manager.filter_records(df, month=8, year=2026)) == 2
    assert len(data_manager.filter_records(df)) == 4


def test_available_months(tmp_path):
    df = data_manager.save_collated_data(sample_records, tmp_path / "collated_data.csv")

    assert data_manager.get_available_months(df) == [8, 9]
    assert data_manager.get_available_month_years(df) == [(2025, 9), (2026, 8)]
    assert data_manager.get_available_months(data_manager.empty_records()) == []
    assert data_manager.get_available_month_years(data_manager.empty_records()) == []


def test_audit_trail_records_and_reloads(tmp_path):
    path = tmp_path / "audit_trail.csv"
    assert data_manager.load_audit_trail(path).empty

    data_manager.record_audit("00001", "EDIT", {"retailer": "Grab"}, {"retailer": "Gojek"}, path)
    data_manager.record_audit("00002", "ARCHIVE", {"retailer": "NTUC"}, path=path)

    audit_df = data_manager.load_audit_trail(path)
    assert list(audit_df.columns) == data_manager.audit_columns
    assert list(audit_df["audit_id"]) == ["00001", "00002"]
    assert list(audit_df["transaction_id"]) == ["00001", "00002"]
    assert list(audit_df["action"]) == ["EDIT", "ARCHIVE"]
    assert audit_df.loc[0, "new_retailer"] == "Gojek"


def test_corrupt_audit_trail_is_quarantined(tmp_path):
    path = tmp_path / "audit_trail.csv"
    path.write_bytes(b"\xff\xfe\x00junk")

    data_manager.record_audit("00001", "EDIT", path=path)

    assert len(data_manager.load_audit_trail(path)) == 1
    assert len(list(tmp_path.glob("audit_trail.corrupt-*.csv"))) == 1