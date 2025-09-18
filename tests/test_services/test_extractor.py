"""Tests for ExtractorService."""

import pytest
import pandas as pd
from pathlib import Path

from text2sg.services.extractor import ExtractorService, extract_columns_from_csv
from text2sg.core.exceptions import FileProcessingError, ValidationError


class TestExtractorService:
    """Tests for ExtractorService class."""
    
    def test_init_default(self):
        """Test ExtractorService initialization with defaults."""
        extractor = ExtractorService()
        
        assert extractor.default_columns == ['input', 'output']
        assert extractor.preserve_order is True
        assert extractor.handle_missing == 'error'
    
    def test_init_custom(self):
        """Test ExtractorService initialization with custom values."""
        extractor = ExtractorService(
            default_columns=['text', 'annotation'],
            preserve_order=False,
            handle_missing='skip'
        )
        
        assert extractor.default_columns == ['text', 'annotation']
        assert extractor.preserve_order is False
        assert extractor.handle_missing == 'skip'
    
    def test_extract_columns_basic(self, temp_dir: Path):
        """Test basic column extraction."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2', 'Text 3'],
            'output': ['Output 1', 'Output 2', 'Output 3'],
            'extra': ['Extra 1', 'Extra 2', 'Extra 3'],
            'id': [1, 2, 3]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService()
        
        # Execute
        result = extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'output']
        )
        
        # Verify
        assert result['success'] is True
        assert result['extracted_rows'] == 3
        assert result['extracted_columns'] == ['input', 'output']
        assert output_file.exists()
        
        # Check output content
        output_df = pd.read_csv(output_file)
        assert list(output_df.columns) == ['input', 'output']
        assert len(output_df) == 3
        assert output_df['input'].tolist() == ['Text 1', 'Text 2', 'Text 3']
    
    def test_extract_columns_preserve_order(self, temp_dir: Path):
        """Test column extraction with order preservation."""
        # Setup
        input_data = pd.DataFrame({
            'id': [1, 2, 3],
            'input': ['Text 1', 'Text 2', 'Text 3'],
            'extra': ['Extra 1', 'Extra 2', 'Extra 3'],
            'output': ['Output 1', 'Output 2', 'Output 3']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService(preserve_order=True)
        
        # Execute - request columns in different order
        result = extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['output', 'input', 'id']
        )
        
        # Verify - should maintain requested order
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        assert list(output_df.columns) == ['output', 'input', 'id']
    
    def test_extract_columns_no_preserve_order(self, temp_dir: Path):
        """Test column extraction without order preservation."""
        # Setup
        input_data = pd.DataFrame({
            'id': [1, 2, 3],
            'input': ['Text 1', 'Text 2', 'Text 3'],
            'output': ['Output 1', 'Output 2', 'Output 3']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService(preserve_order=False)
        
        # Execute
        result = extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['output', 'input']
        )
        
        # Verify - order might be different (original DataFrame order)
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        assert set(output_df.columns) == {'input', 'output'}
    
    def test_extract_columns_missing_column_error(self, temp_dir: Path):
        """Test error handling for missing columns."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService(handle_missing='error')
        
        # Execute - request non-existent column
        with pytest.raises(ValidationError):
            extractor.extract_columns(
                input_file=input_file,
                output_file=output_file,
                columns=['input', 'nonexistent']
            )
    
    def test_extract_columns_missing_column_skip(self, temp_dir: Path):
        """Test skipping missing columns."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService(handle_missing='skip')
        
        # Execute - request non-existent column
        result = extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'nonexistent', 'output']
        )
        
        # Verify - should skip missing column
        assert result['success'] is True
        assert result['extracted_columns'] == ['input', 'output']
        assert 'skipped_columns' in result
        assert result['skipped_columns'] == ['nonexistent']
        
        output_df = pd.read_csv(output_file)
        assert list(output_df.columns) == ['input', 'output']
    
    def test_extract_columns_missing_column_fill(self, temp_dir: Path):
        """Test filling missing columns with default values."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService(handle_missing='fill')
        
        # Execute - request non-existent column
        result = extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'nonexistent', 'output'],
            fill_value='N/A'
        )
        
        # Verify - should fill missing column
        assert result['success'] is True
        assert result['extracted_columns'] == ['input', 'nonexistent', 'output']
        
        output_df = pd.read_csv(output_file)
        assert list(output_df.columns) == ['input', 'nonexistent', 'output']
        assert output_df['nonexistent'].tolist() == ['N/A', 'N/A']
    
    def test_extract_columns_with_backup(self, temp_dir: Path):
        """Test column extraction with backup creation."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2'],
            'extra': ['Extra 1', 'Extra 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService()
        
        # Execute
        result = extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'output'],
            create_backup=True
        )
        
        # Verify
        assert result['success'] is True
        assert 'backup_file' in result
        
        backup_file = Path(result['backup_file'])
        assert backup_file.exists()
        assert backup_file.name.startswith('input_backup_')
    
    def test_extract_batch(self, temp_dir: Path):
        """Test batch extraction from multiple files."""
        # Setup multiple input files
        files = []
        for i in range(3):
            data = pd.DataFrame({
                'input': [f'Text {i}_1', f'Text {i}_2'],
                'output': [f'Output {i}_1', f'Output {i}_2'],
                'extra': [f'Extra {i}_1', f'Extra {i}_2']
            })
            input_file = temp_dir / f"input_{i}.csv"
            output_file = temp_dir / f"output_{i}.csv"
            data.to_csv(input_file, index=False)
            files.append((input_file, output_file, ['input', 'output']))
        
        extractor = ExtractorService()
        
        # Execute
        results = extractor.extract_batch(files)
        
        # Verify
        assert len(results) == 3
        for result in results:
            assert result['success'] is True
            assert result['extracted_rows'] == 2
            assert result['extracted_columns'] == ['input', 'output']
        
        # Check all output files exist
        for _, output_file, _ in files:
            assert output_file.exists()
    
    def test_get_available_columns(self, temp_dir: Path):
        """Test getting available columns from a file."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2'],
            'id': [1, 2],
            'metadata': ['Meta 1', 'Meta 2']
        })
        input_file = temp_dir / "input.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService()
        
        # Execute
        columns = extractor.get_available_columns(input_file)
        
        # Verify
        assert set(columns) == {'input', 'output', 'id', 'metadata'}
    
    def test_get_statistics(self, temp_dir: Path):
        """Test getting processing statistics."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2'],
            'extra': ['Extra 1', 'Extra 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        extractor = ExtractorService()
        
        # Execute extraction
        extractor.extract_columns(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'output']
        )
        
        # Get statistics
        stats = extractor.get_statistics()
        
        # Verify
        assert 'total_files_processed' in stats
        assert 'total_rows_extracted' in stats
        assert 'total_columns_extracted' in stats
        assert 'success_rate' in stats
        assert stats['total_files_processed'] == 1
        assert stats['total_rows_extracted'] == 2
        assert stats['success_rate'] == 100.0


class TestExtractorConvenienceFunctions:
    """Tests for extractor convenience functions."""
    
    def test_extract_columns_from_csv(self, temp_dir: Path):
        """Test extract_columns_from_csv convenience function."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2'],
            'extra': ['Extra 1', 'Extra 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        # Execute
        result = extract_columns_from_csv(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'output']
        )
        
        # Verify
        assert result['success'] is True
        assert result['extracted_rows'] == 2
        assert result['extracted_columns'] == ['input', 'output']
        assert output_file.exists()
    
    def test_extract_columns_from_csv_with_options(self, temp_dir: Path):
        """Test convenience function with custom options."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'output': ['Output 1', 'Output 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        # Execute
        result = extract_columns_from_csv(
            input_file=input_file,
            output_file=output_file,
            columns=['input', 'nonexistent', 'output'],
            handle_missing='skip'
        )
        
        # Verify
        assert result['success'] is True
        assert result['extracted_columns'] == ['input', 'output']
        assert 'skipped_columns' in result