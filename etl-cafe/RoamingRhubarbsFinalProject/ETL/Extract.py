import csv
import io
from pathlib import Path
from typing import Optional

# Global constant eliminates triple redundancy and acts as a Single Source of Truth
FIELDNAMES = [
    'timestamp',
    'location',
    'customer name',
    'items ordered',
    'total amount',
    'payment method',
    'card number',
]


def _parse_csv_stream(reader) -> list:
    """
    Internal helper that processes an iterable CSV reader stream.
    Safely handles BOM characters, skips headers, and filters out truncated lines.
    """
    data = []
    for row in reader:
        if not row:
            continue

        # Strip Byte Order Mark (BOM) if present in the data stream
        if row[0].startswith('\ufeff'):
            row[0] = row[0].lstrip('\ufeff')

        # Skip header rows gracefully (protects both S3 Lambda and local POC)
        if row[0].lower() == 'timestamp' or 'items ordered' in row:
            continue

        # Ignore malformed or truncated rows that won't map cleanly
        if len(row) < len(FIELDNAMES):
            continue

        data.append(dict(zip(FIELDNAMES, row)))
    return data


def extract_data(file_path: str) -> list:
    """
    Extract rows from a local CSV file path. 
    Maintains support for your local Dockerized POC pipeline and unit tests.
    """
    with open(file_path, mode='r', encoding='utf-8', newline='') as file:
        reader = csv.reader(file)
        return _parse_csv_stream(reader)


def extract_data_from_string(csv_text: str) -> list:
    """
    Extract rows from an S3 CSV string stream.
    Streams memory efficiently via StringIO for the AWS Lambda pipeline.
    """
    string_io = io.StringIO(csv_text)
    reader = csv.reader(string_io)
    return _parse_csv_stream(reader)


def get_data(data=None, file_path: Optional[str] = None, search_dir: Optional[str] = None) -> list:
    """
    Return extracted data. Used by local main.py execution framework.

    - If `data` is provided, return it unchanged.
    - If `file_path` is provided, load from that CSV (error if missing).
    - Otherwise search `search_dir` (or current working dir) for the most
      recently modified `*.csv` file and load it.
    """
    if data is not None:
        return data

    if file_path:
        csv_path = Path(file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
    else:
        search_path = Path(search_dir) if search_dir else Path.cwd()
        candidates = sorted(
            search_path.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not candidates:
            raise FileNotFoundError(f"No CSV files found in {search_path}")
        csv_path = candidates[0]

    return extract_data(str(csv_path))


def print_data_table(data: list):
    """
    Prints extracted data in a clean tabular format for local debugging.
    """
    if not data:
        print('No data to display.')
        return

    print(' | '.join(FIELDNAMES))
    print('-' * 120)
    for row in data:
        print(' | '.join(str(row.get(key, '')) for key in FIELDNAMES))


# Execution block moved to the absolute bottom of the module (PEP 8 Standard)
if __name__ == '__main__':
    try:
        local_data = get_data()
        print_data_table(local_data)
    except FileNotFoundError as e:
        print(f"Local Execution Notice: {e}")