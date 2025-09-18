"""Command-line interface for Text2SG.

Provides unified CLI commands for:
- format: Convert CSV data to annotation format
- extract: Extract specific columns from CSV files
- fix: Fix common CSV issues like multiline JSON
- generate: Generate scene graphs from text descriptions
- pipeline: Run complete workflows
"""

from .main import app

__all__ = ['app']