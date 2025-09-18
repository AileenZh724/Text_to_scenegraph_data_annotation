"""Text2SG services module.

Provides high-level services for scene graph generation workflows:
- FormatterService: Convert CSV data to annotation format
- ExtractorService: Extract specific columns from CSV files
- FixerService: Fix common CSV issues like multiline JSON
- PipelineService: Orchestrate complete workflows
- ColorEnricherService: Enrich text descriptions with color information
"""

from .formatter import FormatterService, format_csv_to_annotation, format_csv_batch
from .extractor import ExtractorService, extract_input_column, extract_columns
from .fixer import FixerService, fix_multiline_json_csv, fix_csv_batch
from .pipeline import (
    PipelineService,
    run_complete_pipeline,
    run_data_preparation,
    run_scene_graph_generation
)
from .color_enricher import ColorEnricherService

__all__ = [
    # Service classes
    'FormatterService',
    'ExtractorService', 
    'FixerService',
    'PipelineService',
    'ColorEnricherService',
    
    # Convenience functions
    'format_csv_to_annotation',
    'format_csv_batch',
    'extract_input_column',
    'extract_columns',
    'fix_multiline_json_csv',
    'fix_csv_batch',
    'run_complete_pipeline',
    'run_data_preparation',
    'run_scene_graph_generation'
]