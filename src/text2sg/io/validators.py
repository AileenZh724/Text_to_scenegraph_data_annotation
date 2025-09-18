"""Validation utilities for CSV and JSON data."""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

from ..models import SceneGraph, Node, Edge


class CSVValidator:
    """Validator for CSV file structure and content."""
    
    REQUIRED_ANNOTATION_COLUMNS = ['id', 'input', 'scenegraph', 'is_reasonable', 'is_annotated']
    REQUIRED_INPUT_COLUMNS = ['input']
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_file_exists(self, file_path: Union[str, Path]) -> bool:
        """Validate that file exists and is readable.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file exists and is readable
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.errors.append(f"File does not exist: {file_path}")
                return False
            
            if not path.is_file():
                self.errors.append(f"Path is not a file: {file_path}")
                return False
            
            # Try to read first few bytes
            with open(path, 'r', encoding='utf-8') as f:
                f.read(100)
            
            return True
            
        except PermissionError:
            self.errors.append(f"Permission denied reading file: {file_path}")
            return False
        except UnicodeDecodeError:
            self.errors.append(f"File encoding error (not UTF-8): {file_path}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading file {file_path}: {str(e)}")
            return False
    
    def validate_csv_structure(self, rows: List[Dict[str, Any]], 
                             required_columns: Optional[List[str]] = None) -> bool:
        """Validate CSV structure and required columns.
        
        Args:
            rows: List of CSV rows as dictionaries
            required_columns: List of required column names
            
        Returns:
            True if structure is valid
        """
        if not rows:
            self.errors.append("CSV file is empty")
            return False
        
        # Get actual columns
        actual_columns = set(rows[0].keys())
        
        # Check required columns
        if required_columns:
            missing_columns = set(required_columns) - actual_columns
            if missing_columns:
                self.errors.append(f"Missing required columns: {', '.join(missing_columns)}")
                return False
        
        # Check for empty column names
        empty_columns = [col for col in actual_columns if not col or not col.strip()]
        if empty_columns:
            self.warnings.append(f"Found empty column names: {empty_columns}")
        
        return True
    
    def validate_annotation_format(self, rows: List[Dict[str, Any]]) -> bool:
        """Validate annotation CSV format.
        
        Args:
            rows: List of CSV rows
            
        Returns:
            True if format is valid
        """
        if not self.validate_csv_structure(rows, self.REQUIRED_ANNOTATION_COLUMNS):
            return False
        
        # Validate data types and content
        for i, row in enumerate(rows, 1):
            # Check ID
            if not row.get('id') or not str(row['id']).strip():
                self.errors.append(f"Row {i}: Missing or empty ID")
            
            # Check input
            if not row.get('input') or not str(row['input']).strip():
                self.warnings.append(f"Row {i}: Missing or empty input text")
            
            # Validate boolean fields
            for bool_field in ['is_reasonable', 'is_annotated']:
                value = row.get(bool_field)
                if value and not self._is_valid_boolean(value):
                    self.warnings.append(f"Row {i}: Invalid boolean value for {bool_field}: {value}")
        
        return len(self.errors) == 0
    
    def validate_input_format(self, rows: List[Dict[str, Any]]) -> bool:
        """Validate input CSV format.
        
        Args:
            rows: List of CSV rows
            
        Returns:
            True if format is valid
        """
        if not self.validate_csv_structure(rows, self.REQUIRED_INPUT_COLUMNS):
            return False
        
        # Check for empty inputs
        empty_inputs = 0
        for i, row in enumerate(rows, 1):
            if not row.get('input') or not str(row['input']).strip():
                empty_inputs += 1
                if empty_inputs <= 5:  # Only report first 5
                    self.warnings.append(f"Row {i}: Empty input text")
        
        if empty_inputs > 5:
            self.warnings.append(f"... and {empty_inputs - 5} more rows with empty input")
        
        return True
    
    def _is_valid_boolean(self, value: Any) -> bool:
        """Check if value is a valid boolean representation.
        
        Args:
            value: Value to check
            
        Returns:
            True if valid boolean
        """
        if isinstance(value, bool):
            return True
        
        if isinstance(value, str):
            value = value.lower().strip()
            return value in ('true', 'false', '1', '0', 'yes', 'no', 'y', 'n', '')
        
        return False
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report with errors and warnings.
        
        Returns:
            Validation report dictionary
        """
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def clear(self):
        """Clear errors and warnings."""
        self.errors.clear()
        self.warnings.clear()


class JSONValidator:
    """Validator for JSON scene graph data."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_json_string(self, json_str: str) -> Tuple[bool, Optional[Any]]:
        """Validate JSON string and return parsed data.
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            Tuple of (is_valid, parsed_data)
        """
        if not json_str or not json_str.strip():
            return True, None  # Empty is valid
        
        try:
            parsed = json.loads(json_str)
            return True, parsed
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON decode error: {str(e)}")
            return False, None
    
    def validate_scene_graph_json(self, json_data: Any) -> bool:
        """Validate scene graph JSON structure.
        
        Args:
            json_data: Parsed JSON data
            
        Returns:
            True if structure is valid
        """
        if json_data is None:
            return True  # Empty is valid
        
        # Handle both single scene graph and array of scene graphs
        if isinstance(json_data, list):
            if not json_data:
                return True  # Empty array is valid
            
            # Validate each scene graph in array
            for i, scene in enumerate(json_data):
                if not self._validate_single_scene_graph(scene, f"Scene {i}"):
                    return False
        elif isinstance(json_data, dict):
            # Single scene graph
            if not self._validate_single_scene_graph(json_data, "Scene"):
                return False
        else:
            self.errors.append(f"Scene graph must be object or array, got {type(json_data).__name__}")
            return False
        
        return True
    
    def _validate_single_scene_graph(self, scene: Any, context: str) -> bool:
        """Validate a single scene graph object.
        
        Args:
            scene: Scene graph object
            context: Context for error messages
            
        Returns:
            True if valid
        """
        if not isinstance(scene, dict):
            self.errors.append(f"{context}: Must be an object, got {type(scene).__name__}")
            return False
        
        # Check required fields
        required_fields = ['time', 'nodes', 'edges']
        for field in required_fields:
            if field not in scene:
                self.errors.append(f"{context}: Missing required field '{field}'")
                return False
        
        # Validate time
        if not isinstance(scene['time'], str) or not scene['time'].strip():
            self.errors.append(f"{context}: 'time' must be a non-empty string")
        
        # Validate nodes
        if not self._validate_nodes(scene['nodes'], context):
            return False
        
        # Validate edges
        if not self._validate_edges(scene['edges'], context):
            return False
        
        return True
    
    def _validate_nodes(self, nodes: Any, context: str) -> bool:
        """Validate nodes array.
        
        Args:
            nodes: Nodes data
            context: Context for error messages
            
        Returns:
            True if valid
        """
        if not isinstance(nodes, list):
            self.errors.append(f"{context}: 'nodes' must be an array")
            return False
        
        node_ids = set()
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                self.errors.append(f"{context}: Node {i} must be an object")
                continue
            
            # Check required fields
            if 'id' not in node:
                self.errors.append(f"{context}: Node {i} missing 'id' field")
                continue
            
            if 'attributes' not in node:
                self.errors.append(f"{context}: Node {i} missing 'attributes' field")
                continue
            
            # Validate ID
            node_id = node['id']
            if not isinstance(node_id, str) or not node_id.strip():
                self.errors.append(f"{context}: Node {i} 'id' must be a non-empty string")
                continue
            
            # Check for duplicate IDs
            if node_id in node_ids:
                self.errors.append(f"{context}: Duplicate node ID '{node_id}'")
            node_ids.add(node_id)
            
            # Validate attributes
            attributes = node['attributes']
            if not isinstance(attributes, list):
                self.errors.append(f"{context}: Node {i} 'attributes' must be an array")
                continue
            
            for j, attr in enumerate(attributes):
                if not isinstance(attr, str):
                    self.warnings.append(f"{context}: Node {i} attribute {j} should be a string")
        
        return True
    
    def _validate_edges(self, edges: Any, context: str) -> bool:
        """Validate edges array.
        
        Args:
            edges: Edges data
            context: Context for error messages
            
        Returns:
            True if valid
        """
        if not isinstance(edges, list):
            self.errors.append(f"{context}: 'edges' must be an array")
            return False
        
        for i, edge in enumerate(edges):
            if not isinstance(edge, list):
                self.errors.append(f"{context}: Edge {i} must be an array")
                continue
            
            if len(edge) != 3:
                self.errors.append(f"{context}: Edge {i} must have exactly 3 elements [source, relation, target]")
                continue
            
            # Validate edge elements
            source, relation, target = edge
            for j, element in enumerate([source, relation, target]):
                if not isinstance(element, str) or not element.strip():
                    element_name = ['source', 'relation', 'target'][j]
                    self.errors.append(f"{context}: Edge {i} {element_name} must be a non-empty string")
        
        return True
    
    def validate_scene_graph_string(self, json_str: str) -> bool:
        """Validate scene graph JSON string.
        
        Args:
            json_str: JSON string to validate
            
        Returns:
            True if valid
        """
        is_valid_json, parsed_data = self.validate_json_string(json_str)
        if not is_valid_json:
            return False
        
        return self.validate_scene_graph_json(parsed_data)
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report with errors and warnings.
        
        Returns:
            Validation report dictionary
        """
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }
    
    def clear(self):
        """Clear errors and warnings."""
        self.errors.clear()
        self.warnings.clear()


class DataValidator:
    """Combined validator for CSV and JSON data."""
    
    def __init__(self):
        self.csv_validator = CSVValidator()
        self.json_validator = JSONValidator()
    
    def validate_annotation_file(self, file_path: Union[str, Path], 
                               rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate annotation CSV file comprehensively.
        
        Args:
            file_path: Path to CSV file
            rows: CSV rows data
            
        Returns:
            Comprehensive validation report
        """
        # Clear previous results
        self.csv_validator.clear()
        self.json_validator.clear()
        
        # Validate file existence
        file_valid = self.csv_validator.validate_file_exists(file_path)
        
        # Validate CSV structure
        structure_valid = self.csv_validator.validate_annotation_format(rows)
        
        # Validate JSON content
        json_stats = {'valid': 0, 'invalid': 0, 'empty': 0}
        
        for i, row in enumerate(rows, 1):
            scenegraph = row.get('scenegraph', '')
            
            if not scenegraph or not scenegraph.strip():
                json_stats['empty'] += 1
                continue
            
            if self.json_validator.validate_scene_graph_string(scenegraph):
                json_stats['valid'] += 1
            else:
                json_stats['invalid'] += 1
                # Only keep first few JSON errors to avoid spam
                if json_stats['invalid'] <= 5:
                    for error in self.json_validator.errors:
                        self.csv_validator.errors.append(f"Row {i} JSON: {error}")
                self.json_validator.clear()
        
        # Combine results
        csv_report = self.csv_validator.get_validation_report()
        
        return {
            'file_valid': file_valid,
            'structure_valid': structure_valid,
            'overall_valid': csv_report['valid'],
            'total_rows': len(rows),
            'json_stats': json_stats,
            'errors': csv_report['errors'],
            'warnings': csv_report['warnings'],
            'error_count': csv_report['error_count'],
            'warning_count': csv_report['warning_count']
        }
    
    def validate_input_file(self, file_path: Union[str, Path], 
                          rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate input CSV file.
        
        Args:
            file_path: Path to CSV file
            rows: CSV rows data
            
        Returns:
            Validation report
        """
        # Clear previous results
        self.csv_validator.clear()
        
        # Validate file and structure
        file_valid = self.csv_validator.validate_file_exists(file_path)
        structure_valid = self.csv_validator.validate_input_format(rows)
        
        csv_report = self.csv_validator.get_validation_report()
        
        return {
            'file_valid': file_valid,
            'structure_valid': structure_valid,
            'overall_valid': csv_report['valid'],
            'total_rows': len(rows),
            'errors': csv_report['errors'],
            'warnings': csv_report['warnings'],
            'error_count': csv_report['error_count'],
            'warning_count': csv_report['warning_count']
        }