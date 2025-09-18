"""CSV input/output utilities for text2sg."""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Iterator

from ..models import AnnotatedRow, SceneGraph


class CSVReader:
    """CSV reader with support for multiline JSON fixing and column selection."""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
    
    def read_csv(self, file_path: Union[str, Path], 
                 columns: Optional[List[str]] = None,
                 fix_multiline_json: bool = True) -> List[Dict[str, Any]]:
        """Read CSV file with optional column selection and JSON fixing.
        
        Args:
            file_path: Path to CSV file
            columns: List of columns to read (None for all)
            fix_multiline_json: Whether to fix multiline JSON issues
            
        Returns:
            List of row dictionaries
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Fix multiline JSON if needed
        if fix_multiline_json:
            file_path = self._fix_multiline_json(file_path)
        
        # Read CSV data
        rows = []
        with open(file_path, 'r', encoding=self.encoding) as f:
            reader = csv.DictReader(f)
            
            # Validate columns if specified
            if columns:
                missing_cols = set(columns) - set(reader.fieldnames or [])
                if missing_cols:
                    raise ValueError(f"Missing columns in CSV: {missing_cols}")
            
            for row in reader:
                if columns:
                    # Filter to requested columns only
                    filtered_row = {col: row.get(col, '') for col in columns}
                    rows.append(filtered_row)
                else:
                    rows.append(dict(row))
        
        return rows
    
    def read_annotated_rows(self, file_path: Union[str, Path]) -> List[AnnotatedRow]:
        """Read CSV file and convert to AnnotatedRow objects.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of AnnotatedRow objects
        """
        rows = self.read_csv(file_path)
        annotated_rows = []
        
        for row in rows:
            # Parse scenegraph JSON if present
            scenegraph_data = None
            if 'scenegraph' in row and row['scenegraph']:
                try:
                    scenegraph_json = json.loads(row['scenegraph'])
                    if isinstance(scenegraph_json, list) and scenegraph_json:
                        # Convert first scene graph (for now)
                        scene_data = scenegraph_json[0]
                        scenegraph_data = SceneGraph.from_dict(scene_data)
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    # Keep as None if parsing fails
                    pass
            
            annotated_row = AnnotatedRow(
                id=row.get('id', ''),
                input=row.get('input', ''),
                scenegraph=scenegraph_data,
                is_reasonable=self._parse_bool(row.get('is_reasonable')),
                is_annotated=self._parse_bool(row.get('is_annotated'))
            )
            annotated_rows.append(annotated_row)
        
        return annotated_rows
    
    def _fix_multiline_json(self, file_path: Path) -> Path:
        """Fix multiline JSON issues in CSV file.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Path to fixed file (may be same as input)
        """
        # Read file content
        with open(file_path, 'r', encoding=self.encoding) as f:
            content = f.read()
        
        # Check if file needs fixing
        if not self._needs_json_fixing(content):
            return file_path
        
        # Create temporary fixed file
        fixed_path = file_path.with_suffix('.fixed.csv')
        
        # Process lines to fix multiline JSON
        lines = content.split('\n')
        fixed_lines = []
        current_row = ""
        in_json = False
        json_bracket_count = 0
        
        for i, line in enumerate(lines):
            if i == 0:  # Header line
                fixed_lines.append(line)
                continue
            
            if not in_json:
                # Check if this line starts JSON data
                if '"[' in line or '","[' in line:
                    in_json = True
                    current_row = line
                    json_bracket_count = line.count('[') - line.count(']')
                else:
                    fixed_lines.append(line)
            else:
                # Continue accumulating JSON lines
                current_row += " " + line.strip()
                json_bracket_count += line.count('[') - line.count(']')
                
                # Check if JSON ends
                if (json_bracket_count <= 0 and 
                    (line.strip().endswith('"]"') or 
                     line.strip().endswith(']",true,false') or
                     line.strip().endswith(']",false,false') or
                     line.strip().endswith(']",true,true') or
                     line.strip().endswith(']",false,true'))):
                    
                    fixed_lines.append(current_row)
                    current_row = ""
                    in_json = False
                    json_bracket_count = 0
        
        # Add any remaining row
        if current_row:
            fixed_lines.append(current_row)
        
        # Write fixed content
        with open(fixed_path, 'w', encoding=self.encoding, newline='') as f:
            f.write('\n'.join(fixed_lines))
        
        return fixed_path
    
    def _needs_json_fixing(self, content: str) -> bool:
        """Check if CSV content needs JSON fixing.
        
        Args:
            content: CSV file content
            
        Returns:
            True if fixing is needed
        """
        # Simple heuristic: if we have JSON-like content spanning multiple lines
        lines = content.split('\n')
        for i, line in enumerate(lines[1:], 1):  # Skip header
            if '"[' in line and not line.strip().endswith('"]"'):
                # Found potential multiline JSON
                return True
        return False
    
    def _parse_bool(self, value: Any) -> Optional[bool]:
        """Parse boolean value from CSV.
        
        Args:
            value: Value to parse
            
        Returns:
            Boolean value or None
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.lower().strip()
            if value in ('true', '1', 'yes', 'y'):
                return True
            elif value in ('false', '0', 'no', 'n'):
                return False
        
        return None


class CSVWriter:
    """CSV writer with proper JSON serialization and encoding."""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
    
    def write_csv(self, file_path: Union[str, Path], 
                  rows: List[Dict[str, Any]], 
                  fieldnames: Optional[List[str]] = None,
                  create_backup: bool = False) -> None:
        """Write rows to CSV file.
        
        Args:
            file_path: Output file path
            rows: List of row dictionaries
            fieldnames: Column names (inferred if None)
            create_backup: Whether to create backup of existing file
        """
        file_path = Path(file_path)
        
        # Create backup if requested and file exists
        if create_backup and file_path.exists():
            backup_path = file_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
            file_path.rename(backup_path)
        
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine fieldnames
        if not fieldnames and rows:
            fieldnames = list(rows[0].keys())
        
        if not fieldnames:
            raise ValueError("No fieldnames provided and no rows to infer from")
        
        # Write CSV
        with open(file_path, 'w', encoding=self.encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in rows:
                # Serialize JSON fields properly
                processed_row = {}
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        processed_row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        processed_row[key] = value
                
                writer.writerow(processed_row)
    
    def write_annotated_rows(self, file_path: Union[str, Path], 
                           rows: List[AnnotatedRow],
                           create_backup: bool = False) -> None:
        """Write AnnotatedRow objects to CSV file.
        
        Args:
            file_path: Output file path
            rows: List of AnnotatedRow objects
            create_backup: Whether to create backup of existing file
        """
        # Convert to dictionaries
        dict_rows = []
        for row in rows:
            dict_row = {
                'id': row.id,
                'input': row.input,
                'scenegraph': row.scenegraph.to_dict() if row.scenegraph else '',
                'is_reasonable': row.is_reasonable if row.is_reasonable is not None else '',
                'is_annotated': row.is_annotated if row.is_annotated is not None else ''
            }
            dict_rows.append(dict_row)
        
        fieldnames = ['id', 'input', 'scenegraph', 'is_reasonable', 'is_annotated']
        self.write_csv(file_path, dict_rows, fieldnames, create_backup)
    
    def append_rows(self, file_path: Union[str, Path], 
                   rows: List[Dict[str, Any]]) -> None:
        """Append rows to existing CSV file.
        
        Args:
            file_path: CSV file path
            rows: Rows to append
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Read existing fieldnames
        with open(file_path, 'r', encoding=self.encoding) as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        
        # Append rows
        with open(file_path, 'a', encoding=self.encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            for row in rows:
                # Serialize JSON fields properly
                processed_row = {}
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        processed_row[key] = json.dumps(value, ensure_ascii=False)
                    else:
                        processed_row[key] = value
                
                writer.writerow(processed_row)


class CSVProcessor:
    """High-level CSV processing utilities."""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.reader = CSVReader(encoding)
        self.writer = CSVWriter(encoding)
    
    def extract_column(self, input_file: Union[str, Path], 
                      output_file: Union[str, Path],
                      column: str) -> None:
        """Extract single column from CSV file.
        
        Args:
            input_file: Input CSV file path
            output_file: Output CSV file path
            column: Column name to extract
        """
        rows = self.reader.read_csv(input_file, columns=[column])
        self.writer.write_csv(output_file, rows, fieldnames=[column])
    
    def format_for_annotation(self, input_file: Union[str, Path],
                            output_file: Union[str, Path]) -> None:
        """Format CSV for annotation with required columns.
        
        Args:
            input_file: Input CSV file path
            output_file: Output CSV file path
        """
        rows = self.reader.read_csv(input_file)
        
        # Create annotation format
        formatted_rows = []
        for i, row in enumerate(rows, 1):
            formatted_row = {
                'id': row.get('id', str(i)),
                'input': row.get('input', ''),
                'scenegraph': '',
                'is_reasonable': '',
                'is_annotated': ''
            }
            formatted_rows.append(formatted_row)
        
        fieldnames = ['id', 'input', 'scenegraph', 'is_reasonable', 'is_annotated']
        self.writer.write_csv(output_file, formatted_rows, fieldnames)
    
    def validate_structure(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Validate CSV file structure and content.
        
        Args:
            file_path: CSV file path
            
        Returns:
            Validation results dictionary
        """
        try:
            rows = self.reader.read_csv(file_path)
            
            # Basic statistics
            result = {
                'valid': True,
                'total_rows': len(rows),
                'columns': list(rows[0].keys()) if rows else [],
                'json_validation': {'valid': 0, 'invalid': 0, 'errors': []}
            }
            
            # Validate JSON in scenegraph column
            if 'scenegraph' in result['columns']:
                for i, row in enumerate(rows[:100]):  # Check first 100 rows
                    scenegraph = row.get('scenegraph', '')
                    if scenegraph:
                        try:
                            json.loads(scenegraph)
                            result['json_validation']['valid'] += 1
                        except json.JSONDecodeError as e:
                            result['json_validation']['invalid'] += 1
                            result['json_validation']['errors'].append({
                                'row': i + 1,
                                'error': str(e)
                            })
            
            # Mark as invalid if too many JSON errors
            if result['json_validation']['invalid'] > result['json_validation']['valid']:
                result['valid'] = False
            
            return result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'total_rows': 0,
                'columns': [],
                'json_validation': {'valid': 0, 'invalid': 0, 'errors': []}
            }
    
    def get_resume_point(self, file_path: Union[str, Path], 
                        id_column: str = 'id') -> Optional[str]:
        """Get the last processed ID for resume functionality.
        
        Args:
            file_path: CSV file path
            id_column: ID column name
            
        Returns:
            Last processed ID or None
        """
        try:
            if not Path(file_path).exists():
                return None
            
            rows = self.reader.read_csv(file_path)
            if not rows:
                return None
            
            # Find last row with non-empty scenegraph
            for row in reversed(rows):
                if row.get('scenegraph') and row.get('scenegraph').strip():
                    return row.get(id_column)
            
            return None
            
        except Exception:
            return None