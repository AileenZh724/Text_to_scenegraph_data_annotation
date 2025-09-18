"""Data annotation formatter service.

Converts input CSV files to annotation format with required fields:
id, input, scenegraph, is_reasonable, is_annotated
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from ..models import AnnotatedRow
from ..io.csv_io import CSVReader, CSVWriter
from ..io.validators import DataValidator


class FormatterService:
    """Service for formatting CSV data to annotation format."""
    
    def __init__(self):
        self.csv_reader = CSVReader()
        self.csv_writer = CSVWriter()
        self.validator = DataValidator()
    
    def format_to_annotation(self, 
                           input_file: Union[str, Path], 
                           output_file: Optional[Union[str, Path]] = None,
                           id_prefix: str = "item",
                           default_reasonable: bool = True,
                           default_annotated: bool = False) -> Dict[str, Any]:
        """Format input CSV to annotation format.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            id_prefix: Prefix for generated IDs
            default_reasonable: Default value for is_reasonable field
            default_annotated: Default value for is_annotated field
            
        Returns:
            Dictionary with processing results
        """
        input_path = Path(input_file)
        
        # Generate output filename if not provided
        if output_file is None:
            output_path = input_path.parent / f"formatted_{input_path.stem}.csv"
        else:
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
        
        # Convert to annotation format
        try:
            annotation_rows = self._convert_to_annotation_format(
                rows, id_prefix, default_reasonable, default_annotated
            )
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to convert data: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Write output CSV
        try:
            self.csv_writer.write_annotation_csv(output_path, annotation_rows)
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
            'total_rows': len(annotation_rows),
            'processed_rows': len([r for r in annotation_rows if r.input.strip()]),
            'skipped_rows': len([r for r in annotation_rows if not r.input.strip()]),
            'validation_report': validation_report
        }
    
    def _convert_to_annotation_format(self, 
                                    rows: List[Dict[str, Any]], 
                                    id_prefix: str,
                                    default_reasonable: bool,
                                    default_annotated: bool) -> List[AnnotatedRow]:
        """Convert input rows to annotation format.
        
        Args:
            rows: Input CSV rows
            id_prefix: Prefix for generated IDs
            default_reasonable: Default value for is_reasonable
            default_annotated: Default value for is_annotated
            
        Returns:
            List of AnnotatedRow objects
        """
        annotation_rows = []
        
        for idx, row in enumerate(rows, 1):
            input_text = str(row.get('input', '')).strip()
            
            # Skip completely empty rows
            if not input_text:
                continue
            
            # Create annotation row
            annotation_row = AnnotatedRow(
                id=f"{id_prefix}_{idx:04d}",
                input=input_text,
                scenegraph=[],  # Empty scene graph list
                is_reasonable=default_reasonable,
                is_annotated=default_annotated
            )
            
            annotation_rows.append(annotation_row)
        
        return annotation_rows
    
    def format_batch(self, 
                    input_files: List[Union[str, Path]], 
                    output_dir: Optional[Union[str, Path]] = None,
                    **kwargs) -> List[Dict[str, Any]]:
        """Format multiple CSV files to annotation format.
        
        Args:
            input_files: List of input CSV file paths
            output_dir: Output directory (optional)
            **kwargs: Additional arguments for format_to_annotation
            
        Returns:
            List of processing results for each file
        """
        results = []
        
        for input_file in input_files:
            input_path = Path(input_file)
            
            # Determine output file path
            if output_dir:
                output_path = Path(output_dir) / f"formatted_{input_path.name}"
            else:
                output_path = None
            
            # Process file
            result = self.format_to_annotation(input_path, output_path, **kwargs)
            results.append(result)
        
        return results
    
    def validate_annotation_output(self, output_file: Union[str, Path]) -> Dict[str, Any]:
        """Validate the generated annotation CSV file.
        
        Args:
            output_file: Path to annotation CSV file
            
        Returns:
            Validation report
        """
        try:
            rows = self.csv_reader.read_csv(output_file)
            return self.validator.validate_annotation_file(output_file, rows)
        except Exception as e:
            return {
                'file_valid': False,
                'structure_valid': False,
                'overall_valid': False,
                'error': str(e),
                'total_rows': 0,
                'errors': [f"Failed to read file: {str(e)}"],
                'warnings': []
            }
    
    def get_format_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics from batch formatting results.
        
        Args:
            results: List of formatting results
            
        Returns:
            Statistics summary
        """
        total_files = len(results)
        successful_files = len([r for r in results if r['success']])
        failed_files = total_files - successful_files
        
        total_rows = sum(r.get('total_rows', 0) for r in results if r['success'])
        processed_rows = sum(r.get('processed_rows', 0) for r in results if r['success'])
        skipped_rows = sum(r.get('skipped_rows', 0) for r in results if r['success'])
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': successful_files / total_files if total_files > 0 else 0,
            'total_rows': total_rows,
            'processed_rows': processed_rows,
            'skipped_rows': skipped_rows,
            'processing_rate': processed_rows / total_rows if total_rows > 0 else 0
        }


def format_csv_to_annotation(input_file: Union[str, Path], 
                           output_file: Optional[Union[str, Path]] = None,
                           **kwargs) -> Dict[str, Any]:
    """Convenience function to format a single CSV file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional)
        **kwargs: Additional arguments
        
    Returns:
        Processing result
    """
    formatter = FormatterService()
    return formatter.format_to_annotation(input_file, output_file, **kwargs)


def format_csv_batch(input_files: List[Union[str, Path]], 
                    output_dir: Optional[Union[str, Path]] = None,
                    **kwargs) -> List[Dict[str, Any]]:
    """Convenience function to format multiple CSV files.
    
    Args:
        input_files: List of input CSV file paths
        output_dir: Output directory (optional)
        **kwargs: Additional arguments
        
    Returns:
        List of processing results
    """
    formatter = FormatterService()
    return formatter.format_batch(input_files, output_dir, **kwargs)