"""Pipeline service for orchestrating scene graph generation workflows.

Provides high-level workflows that combine multiple services:
- Data preparation (formatting, extraction, fixing)
- Scene graph generation using various providers
- Result processing and validation
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable

from ..models import AnnotatedRow, SceneGraph
from ..providers.base import ProviderRegistry
from ..io.csv_io import CSVReader, CSVWriter
from ..io.validators import DataValidator
from .formatter import FormatterService
from .extractor import ExtractorService
from .fixer import FixerService


class PipelineService:
    """Service for orchestrating complete scene graph generation pipelines."""
    
    def __init__(self):
        self.formatter = FormatterService()
        self.extractor = ExtractorService()
        self.fixer = FixerService()
        self.csv_reader = CSVReader()
        self.csv_writer = CSVWriter()
        self.validator = DataValidator()
        self.provider_registry = ProviderRegistry()
    
    def prepare_data_pipeline(self, 
                            input_file: Union[str, Path],
                            output_file: Union[str, Path],
                            steps: List[str] = None,
                            **kwargs) -> Dict[str, Any]:
        """Run data preparation pipeline.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to output CSV file
            steps: List of preparation steps to run
            **kwargs: Additional arguments for each step
            
        Returns:
            Pipeline execution results
        """
        if steps is None:
            steps = ['fix', 'format']
        
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        results = {
            'success': True,
            'input_file': str(input_path),
            'output_file': str(output_path),
            'steps_executed': [],
            'step_results': {},
            'errors': []
        }
        
        current_file = input_path
        
        try:
            # Step 1: Fix multiline JSON issues
            if 'fix' in steps:
                temp_fixed = input_path.parent / f"temp_fixed_{input_path.name}"
                fix_result = self.fixer.fix_multiline_json(
                    current_file, temp_fixed, 
                    create_backup=False,
                    **kwargs.get('fix', {})
                )
                
                results['steps_executed'].append('fix')
                results['step_results']['fix'] = fix_result
                
                if fix_result['success']:
                    current_file = temp_fixed
                else:
                    results['success'] = False
                    results['errors'].append(f"Fix step failed: {fix_result['error']}")
                    return results
            
            # Step 2: Format to annotation format
            if 'format' in steps:
                format_result = self.formatter.format_to_annotation(
                    current_file, output_path,
                    **kwargs.get('format', {})
                )
                
                results['steps_executed'].append('format')
                results['step_results']['format'] = format_result
                
                if not format_result['success']:
                    results['success'] = False
                    results['errors'].append(f"Format step failed: {format_result['error']}")
                    return results
            
            # Step 3: Extract specific columns
            if 'extract' in steps:
                extract_result = self.extractor.extract_input_column(
                    current_file, output_path,
                    **kwargs.get('extract', {})
                )
                
                results['steps_executed'].append('extract')
                results['step_results']['extract'] = extract_result
                
                if not extract_result['success']:
                    results['success'] = False
                    results['errors'].append(f"Extract step failed: {extract_result['error']}")
                    return results
            
            # Clean up temporary files
            if 'fix' in steps and current_file != input_path:
                try:
                    current_file.unlink()
                except Exception:
                    pass  # Ignore cleanup errors
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Pipeline execution failed: {str(e)}")
        
        return results
    
    def generate_scene_graphs_pipeline(self, 
                                     input_file: Union[str, Path],
                                     output_file: Union[str, Path],
                                     provider_name: str,
                                     batch_size: int = 10,
                                     max_retries: int = 3,
                                     progress_callback: Optional[Callable] = None,
                                     **provider_kwargs) -> Dict[str, Any]:
        """Run scene graph generation pipeline.
        
        Args:
            input_file: Path to input CSV file with annotation format
            output_file: Path to output CSV file
            provider_name: Name of the scene graph provider
            batch_size: Number of items to process in each batch
            max_retries: Maximum number of retries for failed items
            progress_callback: Optional callback for progress updates
            **provider_kwargs: Additional arguments for the provider
            
        Returns:
            Pipeline execution results
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        results = {
            'success': True,
            'input_file': str(input_path),
            'output_file': str(output_path),
            'provider_name': provider_name,
            'total_items': 0,
            'processed_items': 0,
            'successful_items': 0,
            'failed_items': 0,
            'errors': [],
            'processing_stats': {}
        }
        
        try:
            # Load input data
            annotation_rows = self.csv_reader.read_annotation_csv(input_path)
            results['total_items'] = len(annotation_rows)
            
            if not annotation_rows:
                results['errors'].append("No data found in input file")
                results['success'] = False
                return results
            
            # Get provider
            provider = self.provider_registry.get_provider(provider_name)
            if not provider:
                results['errors'].append(f"Provider '{provider_name}' not found")
                results['success'] = False
                return results
            
            # Configure provider
            provider.configure(**provider_kwargs)
            
            # Process in batches
            processed_rows = []
            
            for i in range(0, len(annotation_rows), batch_size):
                batch = annotation_rows[i:i + batch_size]
                batch_inputs = [row.input for row in batch if row.input.strip()]
                
                if not batch_inputs:
                    # Skip empty batch but keep original rows
                    processed_rows.extend(batch)
                    continue
                
                # Generate scene graphs for batch
                try:
                    batch_results = provider.generate_batch(
                        batch_inputs, 
                        max_retries=max_retries
                    )
                    
                    # Update annotation rows with results
                    for j, row in enumerate(batch):
                        if row.input.strip() and j < len(batch_results):
                            scene_graphs = batch_results[j]
                            if scene_graphs:
                                row.scenegraph = scene_graphs
                                row.is_annotated = True
                                results['successful_items'] += 1
                            else:
                                results['failed_items'] += 1
                        
                        processed_rows.append(row)
                        results['processed_items'] += 1
                    
                    # Progress callback
                    if progress_callback:
                        progress = results['processed_items'] / results['total_items']
                        progress_callback(progress, results['processed_items'], results['total_items'])
                
                except Exception as e:
                    # Handle batch failure
                    error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
                    results['errors'].append(error_msg)
                    
                    # Add original rows without scene graphs
                    for row in batch:
                        processed_rows.append(row)
                        results['processed_items'] += 1
                        results['failed_items'] += 1
            
            # Write results
            self.csv_writer.write_annotation_csv(output_path, processed_rows)
            
            # Calculate final statistics
            results['processing_stats'] = {
                'success_rate': results['successful_items'] / results['total_items'] if results['total_items'] > 0 else 0,
                'failure_rate': results['failed_items'] / results['total_items'] if results['total_items'] > 0 else 0,
                'completion_rate': results['processed_items'] / results['total_items'] if results['total_items'] > 0 else 0
            }
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Pipeline execution failed: {str(e)}")
        
        return results
    
    def complete_pipeline(self, 
                        input_file: Union[str, Path],
                        output_file: Union[str, Path],
                        provider_name: str,
                        preparation_steps: List[str] = None,
                        **kwargs) -> Dict[str, Any]:
        """Run complete pipeline from raw data to scene graphs.
        
        Args:
            input_file: Path to raw input CSV file
            output_file: Path to final output CSV file
            provider_name: Name of the scene graph provider
            preparation_steps: List of data preparation steps
            **kwargs: Additional arguments for each pipeline stage
            
        Returns:
            Complete pipeline execution results
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        
        results = {
            'success': True,
            'input_file': str(input_path),
            'output_file': str(output_path),
            'provider_name': provider_name,
            'stages': {},
            'errors': []
        }
        
        try:
            # Stage 1: Data preparation
            temp_prepared = input_path.parent / f"temp_prepared_{input_path.name}"
            
            prep_result = self.prepare_data_pipeline(
                input_path, temp_prepared,
                steps=preparation_steps,
                **kwargs.get('preparation', {})
            )
            
            results['stages']['preparation'] = prep_result
            
            if not prep_result['success']:
                results['success'] = False
                results['errors'].extend(prep_result['errors'])
                return results
            
            # Stage 2: Scene graph generation
            generation_result = self.generate_scene_graphs_pipeline(
                temp_prepared, output_path,
                provider_name,
                **kwargs.get('generation', {})
            )
            
            results['stages']['generation'] = generation_result
            
            if not generation_result['success']:
                results['success'] = False
                results['errors'].extend(generation_result['errors'])
            
            # Clean up temporary files
            try:
                temp_prepared.unlink()
            except Exception:
                pass  # Ignore cleanup errors
        
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Complete pipeline failed: {str(e)}")
        
        return results
    
    def validate_pipeline_output(self, output_file: Union[str, Path]) -> Dict[str, Any]:
        """Validate pipeline output file.
        
        Args:
            output_file: Path to output CSV file
            
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
                'errors': [f"Failed to validate file: {str(e)}"],
                'warnings': []
            }
    
    def get_pipeline_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive statistics from pipeline results.
        
        Args:
            results: Pipeline execution results
            
        Returns:
            Statistics summary
        """
        stats = {
            'overall_success': results.get('success', False),
            'total_errors': len(results.get('errors', [])),
            'stages_completed': len(results.get('stages', {}))
        }
        
        # Add preparation stage stats
        if 'preparation' in results.get('stages', {}):
            prep_stats = results['stages']['preparation']
            stats['preparation'] = {
                'success': prep_stats.get('success', False),
                'steps_executed': len(prep_stats.get('steps_executed', [])),
                'errors': len(prep_stats.get('errors', []))
            }
        
        # Add generation stage stats
        if 'generation' in results.get('stages', {}):
            gen_stats = results['stages']['generation']
            stats['generation'] = {
                'success': gen_stats.get('success', False),
                'total_items': gen_stats.get('total_items', 0),
                'successful_items': gen_stats.get('successful_items', 0),
                'failed_items': gen_stats.get('failed_items', 0),
                'success_rate': gen_stats.get('processing_stats', {}).get('success_rate', 0)
            }
        
        return stats


def run_complete_pipeline(input_file: Union[str, Path],
                        output_file: Union[str, Path],
                        provider_name: str,
                        **kwargs) -> Dict[str, Any]:
    """Convenience function to run complete pipeline.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        provider_name: Name of scene graph provider
        **kwargs: Additional pipeline arguments
        
    Returns:
        Pipeline execution results
    """
    pipeline = PipelineService()
    return pipeline.complete_pipeline(input_file, output_file, provider_name, **kwargs)


def run_data_preparation(input_file: Union[str, Path],
                       output_file: Union[str, Path],
                       **kwargs) -> Dict[str, Any]:
    """Convenience function to run data preparation pipeline.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        **kwargs: Additional preparation arguments
        
    Returns:
        Preparation results
    """
    pipeline = PipelineService()
    return pipeline.prepare_data_pipeline(input_file, output_file, **kwargs)


def run_scene_graph_generation(input_file: Union[str, Path],
                             output_file: Union[str, Path],
                             provider_name: str,
                             **kwargs) -> Dict[str, Any]:
    """Convenience function to run scene graph generation pipeline.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        provider_name: Name of scene graph provider
        **kwargs: Additional generation arguments
        
    Returns:
        Generation results
    """
    pipeline = PipelineService()
    return pipeline.generate_scene_graphs_pipeline(input_file, output_file, provider_name, **kwargs)