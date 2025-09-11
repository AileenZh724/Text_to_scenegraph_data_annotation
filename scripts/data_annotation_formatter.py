#!/usr/bin/env python3
"""
Data Annotation Formatter Script

This script processes the test_output.csv file and converts it to a CSV format
with 5 fields: id, input, scenegraph, is_reasonable, is_annotated.

Usage:
    python data_annotation_formatter.py <input_file> <output_file>

Example:
    python data_annotation_formatter.py test_output.csv formatted_output.csv
"""

import csv
import json
import sys
import os
import argparse
from typing import List, Dict, Any


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Set up command line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Convert test_output.csv to formatted CSV with 5 fields',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python data_annotation_formatter.py test_output.csv formatted_output.csv
  python data_annotation_formatter.py input.csv output.csv
'''
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the input CSV file (test_output.csv)'
    )
    
    parser.add_argument(
        'output_file',
        nargs='?',
        help='Path to the output CSV file (optional, defaults to formatted_<input_filename>)'
    )
    
    return parser


def validate_input_file(file_path: str) -> None:
    """
    Validate that the input file exists and is readable.
    
    Args:
        file_path (str): Path to the input file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file is not readable
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read input file: {file_path}")





def process_csv_data(input_file: str, output_file: str) -> None:
    """
    Process the input CSV file and convert it to the required format.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
    """
    try:
        # Read input CSV
        with open(input_file, 'r', encoding='utf-8', newline='') as infile:
            reader = csv.DictReader(infile)
            
            # Check if 'input' column exists
            if 'input' not in reader.fieldnames:
                raise ValueError("Input CSV must contain 'input' column")
            
            # Prepare output data
            output_data = []
            
            for idx, row in enumerate(reader, 1):
                input_text = row['input'].strip()
                
                # Skip empty rows
                if not input_text:
                    continue
                
                # Create output row
                output_row = {
                    'id': f"item_{idx:04d}",  # Generate unique ID
                    'input': input_text,
                    'scenegraph': '',  # Empty scenegraph field
                    'is_reasonable': 'true',  # Default to true
                    'is_annotated': 'false'   # Default to false
                }
                
                output_data.append(output_row)
        
        # Write output CSV
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            fieldnames = ['id', 'input', 'scenegraph', 'is_reasonable', 'is_annotated']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            writer.writerows(output_data)
        
        print(f"Successfully processed {len(output_data)} rows")
        print(f"Output saved to: {output_file}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except csv.Error as e:
        print(f"CSV Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """
    Main function to handle command line arguments and process the CSV file.
    """
    try:
        # Parse command line arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Validate input file
        validate_input_file(args.input_file)
        
        # Generate output filename if not provided
        if args.output_file is None:
            input_dir = os.path.dirname(args.input_file)
            input_name = os.path.splitext(os.path.basename(args.input_file))[0]
            args.output_file = os.path.join(input_dir, f"formatted_{input_name}.csv")
        
        # Process the CSV data
        process_csv_data(args.input_file, args.output_file)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()