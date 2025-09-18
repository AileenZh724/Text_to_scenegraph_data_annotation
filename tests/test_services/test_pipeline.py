"""Tests for PipelineService."""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

from text2sg.services.pipeline import PipelineService, run_complete_pipeline
from text2sg.core.exceptions import PipelineError, ValidationError


class TestPipelineService:
    """Tests for PipelineService class."""
    
    def test_init_default(self):
        """Test PipelineService initialization with defaults."""
        pipeline = PipelineService()
        
        assert pipeline.default_input_column == "input"
        assert pipeline.default_output_column == "output"
        assert pipeline.batch_size == 10
        assert pipeline.max_retries == 3
        assert pipeline.enable_validation is True
    
    def test_init_custom(self):
        """Test PipelineService initialization with custom values."""
        pipeline = PipelineService(
            default_input_column="text",
            default_output_column="annotation",
            batch_size=5,
            max_retries=1,
            enable_validation=False
        )
        
        assert pipeline.default_input_column == "text"
        assert pipeline.default_output_column == "annotation"
        assert pipeline.batch_size == 5
        assert pipeline.max_retries == 1
        assert pipeline.enable_validation is False
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_basic(self, mock_provider_class, temp_dir: Path):
        """Test basic pipeline execution."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car'], 'attributes': ['red']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['A red car', 'A blue house'],
            'id': [1, 2]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService()
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 2
        assert result['successful_generations'] == 2
        assert result['failed_generations'] == 0
        assert output_file.exists()
        
        # Check output content
        output_df = pd.read_csv(output_file)
        assert len(output_df) == 2
        assert 'input' in output_df.columns
        assert 'output' in output_df.columns
        assert 'id' in output_df.columns
        
        # Verify provider was called correctly
        assert mock_provider.generate_scene_graph.call_count == 2
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_custom_columns(self, mock_provider_class, temp_dir: Path):
        """Test pipeline with custom column names."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'text': ['A red car'],
            'metadata': ['test']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService()
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key",
            input_column="text",
            output_column="annotation"
        )
        
        # Verify
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        assert 'text' in output_df.columns
        assert 'annotation' in output_df.columns
        assert 'metadata' in output_df.columns
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_with_batching(self, mock_provider_class, temp_dir: Path):
        """Test pipeline with batch processing."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['item']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data - more rows than batch size
        input_data = pd.DataFrame({
            'input': [f'Text {i}' for i in range(15)]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService(batch_size=5)
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 15
        assert result['batches_processed'] == 3  # 15 rows / 5 batch_size
        
        # Verify all rows were processed
        output_df = pd.read_csv(output_file)
        assert len(output_df) == 15
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_with_failures(self, mock_provider_class, temp_dir: Path):
        """Test pipeline handling API failures."""
        # Setup mock provider with some failures
        mock_provider = Mock()
        
        def mock_generate(text):
            if 'fail' in text:
                return {'success': False, 'error': 'API error'}
            return {'success': True, 'scene_graph': {'objects': ['item']}}
        
        mock_provider.generate_scene_graph.side_effect = mock_generate
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['Success text', 'This will fail', 'Another success']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService()
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Verify
        assert result['success'] is True  # Overall success even with some failures
        assert result['processed_rows'] == 3
        assert result['successful_generations'] == 2
        assert result['failed_generations'] == 1
        
        output_df = pd.read_csv(output_file)
        assert len(output_df) == 3
        
        # Check that failed row has error message
        failed_row = output_df[output_df['input'] == 'This will fail']
        assert len(failed_row) == 1
        assert 'error' in failed_row['output'].iloc[0].lower()
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_with_retries(self, mock_provider_class, temp_dir: Path):
        """Test pipeline retry mechanism."""
        # Setup mock provider with initial failures then success
        mock_provider = Mock()
        call_count = 0
        
        def mock_generate(text):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                return {'success': False, 'error': 'Temporary error'}
            return {'success': True, 'scene_graph': {'objects': ['item']}}
        
        mock_provider.generate_scene_graph.side_effect = mock_generate
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['Test text']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService(max_retries=3)
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Verify
        assert result['success'] is True
        assert result['successful_generations'] == 1
        assert result['failed_generations'] == 0
        
        # Verify retries occurred
        assert mock_provider.generate_scene_graph.call_count == 3
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_with_validation(self, mock_provider_class, temp_dir: Path):
        """Test pipeline with output validation."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car'], 'attributes': ['red']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['A red car']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService(enable_validation=True)
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Verify
        assert result['success'] is True
        assert 'validation_results' in result
        assert result['validation_results']['valid_outputs'] == 1
        assert result['validation_results']['invalid_outputs'] == 0
    
    def test_run_pipeline_missing_input_file(self, temp_dir: Path):
        """Test error handling for missing input file."""
        input_file = temp_dir / "nonexistent.csv"
        output_file = temp_dir / "output.csv"
        
        pipeline = PipelineService()
        
        with pytest.raises(PipelineError):
            pipeline.run_pipeline(
                input_file=input_file,
                output_file=output_file,
                api_key="test_key"
            )
    
    def test_run_pipeline_missing_input_column(self, temp_dir: Path):
        """Test error handling for missing input column."""
        # Setup - CSV without 'input' column
        input_data = pd.DataFrame({
            'text': ['A red car'],
            'id': [1]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService()
        
        with pytest.raises(ValidationError):
            pipeline.run_pipeline(
                input_file=input_file,
                output_file=output_file,
                api_key="test_key"
            )
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_pipeline_with_backup(self, mock_provider_class, temp_dir: Path):
        """Test pipeline with backup creation."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['A red car']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService()
        
        # Execute
        result = pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key",
            create_backup=True
        )
        
        # Verify
        assert result['success'] is True
        assert 'backup_file' in result
        
        backup_file = Path(result['backup_file'])
        assert backup_file.exists()
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_get_statistics(self, mock_provider_class, temp_dir: Path):
        """Test getting pipeline statistics."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['A red car', 'A blue house']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        pipeline = PipelineService()
        
        # Execute pipeline
        pipeline.run_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Get statistics
        stats = pipeline.get_statistics()
        
        # Verify
        assert 'total_pipelines_run' in stats
        assert 'total_rows_processed' in stats
        assert 'total_successful_generations' in stats
        assert 'total_failed_generations' in stats
        assert 'success_rate' in stats
        assert 'average_processing_time' in stats
        assert stats['total_pipelines_run'] == 1
        assert stats['total_rows_processed'] == 2
        assert stats['success_rate'] == 100.0


class TestPipelineConvenienceFunctions:
    """Tests for pipeline convenience functions."""
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_complete_pipeline(self, mock_provider_class, temp_dir: Path):
        """Test run_complete_pipeline convenience function."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'input': ['A red car']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        # Execute
        result = run_complete_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key"
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 1
        assert output_file.exists()
    
    @patch('text2sg.services.pipeline.GeminiProvider')
    def test_run_complete_pipeline_with_options(self, mock_provider_class, temp_dir: Path):
        """Test convenience function with custom options."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup input data
        input_data = pd.DataFrame({
            'text': ['A red car']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        # Execute
        result = run_complete_pipeline(
            input_file=input_file,
            output_file=output_file,
            api_key="test_key",
            input_column="text",
            batch_size=5,
            max_retries=1
        )
        
        # Verify
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        assert 'text' in output_df.columns