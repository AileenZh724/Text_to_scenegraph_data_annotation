"""Tests for CLI main module."""

import pytest
import pandas as pd
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import Mock, patch

from text2sg.cli.main import app


class TestCLICommands:
    """Tests for CLI commands."""
    
    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()
    
    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        
        assert result.exit_code == 0
        assert "Text2SG" in result.stdout
        assert "version" in result.stdout.lower()
    
    @patch('text2sg.cli.main.FormatterService')
    def test_format_command_basic(self, mock_formatter_class, temp_dir: Path):
        """Test basic format command."""
        # Setup mock formatter
        mock_formatter = Mock()
        mock_formatter.format_csv.return_value = {
            'success': True,
            'processed_rows': 2
        }
        mock_formatter_class.return_value = mock_formatter
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command
        result = self.runner.invoke(app, [
            "format",
            str(input_file),
            str(output_file)
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "Successfully formatted" in result.stdout
        mock_formatter.format_csv.assert_called_once()
    
    @patch('text2sg.cli.main.FormatterService')
    def test_format_command_with_options(self, mock_formatter_class, temp_dir: Path):
        """Test format command with custom options."""
        # Setup mock formatter
        mock_formatter = Mock()
        mock_formatter.format_csv.return_value = {
            'success': True,
            'processed_rows': 1
        }
        mock_formatter_class.return_value = mock_formatter
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'text': ['Sample text']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command with options
        result = self.runner.invoke(app, [
            "format",
            str(input_file),
            str(output_file),
            "--input-column", "text",
            "--output-column", "annotation",
            "--template", "Custom template: {input}",
            "--backup"
        ])
        
        # Verify
        assert result.exit_code == 0
        
        # Check that formatter was called with correct arguments
        call_args = mock_formatter.format_csv.call_args
        assert call_args[1]['input_column'] == 'text'
        assert call_args[1]['output_column'] == 'annotation'
        assert call_args[1]['prompt_template'] == 'Custom template: {input}'
        assert call_args[1]['create_backup'] is True
    
    @patch('text2sg.cli.main.ExtractorService')
    def test_extract_command_basic(self, mock_extractor_class, temp_dir: Path):
        """Test basic extract command."""
        # Setup mock extractor
        mock_extractor = Mock()
        mock_extractor.extract_columns.return_value = {
            'success': True,
            'extracted_rows': 2,
            'extracted_columns': ['input', 'output']
        }
        mock_extractor_class.return_value = mock_extractor
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2'],
            'extra': ['Extra 1', 'Extra 2']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command
        result = self.runner.invoke(app, [
            "extract",
            str(input_file),
            str(output_file),
            "--columns", "input,output"
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "Successfully extracted" in result.stdout
        mock_extractor.extract_columns.assert_called_once()
    
    @patch('text2sg.cli.main.ExtractorService')
    def test_extract_command_with_options(self, mock_extractor_class, temp_dir: Path):
        """Test extract command with custom options."""
        # Setup mock extractor
        mock_extractor = Mock()
        mock_extractor.extract_columns.return_value = {
            'success': True,
            'extracted_rows': 1,
            'extracted_columns': ['text'],
            'skipped_columns': ['nonexistent']
        }
        mock_extractor_class.return_value = mock_extractor
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'text': ['Sample text']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command with options
        result = self.runner.invoke(app, [
            "extract",
            str(input_file),
            str(output_file),
            "--columns", "text,nonexistent",
            "--handle-missing", "skip",
            "--no-preserve-order",
            "--backup"
        ])
        
        # Verify
        assert result.exit_code == 0
        
        # Check that extractor was called with correct arguments
        call_args = mock_extractor.extract_columns.call_args
        assert call_args[1]['columns'] == ['text', 'nonexistent']
        assert call_args[1]['create_backup'] is True
    
    @patch('text2sg.cli.main.FixerService')
    def test_fix_command_basic(self, mock_fixer_class, temp_dir: Path):
        """Test basic fix command."""
        # Setup mock fixer
        mock_fixer = Mock()
        mock_fixer.fix_multiline_json.return_value = {
            'success': True,
            'processed_rows': 1,
            'fixed_rows': 1
        }
        mock_fixer_class.return_value = mock_fixer
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'output': ['{\n  "objects": ["car"]\n}']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command
        result = self.runner.invoke(app, [
            "fix",
            str(input_file),
            str(output_file)
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "Successfully fixed" in result.stdout
        mock_fixer.fix_multiline_json.assert_called_once()
    
    @patch('text2sg.cli.main.FixerService')
    def test_fix_command_with_options(self, mock_fixer_class, temp_dir: Path):
        """Test fix command with custom options."""
        # Setup mock fixer
        mock_fixer = Mock()
        mock_fixer.fix_multiline_json.return_value = {
            'success': True,
            'processed_rows': 1,
            'fixed_rows': 1,
            'strategy_used': 'compact'
        }
        mock_fixer_class.return_value = mock_fixer
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'annotation': ['{\n  "objects": ["car"]\n}']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command with options
        result = self.runner.invoke(app, [
            "fix",
            str(input_file),
            str(output_file),
            "--column", "annotation",
            "--strategy", "compact",
            "--no-preserve-original",
            "--no-validate",
            "--backup"
        ])
        
        # Verify
        assert result.exit_code == 0
        
        # Check that fixer was called with correct arguments
        call_args = mock_fixer.fix_multiline_json.call_args
        assert call_args[1]['column'] == 'annotation'
        assert call_args[1]['create_backup'] is True
    
    @patch('text2sg.cli.main.GeminiProvider')
    def test_generate_command_basic(self, mock_provider_class, temp_dir: Path):
        """Test basic generate command."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car'], 'attributes': ['red']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Execute command
        result = self.runner.invoke(app, [
            "generate",
            "A red car",
            "--api-key", "test_key"
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "Scene Graph Generated" in result.stdout
        mock_provider.generate_scene_graph.assert_called_once_with("A red car")
    
    @patch('text2sg.cli.main.GeminiProvider')
    def test_generate_command_with_options(self, mock_provider_class, temp_dir: Path):
        """Test generate command with output file."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_scene_graph.return_value = {
            'success': True,
            'scene_graph': {'objects': ['car']}
        }
        mock_provider_class.return_value = mock_provider
        
        # Setup output file
        output_file = temp_dir / "output.json"
        
        # Execute command
        result = self.runner.invoke(app, [
            "generate",
            "A red car",
            "--api-key", "test_key",
            "--output", str(output_file),
            "--model", "gemini-pro",
            "--temperature", "0.5"
        ])
        
        # Verify
        assert result.exit_code == 0
        assert output_file.exists()
    
    @patch('text2sg.cli.main.PipelineService')
    def test_pipeline_command_basic(self, mock_pipeline_class, temp_dir: Path):
        """Test basic pipeline command."""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.run_pipeline.return_value = {
            'success': True,
            'processed_rows': 2,
            'successful_generations': 2,
            'failed_generations': 0
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'input': ['A red car', 'A blue house']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command
        result = self.runner.invoke(app, [
            "pipeline",
            str(input_file),
            str(output_file),
            "--api-key", "test_key"
        ])
        
        # Verify
        assert result.exit_code == 0
        assert "Pipeline completed successfully" in result.stdout
        mock_pipeline.run_pipeline.assert_called_once()
    
    @patch('text2sg.cli.main.PipelineService')
    def test_pipeline_command_with_options(self, mock_pipeline_class, temp_dir: Path):
        """Test pipeline command with custom options."""
        # Setup mock pipeline
        mock_pipeline = Mock()
        mock_pipeline.run_pipeline.return_value = {
            'success': True,
            'processed_rows': 1,
            'successful_generations': 1,
            'failed_generations': 0
        }
        mock_pipeline_class.return_value = mock_pipeline
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'text': ['Sample text']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command with options
        result = self.runner.invoke(app, [
            "pipeline",
            str(input_file),
            str(output_file),
            "--api-key", "test_key",
            "--input-column", "text",
            "--output-column", "annotation",
            "--batch-size", "5",
            "--max-retries", "2",
            "--model", "gemini-pro",
            "--temperature", "0.7",
            "--no-validation",
            "--backup"
        ])
        
        # Verify
        assert result.exit_code == 0
        
        # Check that pipeline was called with correct arguments
        call_args = mock_pipeline.run_pipeline.call_args
        assert call_args[1]['input_column'] == 'text'
        assert call_args[1]['output_column'] == 'annotation'
        assert call_args[1]['create_backup'] is True
    
    def test_invalid_command(self):
        """Test handling of invalid commands."""
        result = self.runner.invoke(app, ["invalid_command"])
        
        assert result.exit_code != 0
    
    def test_help_command(self):
        """Test help command."""
        result = self.runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Text2SG" in result.stdout
        assert "Commands:" in result.stdout
        assert "format" in result.stdout
        assert "extract" in result.stdout
        assert "fix" in result.stdout
        assert "generate" in result.stdout
        assert "pipeline" in result.stdout
    
    def test_command_help(self):
        """Test individual command help."""
        result = self.runner.invoke(app, ["format", "--help"])
        
        assert result.exit_code == 0
        assert "Format CSV" in result.stdout
        assert "input-file" in result.stdout
        assert "output-file" in result.stdout
    
    @patch('text2sg.cli.main.FormatterService')
    def test_error_handling(self, mock_formatter_class, temp_dir: Path):
        """Test CLI error handling."""
        # Setup mock formatter to raise exception
        mock_formatter = Mock()
        mock_formatter.format_csv.side_effect = Exception("Test error")
        mock_formatter_class.return_value = mock_formatter
        
        # Setup test files
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        
        input_data = pd.DataFrame({
            'input': ['Text 1']
        })
        input_data.to_csv(input_file, index=False)
        
        # Execute command
        result = self.runner.invoke(app, [
            "format",
            str(input_file),
            str(output_file)
        ])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "Error" in result.stdout or "Error" in result.stderr
    
    def test_missing_required_arguments(self):
        """Test handling of missing required arguments."""
        # Test format command without required files
        result = self.runner.invoke(app, ["format"])
        
        assert result.exit_code != 0
    
    def test_nonexistent_input_file(self, temp_dir: Path):
        """Test handling of nonexistent input files."""
        input_file = temp_dir / "nonexistent.csv"
        output_file = temp_dir / "output.csv"
        
        result = self.runner.invoke(app, [
            "format",
            str(input_file),
            str(output_file)
        ])
        
        assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def setup_method(self):
        """Setup test runner."""
        self.runner = CliRunner()
    
    def test_format_extract_pipeline(self, temp_dir: Path):
        """Test chaining format and extract commands."""
        # This would be an integration test that actually runs the commands
        # For now, we'll just test that the commands can be invoked
        
        # Setup initial data
        input_data = pd.DataFrame({
            'text': ['A red car', 'A blue house'],
            'id': [1, 2],
            'metadata': ['meta1', 'meta2']
        })
        
        input_file = temp_dir / "input.csv"
        formatted_file = temp_dir / "formatted.csv"
        extracted_file = temp_dir / "extracted.csv"
        
        input_data.to_csv(input_file, index=False)
        
        # Note: In a real integration test, we would run actual commands
        # Here we just verify the CLI structure is correct
        
        # Test that commands exist and have proper help
        format_help = self.runner.invoke(app, ["format", "--help"])
        extract_help = self.runner.invoke(app, ["extract", "--help"])
        
        assert format_help.exit_code == 0
        assert extract_help.exit_code == 0
        assert "input-column" in format_help.stdout
        assert "columns" in extract_help.stdout