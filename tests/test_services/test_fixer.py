"""Tests for FixerService."""

import pytest
import pandas as pd
from pathlib import Path
import json

from text2sg.services.fixer import FixerService, fix_multiline_json_in_csv
from text2sg.core.exceptions import FileProcessingError, ValidationError


class TestFixerService:
    """Tests for FixerService class."""
    
    def test_init_default(self):
        """Test FixerService initialization with defaults."""
        fixer = FixerService()
        
        assert fixer.default_column == "output"
        assert fixer.fix_strategy == "auto"
        assert fixer.preserve_original is True
        assert fixer.validate_json is True
    
    def test_init_custom(self):
        """Test FixerService initialization with custom values."""
        fixer = FixerService(
            default_column="annotation",
            fix_strategy="merge_lines",
            preserve_original=False,
            validate_json=False
        )
        
        assert fixer.default_column == "annotation"
        assert fixer.fix_strategy == "merge_lines"
        assert fixer.preserve_original is False
        assert fixer.validate_json is False
    
    def test_fix_multiline_json_basic(self, temp_dir: Path):
        """Test basic multiline JSON fixing."""
        # Setup - CSV with multiline JSON
        input_data = pd.DataFrame({
            'input': ['A red car', 'A blue house'],
            'output': [
                '{\n  "objects": ["car"],\n  "attributes": ["red"]\n}',
                '{\n  "objects": ["house"],\n  "attributes": ["blue"]\n}'
            ]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService()
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 2
        assert result['fixed_rows'] == 2
        assert output_file.exists()
        
        # Check output content
        output_df = pd.read_csv(output_file)
        assert len(output_df) == 2
        
        # Verify JSON is now single-line and valid
        for output_text in output_df['output']:
            assert '\n' not in output_text  # No newlines
            json.loads(output_text)  # Should be valid JSON
    
    def test_fix_multiline_json_custom_column(self, temp_dir: Path):
        """Test fixing multiline JSON in custom column."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['A red car'],
            'annotation': ['{\n  "objects": ["car"]\n}'],
            'id': [1]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService()
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file,
            column="annotation"
        )
        
        # Verify
        assert result['success'] is True
        assert result['fixed_rows'] == 1
        
        output_df = pd.read_csv(output_file)
        assert 'annotation' in output_df.columns
        assert '\n' not in output_df['annotation'].iloc[0]
    
    def test_fix_multiline_json_preserve_original(self, temp_dir: Path):
        """Test fixing with original column preservation."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['A red car'],
            'output': ['{\n  "objects": ["car"]\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService(preserve_original=True)
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        assert 'output' in output_df.columns
        assert 'output_original' in output_df.columns
        
        # Original should have newlines, fixed should not
        assert '\n' in output_df['output_original'].iloc[0]
        assert '\n' not in output_df['output'].iloc[0]
    
    def test_fix_multiline_json_no_preserve_original(self, temp_dir: Path):
        """Test fixing without preserving original."""
        # Setup
        input_data = pd.DataFrame({
            'input': ['A red car'],
            'output': ['{\n  "objects": ["car"]\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService(preserve_original=False)
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        
        output_df = pd.read_csv(output_file)
        assert 'output' in output_df.columns
        assert 'output_original' not in output_df.columns
    
    def test_fix_multiline_json_merge_lines_strategy(self, temp_dir: Path):
        """Test merge_lines fixing strategy."""
        # Setup
        input_data = pd.DataFrame({
            'output': ['{\n  "objects": ["car"],\n  "color": "red"\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService(fix_strategy="merge_lines")
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['strategy_used'] == "merge_lines"
        
        output_df = pd.read_csv(output_file)
        fixed_json = output_df['output'].iloc[0]
        assert '\n' not in fixed_json
        json.loads(fixed_json)  # Should be valid JSON
    
    def test_fix_multiline_json_compact_strategy(self, temp_dir: Path):
        """Test compact fixing strategy."""
        # Setup
        input_data = pd.DataFrame({
            'output': ['{\n  "objects": ["car"],\n  "color": "red"\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService(fix_strategy="compact")
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['strategy_used'] == "compact"
        
        output_df = pd.read_csv(output_file)
        fixed_json = output_df['output'].iloc[0]
        assert '\n' not in fixed_json
        assert ' ' not in fixed_json or fixed_json.count(' ') < 5  # More compact
    
    def test_fix_multiline_json_with_validation(self, temp_dir: Path):
        """Test fixing with JSON validation enabled."""
        # Setup - include invalid JSON
        input_data = pd.DataFrame({
            'output': [
                '{\n  "objects": ["car"]\n}',  # Valid
                '{\n  "objects": ["house"\n}',  # Invalid - missing closing bracket
                '{\n  "objects": ["bike"]\n}'   # Valid
            ]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService(validate_json=True)
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['processed_rows'] == 3
        assert result['fixed_rows'] == 2  # Only valid JSON fixed
        assert result['validation_errors'] == 1
        
        output_df = pd.read_csv(output_file)
        assert len(output_df) == 3
        
        # Check that valid JSON was fixed, invalid remains unchanged
        assert '\n' not in output_df['output'].iloc[0]  # Fixed
        assert '\n' in output_df['output'].iloc[1]     # Unchanged (invalid)
        assert '\n' not in output_df['output'].iloc[2]  # Fixed
    
    def test_fix_multiline_json_no_validation(self, temp_dir: Path):
        """Test fixing without JSON validation."""
        # Setup - include invalid JSON
        input_data = pd.DataFrame({
            'output': [
                '{\n  "objects": ["car"]\n}',
                '{\n  "objects": ["house"\n}'  # Invalid JSON
            ]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService(validate_json=False)
        
        # Execute
        result = fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify - should fix all rows regardless of validity
        assert result['success'] is True
        assert result['processed_rows'] == 2
        assert result['fixed_rows'] == 2
        assert 'validation_errors' not in result
        
        output_df = pd.read_csv(output_file)
        for output_text in output_df['output']:
            assert '\n' not in output_text  # All should be fixed
    
    def test_fix_multiline_json_with_backup(self, temp_dir: Path):
        """Test fixing with backup creation."""
        # Setup
        input_data = pd.DataFrame({
            'output': ['{\n  "objects": ["car"]\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService()
        
        # Execute
        result = fixer.fix_multiline_json(
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
    
    def test_fix_batch(self, temp_dir: Path):
        """Test batch fixing of multiple files."""
        # Setup multiple input files
        files = []
        for i in range(3):
            data = pd.DataFrame({
                'output': [f'{{\n  "text": "sample {i}"\n}}']
            })
            input_file = temp_dir / f"input_{i}.csv"
            output_file = temp_dir / f"output_{i}.csv"
            data.to_csv(input_file, index=False)
            files.append((input_file, output_file))
        
        fixer = FixerService()
        
        # Execute
        results = fixer.fix_batch(files)
        
        # Verify
        assert len(results) == 3
        for result in results:
            assert result['success'] is True
            assert result['fixed_rows'] == 1
        
        # Check all output files exist
        for _, output_file in files:
            assert output_file.exists()
    
    def test_get_statistics(self, temp_dir: Path):
        """Test getting processing statistics."""
        # Setup
        input_data = pd.DataFrame({
            'output': [
                '{\n  "objects": ["car"]\n}',
                '{\n  "objects": ["house"]\n}'
            ]
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService()
        
        # Execute fixing
        fixer.fix_multiline_json(
            input_file=input_file,
            output_file=output_file
        )
        
        # Get statistics
        stats = fixer.get_statistics()
        
        # Verify
        assert 'total_files_processed' in stats
        assert 'total_rows_processed' in stats
        assert 'total_rows_fixed' in stats
        assert 'success_rate' in stats
        assert 'fix_rate' in stats
        assert stats['total_files_processed'] == 1
        assert stats['total_rows_processed'] == 2
        assert stats['total_rows_fixed'] == 2
        assert stats['success_rate'] == 100.0
        assert stats['fix_rate'] == 100.0
    
    def test_missing_input_file(self, temp_dir: Path):
        """Test error handling for missing input file."""
        input_file = temp_dir / "nonexistent.csv"
        output_file = temp_dir / "output.csv"
        
        fixer = FixerService()
        
        with pytest.raises(FileProcessingError):
            fixer.fix_multiline_json(input_file=input_file, output_file=output_file)
    
    def test_missing_column(self, temp_dir: Path):
        """Test error handling for missing column."""
        # Setup - CSV without 'output' column
        input_data = pd.DataFrame({
            'input': ['Text 1', 'Text 2'],
            'annotation': ['Ann 1', 'Ann 2']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        fixer = FixerService()
        
        with pytest.raises(ValidationError):
            fixer.fix_multiline_json(input_file=input_file, output_file=output_file)


class TestFixerConvenienceFunctions:
    """Tests for fixer convenience functions."""
    
    def test_fix_multiline_json_in_csv(self, temp_dir: Path):
        """Test fix_multiline_json_in_csv convenience function."""
        # Setup
        input_data = pd.DataFrame({
            'output': ['{\n  "objects": ["car"]\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        # Execute
        result = fix_multiline_json_in_csv(
            input_file=input_file,
            output_file=output_file
        )
        
        # Verify
        assert result['success'] is True
        assert result['fixed_rows'] == 1
        assert output_file.exists()
    
    def test_fix_multiline_json_in_csv_with_options(self, temp_dir: Path):
        """Test convenience function with custom options."""
        # Setup
        input_data = pd.DataFrame({
            'annotation': ['{\n  "objects": ["car"]\n}']
        })
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "output.csv"
        input_data.to_csv(input_file, index=False)
        
        # Execute
        result = fix_multiline_json_in_csv(
            input_file=input_file,
            output_file=output_file,
            column="annotation",
            fix_strategy="compact",
            preserve_original=False
        )
        
        # Verify
        assert result['success'] is True
        assert result['strategy_used'] == "compact"
        
        output_df = pd.read_csv(output_file)
        assert 'annotation' in output_df.columns
        assert 'annotation_original' not in output_df.columns