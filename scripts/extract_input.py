#!/usr/bin/env python3
"""
CSV Input Column Extractor

This script extracts the 'input' column from a CSV file and saves it to a new CSV file.
Designed to work with datasets containing instruction, input, and output columns.

Usage:
    python extract_input.py --input <input_file> --output <output_file>

Example:
    python scripts/extract_input.py --input dataset.csv --output output.csv
"""

import argparse
import csv
import sys
import os
from pathlib import Path


def setup_argument_parser():
    """
    Set up command-line argument parser with input and output file options.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Extract input column from CSV dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Example: python extract_input.py --input dataset.csv --output output.csv'
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Path to input CSV file containing the dataset'
    )
    
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Path to output CSV file for extracted input data'
    )
    
    return parser


def validate_input_file(input_path):
    """
    Validate that the input file exists and is readable.
    
    Args:
        input_path (str): Path to the input CSV file
        
    Returns:
        bool: True if file is valid, False otherwise
        
    Raises:
        SystemExit: If file validation fails
    """
    input_file = Path(input_path)
    
    # Check if file exists
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    # Check if it's a file (not a directory)
    if not input_file.is_file():
        print(f"Error: '{input_path}' is not a valid file.", file=sys.stderr)
        sys.exit(1)
    
    # Check if file is readable
    if not os.access(input_path, os.R_OK):
        print(f"Error: No read permission for file '{input_path}'.", file=sys.stderr)
        sys.exit(1)
    
    return True


def validate_output_path(output_path):
    """
    Validate that the output path is writable.
    
    Args:
        output_path (str): Path to the output CSV file
        
    Returns:
        bool: True if path is valid, False otherwise
        
    Raises:
        SystemExit: If path validation fails
    """
    output_file = Path(output_path)
    
    # Create parent directories if they don't exist
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Error: No permission to create directory '{output_file.parent}'.", file=sys.stderr)
        sys.exit(1)
    
    # Check if we can write to the output location
    if output_file.exists() and not os.access(output_path, os.W_OK):
        print(f"Error: No write permission for file '{output_path}'.", file=sys.stderr)
        sys.exit(1)
    
    # Check if we can write to the parent directory
    if not output_file.exists() and not os.access(output_file.parent, os.W_OK):
        print(f"Error: No write permission for directory '{output_file.parent}'.", file=sys.stderr)
        sys.exit(1)
    
    return True


def read_csv_data(input_path):
    """
    Read CSV data from input file and extract the input column.
    
    Args:
        input_path (str): Path to the input CSV file
        
    Returns:
        list: List of input values from the CSV file
        
    Raises:
        SystemExit: If file reading or parsing fails
    """
    input_data = []
    
    try:
        # Open the CSV file with proper encoding handling
        with open(input_path, 'r', encoding='utf-8', newline='') as csvfile:
            # Use comma as delimiter (standard CSV format)
            delimiter = ','
            
            # Create CSV reader with comma delimiter
            csv_reader = csv.DictReader(csvfile, delimiter=delimiter)
            
            # Validate that 'input' column exists
            if 'input' not in csv_reader.fieldnames:
                print(f"Error: 'input' column not found in CSV file. Available columns: {csv_reader.fieldnames}", file=sys.stderr)
                sys.exit(1)
            
            # Extract input column data
            row_count = 0
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because header is row 1
                try:
                    input_value = row['input']
                    if input_value is not None:  # Handle None values
                        input_data.append(input_value)
                        row_count += 1
                    else:
                        print(f"Warning: Empty input value found at row {row_num}", file=sys.stderr)
                        input_data.append('')  # Add empty string for None values
                        row_count += 1
                except KeyError as e:
                    print(f"Error: Missing 'input' column in row {row_num}: {e}", file=sys.stderr)
                    sys.exit(1)
            
            print(f"Successfully read {row_count} input records from '{input_path}'")
            
    except FileNotFoundError:
        print(f"Error: File '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when reading '{input_path}'.", file=sys.stderr)
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Error: Unable to decode file '{input_path}'. Please check file encoding: {e}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"Error: Invalid CSV format in '{input_path}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while reading '{input_path}': {e}", file=sys.stderr)
        sys.exit(1)
    
    return input_data


def write_csv_data(output_path, input_data):
    """
    Write extracted input data to output CSV file.
    
    Args:
        output_path (str): Path to the output CSV file
        input_data (list): List of input values to write
        
    Raises:
        SystemExit: If file writing fails
    """
    try:
        # Write data to output CSV file
        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header
            csv_writer.writerow(['input'])
            
            # Write input data rows
            for input_value in input_data:
                csv_writer.writerow([input_value])
        
        print(f"Successfully wrote {len(input_data)} input records to '{output_path}'")
        
    except PermissionError:
        print(f"Error: Permission denied when writing to '{output_path}'.", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Unable to write to '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while writing to '{output_path}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function that orchestrates the input extraction process.
    
    This function:
    1. Parses command-line arguments
    2. Validates input and output paths
    3. Reads and processes the CSV data
    4. Writes the extracted input data to output file
    5. Handles errors and provides appropriate exit codes
    """
    # Set up argument parser and parse command-line arguments
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Validate input and output file paths
    validate_input_file(args.input)
    validate_output_path(args.output)
    
    # Read CSV data and extract input column
    print(f"Reading data from '{args.input}'...")
    input_data = read_csv_data(args.input)
    
    # Check if any data was extracted
    if not input_data:
        print("Warning: No input data found in the CSV file.", file=sys.stderr)
        sys.exit(1)
    
    # Write extracted data to output file
    print(f"Writing extracted input data to '{args.output}'...")
    write_csv_data(args.output, input_data)
    
    # Success - exit with code 0
    print("Input extraction completed successfully.")
    sys.exit(0)


if __name__ == '__main__':
    main()