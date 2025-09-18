"""Tests for FormatterService."""

import pytest
import pandas as pd
from pathlib import Path

from text2sg.services.formatter import FormatterService, format_csv_to_annotation
from text2sg.core.exceptions import FileProcessingError, ValidationError


class TestFormatterService:
    """Tests for FormatterService class."""
    
    def test_init_default(self):
        """Test FormatterService initialization with defaults."""
        formatter = FormatterService()
        
        assert formatter.default_input_column == "input"
        assert formatter.default_output_column == "output"
        assert "Please annotate" in formatter.default_prompt_template
    
    def test_init_custom(self):
        """Test FormatterService initialization with custom values."""
        custom_template = "Custom template: {input}"
        formatter = FormatterService(
            default_input_column="text",
            default_output_column="annotation",
            default_prompt_template=custom_template
        )
        
        assert formatter.default_input_column == "text"
        assert formatter.default_output_column == "annotation"
        assert formatter.default_prompt_template == custom_template
    
    def test_format_csv_basic(self, temp_dir: Path, sample_csv_data: pd.DataFrame):
        """Test basic CSV formatting."""
        # Setup
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        sample_csv_data.to_csv(input_file, index=False)
        
        formatter = FormatterService()
        
        # Execute
        result = formatter.format_csv(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 3
        assert output_file.exists()
        
        # Check output content
        output_df = pd.read_csv(output_file)
        assert 'input' in output_df.columns
        assert 'output' in output_df.columns
        assert len(output_df) == 3
        
        # Check that output column contains the prompt template
        for output_text in output_df['output']:
            assert "Please annotate" in output_text
    
    def test_format_csv_custom_columns(self, temp_dir: Path):
        """Test CSV formatting with custom column names."""
        # Setup
        input_data = pd.DataFrame({
            'text': ['A red car', 'A blue house'],
            'id': [1, 2]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        formatter = FormatterService()
        
        # Execute
        result = formatter.format_csv(
            input_file=input_file,
            output_file=output_file,
            input_column="text",
            output_column="annotation"
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 2
        
        output_df = pd.read_csv(output_file)
        assert 'text' in output_df.columns
        assert 'annotation' in output_df.columns
        assert 'id' in output_df.columns  # Original columns preserved
    
    def test_format_csv_custom_template(self, temp_dir: Path, sample_csv_data: pd.DataFrame):
        """Test CSV formatting with custom prompt template."""
        # Setup
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        sample_csv_data.to_csv(input_file, index=False)
        
        custom_template = "Generate scene graph for: {input}"
        formatter = FormatterService()
        
        # Execute
        result = formatter.format_csv(
            input_file=input_file,
            output_file=output_file,
            prompt_template=custom_template
        )
        
        # Verify
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        for i, row in output_df.iterrows():
            expected_output = custom_template.format(input=row['input'])
            assert row['output'] == expected_output
    
    def test_format_csv_with_backup(self, temp_dir: Path, sample_csv_data: pd.DataFrame):
        """Test CSV formatting with backup creation."""
        # Setup
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        sample_csv_data.to_csv(input_file, index=False)
        
        formatter = FormatterService()
        
        # Execute
        result = formatter.format_csv(
            input_file=input_file,
            output_file=output_file,
            create_backup=True
        )
        
        # Verify
        assert result['success'] is True
        assert 'backup_file' in result
        
        backup_file = Path(result['backup_file'])
        assert backup_file.exists()
        assert backup_file.name.startswith('input_backup_')
    
    def test_format_csv_missing_input_file(self, temp_dir: Path):
        """Test error handling for missing input file."""
        input_file = temp_dir / "nonexistent.csv"
        output_file = temp_dir / "output.csv"
        
        formatter = FormatterService()
        
        with pytest.raises(FileProcessingError):
            formatter.format_csv(input_file=input_file, output_file=output_file)
    
    def test_format_csv_missing_input_column(self, temp_dir: Path):
        """Test error handling for missing input column."""
        # Setup - CSV without 'input' column
        input_data = pd.DataFrame({
            'text': ['A red car', 'A blue house'],
            'id': [1, 2]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        formatter = FormatterService()
        
        with pytest.raises(ValidationError):
            formatter.format_csv(input_file=input_file, output_file=output_file)
    
    def test_format_batch(self, temp_dir: Path):
        """Test batch formatting of multiple files."""
        # Setup multiple input files
        files = []
        for i in range(3):
            data = pd.DataFrame({
                'input': [f'Text {i}_1', f'Text {i}_2'],
                'id': [1, 2]
            })
            input_file = temp_dir / f"input_{i}.csv"
            output_file = temp_dir / f"output_{i}.csv"
            data.to_csv(input_file, index=False)
            files.append((input_file, output_file))
        
        formatter = FormatterService()
        
        # Execute
        results = formatter.format_batch(files)
        
        # Verify
        assert len(results) == 3
        for result in results:
            assert result['success'] is True
            assert result['processed_rows'] == 2
        
        # Check all output files exist
        for _, output_file in files:
            assert output_file.exists()
    
    def test_get_statistics(self, temp_dir: Path, sample_csv_data: pd.DataFrame):
        """Test getting processing statistics."""
        # Setup
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        sample_csv_data.to_csv(input_file, index=False)
        
        formatter = FormatterService()
        
        # Execute formatting
        formatter.format_csv(input_file=input_file, output_file=output_file)
        
        # Get statistics
        stats = formatter.get_statistics()
        
        # Verify
        assert 'total_files_processed' in stats
        assert 'total_rows_processed' in stats
        assert 'success_rate' in stats
        assert stats['total_files_processed'] == 1
        assert stats['total_rows_processed'] == 3
        assert stats['success_rate'] == 100.0


class TestFormatterConvenienceFunctions:
    """Tests for formatter convenience functions."""
    
    def test_format_csv_to_annotation(self, temp_dir: Path, sample_csv_data: pd.DataFrame):
        """Test format_csv_to_annotation convenience function."""
        # Setup
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        sample_csv_data.to_csv(input_file, index=False)
        
        # Execute
        result = format_csv_to_annotation(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 3
        assert output_file.exists()
    
    def test_format_csv_to_annotation_with_custom_template(self, temp_dir: Path, sample_csv_data: pd.DataFrame):
        """Test convenience function with custom template."""
        # Setup
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        sample_csv_data.to_csv(input_file, index=False)
        
        custom_template = "Create scene graph: {input}"
        
        # Execute
        result = format_csv_to_annotation(
            input_file=input_file,
            output_file=output_file,
            prompt_template=custom_template
        )
        
        # Verify
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        for i, row in output_df.iterrows():
            assert "Create scene graph:" in row['output']