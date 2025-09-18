"""CSV fixer service.

Fixes common issues in CSV files, particularly multiline JSON data
that spans across multiple rows.
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from ..io.csv_io import CSVReader, CSVWriter
from ..io.validators import DataValidator, JSONValidator


class FixerService:
    """Service for fixing CSV file issues."""
    
    def __init__(self):
        self.csv_reader = CSVReader()
        self.csv_writer = CSVWriter()
        self.validator = DataValidator()
        self.json_validator = JSONValidator()
    
    def fix_multiline_json(self, 
                          input_file: Union[str, Path], 
                          output_file: Optional[Union[str, Path]] = None,
                          json_column: str = 'scenegraph',
                          create_backup: bool = True) -> Dict[str, Any]:
        """Fix multiline JSON data in CSV file.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file (optional)
            json_column: Name of the column containing JSON data
            create_backup: Whether to create backup of original file
            
        Returns:
            Dictionary with fixing results
        """
        input_path = Path(input_file)
        
        # Generate output filename if not provided
        if output_file is None:
            output_path = input_path.parent / f"fixed_{input_path.name}"
        else:
            output_path = Path(output_file)
        
        # Create backup if requested
        if create_backup:
            backup_path = input_path.parent / f"{input_path.stem}_backup{input_path.suffix}"
            try:
                backup_path.write_bytes(input_path.read_bytes())
            except Exception as e:
                return {
                    'success': False,
                    'error': f"Failed to create backup: {str(e)}",
                    'input_file': str(input_path),
                    'output_file': str(output_path)
                }
        
        # Read and fix CSV data
        try:
            fixed_rows, fix_stats = self._fix_multiline_json_data(input_path, json_column)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to fix CSV data: {str(e)}",
                'input_file': str(input_path),
                'output_file': str(output_path)
            }
        
        # Write fixed data
        try:
            if fixed_rows:
                fieldnames = list(fixed_rows[0].keys())
                self.csv_writer.write_csv(output_path, fixed_rows, fieldnames)
            else:
                # Create empty file with same structure as input
                with open(input_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames or []
                self.csv_writer.write_csv(output_path, [], fieldnames)
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
            'backup_created': create_backup,
            'total_rows': fix_stats['total_rows'],
            'fixed_rows': fix_stats['fixed_rows'],
            'valid_json_rows': fix_stats['valid_json_rows'],
            'invalid_json_rows': fix_stats['invalid_json_rows'],
            'empty_json_rows': fix_stats['empty_json_rows']
        }
    
    def _fix_multiline_json_data(self, input_path: Path, 
                               json_column: str) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """Fix multiline JSON data in CSV.
        
        Args:
            input_path: Path to input CSV file
            json_column: Name of JSON column
            
        Returns:
            Tuple of (fixed_rows, statistics)
        """
        fixed_rows = []
        stats = {
            'total_rows': 0,
            'fixed_rows': 0,
            'valid_json_rows': 0,
            'invalid_json_rows': 0,
            'empty_json_rows': 0
        }
        
        with open(input_path, 'r', encoding='utf-8') as f:
            # Read all lines
            lines = f.readlines()
        
        if not lines:
            return fixed_rows, stats
        
        # Parse header
        header_line = lines[0].strip()
        fieldnames = list(csv.DictReader([header_line]).__next__().keys())
        
        if json_column not in fieldnames:
            # If JSON column doesn't exist, just return original data
            rows = self.csv_reader.read_csv(input_path)
            stats['total_rows'] = len(rows)
            return rows, stats
        
        # Process data lines
        i = 1
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Try to parse as complete CSV row
            try:
                row_data = list(csv.reader([line]))[0]
                if len(row_data) == len(fieldnames):
                    # Complete row
                    row = dict(zip(fieldnames, row_data))
                    json_data = row.get(json_column, '')
                    
                    if not json_data.strip():
                        stats['empty_json_rows'] += 1
                    elif self._is_valid_json(json_data):
                        stats['valid_json_rows'] += 1
                    else:
                        # Try to fix multiline JSON
                        fixed_json, lines_consumed = self._fix_json_from_lines(lines, i, json_column, fieldnames)
                        if fixed_json:
                            row[json_column] = fixed_json
                            stats['fixed_rows'] += 1
                            i += lines_consumed - 1  # Skip consumed lines
                        else:
                            stats['invalid_json_rows'] += 1
                    
                    fixed_rows.append(row)
                    stats['total_rows'] += 1
                else:
                    # Incomplete row, try to fix multiline JSON
                    fixed_json, lines_consumed = self._fix_json_from_lines(lines, i, json_column, fieldnames)
                    if fixed_json and lines_consumed > 1:
                        # Reconstruct the complete row
                        combined_line = ''.join(lines[i:i+lines_consumed]).replace('\n', ' ').strip()
                        row_data = list(csv.reader([combined_line]))[0]
                        
                        if len(row_data) >= len(fieldnames):
                            row = dict(zip(fieldnames, row_data[:len(fieldnames)]))
                            row[json_column] = fixed_json
                            fixed_rows.append(row)
                            stats['total_rows'] += 1
                            stats['fixed_rows'] += 1
                            i += lines_consumed - 1
                        else:
                            stats['invalid_json_rows'] += 1
                    else:
                        stats['invalid_json_rows'] += 1
            
            except (csv.Error, IndexError, ValueError):
                # Try to fix multiline JSON
                fixed_json, lines_consumed = self._fix_json_from_lines(lines, i, json_column, fieldnames)
                if fixed_json and lines_consumed > 1:
                    try:
                        # Reconstruct the complete row
                        combined_line = ''.join(lines[i:i+lines_consumed]).replace('\n', ' ').strip()
                        row_data = list(csv.reader([combined_line]))[0]
                        
                        if len(row_data) >= len(fieldnames):
                            row = dict(zip(fieldnames, row_data[:len(fieldnames)]))
                            row[json_column] = fixed_json
                            fixed_rows.append(row)
                            stats['total_rows'] += 1
                            stats['fixed_rows'] += 1
                            i += lines_consumed - 1
                        else:
                            stats['invalid_json_rows'] += 1
                    except (csv.Error, IndexError):
                        stats['invalid_json_rows'] += 1
                else:
                    stats['invalid_json_rows'] += 1
            
            i += 1
        
        return fixed_rows, stats
    
    def _fix_json_from_lines(self, lines: List[str], start_idx: int, 
                           json_column: str, fieldnames: List[str]) -> Tuple[Optional[str], int]:
        """Try to fix JSON data that spans multiple lines.
        
        Args:
            lines: All lines from the file
            start_idx: Starting line index
            json_column: Name of JSON column
            fieldnames: CSV field names
            
        Returns:
            Tuple of (fixed_json_string, lines_consumed)
        """
        json_column_idx = fieldnames.index(json_column) if json_column in fieldnames else -1
        if json_column_idx == -1:
            return None, 1
        
        # Try to accumulate lines until we have valid JSON
        accumulated_text = ''
        lines_consumed = 0
        
        for i in range(start_idx, min(start_idx + 10, len(lines))):  # Limit to 10 lines
            accumulated_text += lines[i].strip() + ' '
            lines_consumed += 1
            
            # Try to parse as CSV and extract JSON
            try:
                row_data = list(csv.reader([accumulated_text.strip()]))[0]
                if len(row_data) > json_column_idx:
                    potential_json = row_data[json_column_idx]
                    if self._is_valid_json(potential_json):
                        return potential_json, lines_consumed
            except (csv.Error, IndexError):
                continue
            
            # Also try to find JSON patterns in the accumulated text
            json_match = self._extract_json_pattern(accumulated_text)
            if json_match and self._is_valid_json(json_match):
                return json_match, lines_consumed
        
        return None, lines_consumed
    
    def _extract_json_pattern(self, text: str) -> Optional[str]:
        """Extract JSON pattern from text.
        
        Args:
            text: Text to search for JSON
            
        Returns:
            Extracted JSON string or None
        """
        # Look for JSON array or object patterns
        patterns = [
            r'\[.*?\]',  # JSON array
            r'\{.*?\}',  # JSON object
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                if self._is_valid_json(match):
                    return match
        
        return None
    
    def _is_valid_json(self, json_str: str) -> bool:
        """Check if string is valid JSON.
        
        Args:
            json_str: String to validate
            
        Returns:
            True if valid JSON
        """
        if not json_str or not json_str.strip():
            return False
        
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def validate_csv_structure(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate CSV file structure and report issues.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Validation report
        """
        try:
            rows = self.csv_reader.read_csv(file_path)
            return self.validator.validate_annotation_file(file_path, rows)
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
    
    def fix_batch(self, 
                 input_files: List[Union[str, Path]], 
                 output_dir: Optional[Union[str, Path]] = None,
                 **kwargs) -> List[Dict[str, Any]]:
        """Fix multiple CSV files.
        
        Args:
            input_files: List of input CSV file paths
            output_dir: Output directory (optional)
            **kwargs: Additional arguments for fix_multiline_json
            
        Returns:
            List of fixing results for each file
        """
        results = []
        
        for input_file in input_files:
            input_path = Path(input_file)
            
            # Determine output file path
            if output_dir:
                output_path = Path(output_dir) / f"fixed_{input_path.name}"
            else:
                output_path = None
            
            # Process file
            result = self.fix_multiline_json(input_path, output_path, **kwargs)
            results.append(result)
        
        return results
    
    def get_fix_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics from batch fixing results.
        
        Args:
            results: List of fixing results
            
        Returns:
            Statistics summary
        """
        total_files = len(results)
        successful_files = len([r for r in results if r['success']])
        failed_files = total_files - successful_files
        
        total_rows = sum(r.get('total_rows', 0) for r in results if r['success'])
        fixed_rows = sum(r.get('fixed_rows', 0) for r in results if r['success'])
        valid_json_rows = sum(r.get('valid_json_rows', 0) for r in results if r['success'])
        invalid_json_rows = sum(r.get('invalid_json_rows', 0) for r in results if r['success'])
        
        return {
            'total_files': total_files,
            'successful_files': successful_files,
            'failed_files': failed_files,
            'success_rate': successful_files / total_files if total_files > 0 else 0,
            'total_rows': total_rows,
            'fixed_rows': fixed_rows,
            'valid_json_rows': valid_json_rows,
            'invalid_json_rows': invalid_json_rows,
            'fix_rate': fixed_rows / total_rows if total_rows > 0 else 0,
            'json_validity_rate': valid_json_rows / total_rows if total_rows > 0 else 0
        }


def fix_multiline_json_csv(input_file: Union[str, Path], 
                          output_file: Optional[Union[str, Path]] = None,
                          **kwargs) -> Dict[str, Any]:
    """Convenience function to fix multiline JSON in a single CSV file.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional)
        **kwargs: Additional arguments
        
    Returns:
        Fixing result
    """
    fixer = FixerService()
    return fixer.fix_multiline_json(input_file, output_file, **kwargs)


def fix_csv_batch(input_files: List[Union[str, Path]], 
                 output_dir: Optional[Union[str, Path]] = None,
                 **kwargs) -> List[Dict[str, Any]]:
    """Convenience function to fix multiple CSV files.
    
    Args:
        input_files: List of input CSV file paths
        output_dir: Output directory (optional)
        **kwargs: Additional arguments
        
    Returns:
        List of fixing results
    """
    fixer = FixerService()
    return fixer.fix_batch(input_files, output_dir, **kwargs)