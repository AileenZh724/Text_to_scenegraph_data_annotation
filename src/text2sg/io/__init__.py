"""IO utilities for CSV processing and validation."""

from .csv_io import CSVReader, CSVWriter
from .validators import CSVValidator, JSONValidator

# Create a function that wraps the CSVValidator.validate_csv_structure method
def validate_csv_structure(rows, required_columns=None):
    """Wrapper for CSVValidator.validate_csv_structure method."""
    validator = CSVValidator()
    return validator.validate_csv_structure(rows, required_columns)

# Create a function that wraps JSONValidator.validate_json_string method
def validate_json_field(json_str):
    """Validate JSON field content."""
    validator = JSONValidator()
    return validator.validate_json_string(json_str)

__all__ = [
    "CSVReader",
    "CSVWriter", 
    "CSVValidator",
    "JSONValidator",
    "validate_csv_structure",
    "validate_json_field"
]