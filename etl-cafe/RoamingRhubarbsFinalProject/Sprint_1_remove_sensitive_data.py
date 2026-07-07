"""
remove_sensitive_data.py
------------------------
Strips personally identifiable information (PII) from SuperCafe transaction CSV files.

Removes:
  - Column 2: customer name
  - Column 6: card number

Usage:
  # Process a single file (output saved alongside input with '_anonymised' suffix):
  python remove_sensitive_data.py data/leeds_28-03-2025_09-00-00_in_.csv

  # Process all CSVs in a folder:
  python remove_sensitive_data.py data/

  # Specify a custom output folder:
  python remove_sensitive_data.py data/ --output-dir cleaned/
"""

# argparse lets us pass arguments in the command line (e.g. the filename)
# sys lets us exit the script with an error if something goes wrong
# Path from pathlib is a cleaner way to handle file paths than plain strings
import argparse
import sys
from pathlib import Path

# pandas is the library we use to read, edit, and save CSV files
import pandas as pd


# Columns that contain PII and must be removed.
# The CSV has no header row, so these are zero-based integer positions.


SENSITIVE_COLUMNS = [2, 6]  # customer_name, card_number (columns 2 and 6)

#This is a refernce map so we know what each column contains. 
COLUMN_NAMES = {
    0: "datetime",
    1: "location",
    2: "customer_name",   # <-- REMOVED
    3: "items",
    4: "total",
    5: "payment_type",
    6: "card_number",     # <-- REMOVED
}

#This function does the actual work of removing the sensitive columns from one file.
def anonymise_file(input_path: Path, output_path: Path) -> int:
    
    """
    Load a single CSV, drop PII columns, and save to output_path.
    Returns the number of rows processed.
    """
    #Read the CSV into a pandas dataframe (like a table in memory).
    df = pd.read_csv(input_path, header=None, dtype=str)

    # Check the file has the expected number of columns, if not, raise an error. 
    if df.shape[1] != len(COLUMN_NAMES):
        raise ValueError(
            f"{input_path.name}: expected {len(COLUMN_NAMES)} columns, "
            f"got {df.shape[1]}. Is this the right file format?"
        )

    #drop the snesitive colummns from the dataframe. 
    df.drop(columns=SENSITIVE_COLUMNS, inplace=True)
    #create the output folder if it doesnt exist, then save the cleaned file. 
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, header=False)
    #Return the number of rows so we can print it in the same summary.
    return len(df)

#This function builds the output filename by adding "_anonymised" to the orginal filename."
def build_output_path(input_path: Path, output_dir: Path | None) -> Path:
    """Work out where to save the cleaned file."""
    stem = input_path.stem + "_anonymised"
    filename = stem + input_path.suffix
    if output_dir:
        return output_dir / filename
    return input_path.parent / filename

#This is the main function that runs when you execute the script.
def main():
    parser = argparse.ArgumentParser(
        description="Remove PII (customer name, card number) from SuperCafe CSV files."
    )
    parser.add_argument(
        "input",
        help="Path to a CSV file, or a folder containing CSV files."
    )
    parser.add_argument(
        "--output-dir", "-o",
        default=None,
        help="Folder to write anonymised files into. "
             "Defaults to the same folder as each input file."
    )
    args = parser.parse_args()

    # Convert the input arguemnt into a path object.
    input_path = Path(args.input)
    output_dir = Path(args.output_dir) if args.output_dir else None

    # Collect files to process. (process all CSVs)
    if input_path.is_dir():
        csv_files = sorted(input_path.glob("*.csv"))
        if not csv_files:
            print(f"No CSV files found in '{input_path}'.")
            sys.exit(1)
    elif input_path.is_file():
        csv_files = [input_path]
    else:
        print(f"Error: '{input_path}' is not a valid file or directory.")
        sys.exit(1)

    # Process each file. print whether it succeeded or failed. 
    total_rows = 0
    errors = []

    for csv_file in csv_files:
        output_path = build_output_path(csv_file, output_dir)
        try:
            rows = anonymise_file(csv_file, output_path)
            total_rows += rows
            print(f"  ✓  {csv_file.name}  →  {output_path}  ({rows} rows)")
        except Exception as e:
            errors.append(csv_file.name)
            print(f"  ✗  {csv_file.name}: {e}")

    # Summary - prints how many files and rows were processed.
    print()
    print(f"Done. {len(csv_files) - len(errors)}/{len(csv_files)} file(s) processed, "
          f"{total_rows} rows anonymised.")
    if errors:
        print(f"Failed: {', '.join(errors)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# HOW TO RUN THIS SCRIPT
# =============================================================================
# Make sure the CSV file is in the same folder as this script, then run:
#
#   Process a single file:
#   python Sprint_1.py "leeds_28-03-2025_09-00-00(in).csv"
#
#   Process all CSVs in a folder:
#   python Sprint_1.py data/
#
#   Save the output to a specific folder:
#   python Sprint_1.py "leeds_28-03-2025_09-00-00(in).csv" --output-dir cleaned/