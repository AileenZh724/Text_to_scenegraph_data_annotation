"""Input extraction service.

Extracts specific columns from CSV files, primarily the 'input' column
for processing by scene graph generators.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..io.csv_io import CSVReader, CSVWriter
from ..io.validators import DataValidator


class ExtractorService:
    """Service for extracting columns from CSV files."""
    
    def __init__(self):
        self.csv_reader = CSVReader()
        self.csv_writer = CSVWriter()
        self.validator = DataValidator()
    
    def extract_input_column(self, 
                           input_file: Union[str, Path], 
                           output_file: Union[str, Path],
                           input_column: str = 'input') -> Dict[str, Any]:
        """Extract input column from CSV file.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            input_column: Name of the input column to extract
            
        Returns:
            Dictionary with extraction results
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        # Read input CSV
        try:
            rows = self.csv_reader.read_csv(input_path)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to read input file: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Validate input format
        validation_report = self.validator.validate_input_file(input_path, rows)
        if not validation_report['overall_valid']:
            return {
                'success': False,
                'error': 'Input file validation failed',
                'validation_report': validation_report,
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Check if input column exists
        if not rows or input_column not in rows[0]:
            available_columns = list(rows[0].keys()) if rows else []
            return {
                'success': False,
                'error': f"Column '{input_column}' not found. Available columns: {available_columns}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Extract input data
        try:
            input_data = self._extract_column_data(rows, input_column)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to extract data: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Write output CSV
        try:
            self._write_extracted_data(output_path, input_data, input_column)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to write output file: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        return {
            'success': True,
            'input_file': str(input_path),
            'output_file': str(output_path),
            'total_rows': len(input_data),
            'non_empty_rows': len([d for d in input_data if d.strip()]),
            'empty_rows': len([d for d in input_data if not d.strip()]),
            'extracted_column': input_column,
            'validation_report': validation_report
        }
    
    def extract_multiple_columns(self, 
                               input_file: Union[str, Path], 
                               output_file: Union[str, Path],
                               columns: List[str]) -> Dict[str, Any]:
        """Extract multiple columns from CSV file.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            columns: List of column names to extract
            
        Returns:
            Dictionary with extraction results
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        # Read input CSV
        try:
            rows = self.csv_reader.read_csv(input_path)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to read input file: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Check if all columns exist
        if not rows:
            return {
                'success': False,
                'error': "Input file is empty",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        available_columns = list(rows[0].keys())
        missing_columns = [col for col in columns if col not in available_columns]
        
        if missing_columns:
            return {
                'success': False,
                'error': f"Columns not found: {missing_columns}. Available columns: {available_columns}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Extract selected columns
        try:
            extracted_rows = self._extract_multiple_columns_data(rows, columns)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to extract data: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Write output CSV
        try:
            self.csv_writer.write_csv(output_path, extracted_rows, columns)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to write output file: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        return {
            'success': True,
            'input_file': str(input_path),
            'output_file': str(output_path),
            'total_rows': len(extracted_rows),
            'extracted_columns': columns,
            'available_columns': available_columns
        }
    
    def _extract_column_data(self, rows: List[Dict[str, Any]], column: str) -> List[str]:
        """Extract data from a specific column.
        
        Args:
            rows: CSV rows data
            column: Column name to extract
            
        Returns:
            List of column values
        """
        column_data = []
        
        for row in rows:
            value = row.get(column, '')
            # Convert to string and handle None values
            if value is None:
                column_data.append('')
            else:
                column_data.append(str(value))
        
        return column_data
    
    def _extract_multiple_columns_data(self, rows: List[Dict[str, Any]], 
                                     columns: List[str]) -> List[Dict[str, Any]]:
        """Extract data from multiple columns.
        
        Args:
            rows: CSV rows data
            columns: List of column names to extract
            
        Returns:
            List of dictionaries with extracted data
        """
        extracted_rows = []
        
        for row in rows:
            extracted_row = {}
            for column in columns:
                value = row.get(column, '')
                # Convert to string and handle None values
                if value is None:
                    extracted_row[column] = ''
                else:
                    extracted_row[column] = str(value)
            extracted_rows.append(extracted_row)
        
        return extracted_rows
    
    def _write_extracted_data(self, output_path: Path, data: List[str], column_name: str):
        """Write extracted single column data to CSV file.
        
        Args:
            output_path: Path to output file
            data: List of column values
            column_name: Name of the column
        """
        # Convert to list of dictionaries for CSV writer
        rows = [{column_name: value} for value in data]
        self.csv_writer.write_csv(output_path, rows, [column_name])
    
    def extract_batch(self, 
                     input_files: List[Union[str, Path]], 
                     output_dir: Union[str, Path],
                     columns: Union[str, List[str]] = 'input') -> List[Dict[str, Any]]:
        """Extract columns from multiple CSV files.
        
        Args:
            input_files: List of input CSV file paths
            output_dir: Output directory
            columns: Column name(s) to extract
            
        Returns:
            List of extraction results for each file
        """
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for input_file in input_files:
            input_path = Path(input_file)
            output_file = output_path / f"extracted_{input_path.name}"
            
            # Process file
            if isinstance(columns, str):
                result = self.extract_input_column(input_path, output_file, columns)
            else:
                result = self.extract_multiple_columns(input_path, output_file, columns)
            
            results.append(result)
        
        return results
    
    def get_extraction_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics from batch extraction results.
        
        Args:
            results: List of extraction results
            
        Returns:
            Statistics summary
        """
        total_files = len(results)
        successful_files = len([r for r in results if r['success']])
        failed_files = total_files - successful_files
        
        total_rows = sum(r.get('total_rows', 0) for r in results if r['success'])
        non_empty_rows = sum(r.get('non_empty_rows', 0) for r in results if r['success'])
        empty_rows = sum(r.get('empty_rows', 0) for r in results if r['success'])
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': successful_files / total_files if total_files > 0 else 0,
            'total_rows': total_rows,
            'non_empty_rows': non_empty_rows,
            'empty_rows': empty_rows,
            'data_completeness': non_empty_rows / total_rows if total_rows > 0 else 0
        }


def extract_input_column(input_file: Union[str, Path], 
                        output_file: Union[str, Path],
                        input_column: str = 'input') -> Dict[str, Any]:
    """Convenience function to extract input column from a single CSV file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        input_column: Name of the input column
        
    Returns:
        Extraction result
    """
    extractor = ExtractorService()
    return extractor.extract_input_column(input_file, output_file, input_column)


def extract_columns(input_file: Union[str, Path], 
                   output_file: Union[str, Path],
                   columns: List[str]) -> Dict[str, Any]:
    """Convenience function to extract multiple columns from a single CSV file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        columns: List of column names to extract
        
    Returns:
        Extraction result
    """
    extractor = ExtractorService()
    return extractor.extract_multiple_columns(input_file, output_file, columns)