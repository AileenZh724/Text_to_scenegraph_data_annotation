"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
import pandas as pd
import json

# Add src to path for imports
import sys
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from text2sg.core.models import GenerationConfig, SceneGraph, AnnotatedRow
from text2sg.config.settings import Settings, LoggingSettings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_csv_data() -> pd.DataFrame:
    """Create sample CSV data for testing."""
    return pd.DataFrame({
        'input': [
            'A red car is parked next to a blue house.',
            'The cat is sitting on the table.',
            'A person is walking in the park with a dog.'
        ],
        'id': [1, 2, 3],
        'category': ['vehicle', 'animal', 'person']
    })


@pytest.fixture
def sample_csv_file(temp_dir: Path, sample_csv_data: pd.DataFrame) -> Path:
    """Create a sample CSV file for testing."""
    csv_file = temp_dir / "sample.csv"
    sample_csv_data.to_csv(csv_file, index=False)
    return csv_file


@pytest.fixture
def sample_scene_graph() -> SceneGraph:
    """Create a sample scene graph for testing."""
    return SceneGraph(
        objects=[
            {'id': 1, 'name': 'car', 'attributes': ['red']},
            {'id': 2, 'name': 'house', 'attributes': ['blue']}
        ],
        relationships=[
            {'subject': 1, 'predicate': 'parked_next_to', 'object': 2}
        ]
    )


@pytest.fixture
def sample_annotated_row(sample_scene_graph: SceneGraph) -> AnnotatedRow:
    """Create a sample annotated row for testing."""
    return AnnotatedRow(
        input="A red car is parked next to a blue house.",
        output="Please annotate this text to generate a scene graph.",
        scene_graph=sample_scene_graph
    )


@pytest.fixture
def sample_generation_config() -> GenerationConfig:
    """Create a sample generation config for testing."""
    return GenerationConfig(
        api_key="test_api_key",
        model="gemini-pro",
        max_retries=2,
        timeout=10,
        batch_size=5
    )


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults."""
    return Settings(
        debug=True,
        logging=LoggingSettings(
            level="DEBUG",
            console_enabled=False,  # Disable console logging in tests
            rich_enabled=False,
            file_path=None
        )
    )


@pytest.fixture
def multiline_json_csv_content() -> str:
    """Create CSV content with multiline JSON for testing."""
    return '''input,output
"A red car","{
  ""objects"": [
    {""id"": 1, ""name"": ""car""}
  ]
}"
"A blue house","{""objects"": [{""id"": 2, ""name"": ""house""}]}"
'''


@pytest.fixture
def multiline_json_csv_file(temp_dir: Path, multiline_json_csv_content: str) -> Path:
    """Create a CSV file with multiline JSON for testing."""
    csv_file = temp_dir / "multiline.csv"
    csv_file.write_text(multiline_json_csv_content, encoding='utf-8')
    return csv_file


@pytest.fixture
def mock_api_response() -> Dict[str, Any]:
    """Create a mock API response for testing."""
    return {
        'candidates': [{
            'content': {
                'parts': [{
                    'text': json.dumps({
                        'objects': [
                            {'id': 1, 'name': 'car', 'attributes': ['red']}
                        ],
                        'relationships': []
                    })
                }]
            }
        }]
    }


@pytest.fixture
def sample_config_file(temp_dir: Path) -> Path:
    """Create a sample configuration file for testing."""
    config_data = {
        'app_name': 'Test2SG',
        'debug': True,
        'api': {
            'gemini_api_key': 'test_key',
            'max_retries': 2
        },
        'processing': {
            'batch_size': 5
        }
    }
    
    config_file = temp_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return config_file


class MockProvider:
    """Mock provider for testing."""
    
    def __init__(self, config: GenerationConfig, should_fail: bool = False):
        self.config = config
        self.should_fail = should_fail
        self.call_count = 0
    
    def generate_scene_graph(self, text: str) -> SceneGraph:
        """Mock scene graph generation."""
        self.call_count += 1
        
        if self.should_fail:
            raise Exception("Mock provider failure")
        
        return SceneGraph(
            objects=[{'id': 1, 'name': 'test_object', 'attributes': []}],
            relationships=[]
        )
    
    def generate_batch(self, texts: list) -> list:
        """Mock batch generation."""
        return [self.generate_scene_graph(text) for text in texts]


@pytest.fixture
def mock_provider(sample_generation_config: GenerationConfig) -> MockProvider:
    """Create a mock provider for testing."""
    return MockProvider(sample_generation_config)


@pytest.fixture
def failing_mock_provider(sample_generation_config: GenerationConfig) -> MockProvider:
    """Create a mock provider that fails for testing error handling."""
    return MockProvider(sample_generation_config, should_fail=True)


# Test utilities
def assert_csv_files_equal(file1: Path, file2: Path, ignore_index: bool = True):
    """Assert that two CSV files have the same content."""
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    if ignore_index:
        df1 = df1.reset_index(drop=True)
        df2 = df2.reset_index(drop=True)
    
    pd.testing.assert_frame_equal(df1, df2)


def create_test_csv(file_path: Path, data: Dict[str, list]):
    """Create a test CSV file with given data."""
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_file(file_path: Path, data: Dict[str, Any]):
    """Write data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)