from pathlib import Path

from ETL.Extract import extract_data, get_data


def test_extract_data_reads_csv_rows_into_dictionaries(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "28/03/2025 09:00,Leeds,Ada Lovelace,Latte - 3.50,3.50,card,1234567890123456\n"
        "28/03/2025 09:05,Leeds,Grace Hopper,Tea - 2.00,2.00,cash,\n",
        encoding="utf-8",
    )

    rows = extract_data(csv_file)

    assert rows == [
        {
            "timestamp": "28/03/2025 09:00",
            "location": "Leeds",
            "customer name": "Ada Lovelace",
            "items ordered": "Latte - 3.50",
            "total amount": "3.50",
            "payment method": "card",
            "card number": "1234567890123456",
        },
        {
            "timestamp": "28/03/2025 09:05",
            "location": "Leeds",
            "customer name": "Grace Hopper",
            "items ordered": "Tea - 2.00",
            "total amount": "2.00",
            "payment method": "cash",
            "card number": "",
        },
    ]


def test_extract_data_ignores_blank_and_incomplete_rows(tmp_path):
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(
        "\n"
        "bad,row\n"
        "28/03/2025 09:00,Leeds,Ada Lovelace,Latte - 3.50,3.50,card,1234567890123456\n",
        encoding="utf-8",
    )

    rows = extract_data(csv_file)

    assert len(rows) == 1
    assert rows[0]["location"] == "Leeds"


def test_get_data_uses_provided_data_without_reading_file():
    supplied_rows = [{"timestamp": "already extracted"}]

    assert get_data(data=supplied_rows) is supplied_rows


def test_get_data_raises_for_missing_explicit_file():
    missing_file = Path("does-not-exist.csv")

    try:
        get_data(file_path=str(missing_file))
    except FileNotFoundError as error:
        assert "CSV file not found" in str(error)
    else:
        raise AssertionError("Expected FileNotFoundError for missing CSV")
