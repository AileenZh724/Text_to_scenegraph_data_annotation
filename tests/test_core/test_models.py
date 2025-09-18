"""Tests for core models."""

import pytest
import json
from pydantic import ValidationError

from text2sg.core.models import (
    SceneGraph, AnnotatedRow, GenerationConfig,
    SceneGraphObject, SceneGraphRelationship
)


class TestSceneGraphObject:
    """Tests for SceneGraphObject model."""
    
    def test_create_valid_object(self):
        """Test creating a valid scene graph object."""
        obj = SceneGraphObject(
            id=1,
            name="car",
            attributes=["red", "fast"]
        )
        
        assert obj.id == 1
        assert obj.name == "car"
        assert obj.attributes == ["red", "fast"]
    
    def test_create_object_without_attributes(self):
        """Test creating object without attributes."""
        obj = SceneGraphObject(id=1, name="car")
        
        assert obj.id == 1
        assert obj.name == "car"
        assert obj.attributes == []
    
    def test_invalid_object_id(self):
        """Test validation of object ID."""
        with pytest.raises(ValidationError):
            SceneGraphObject(id=-1, name="car")
    
    def test_empty_object_name(self):
        """Test validation of empty object name."""
        with pytest.raises(ValidationError):
            SceneGraphObject(id=1, name="")


class TestSceneGraphRelationship:
    """Tests for SceneGraphRelationship model."""
    
    def test_create_valid_relationship(self):
        """Test creating a valid relationship."""
        rel = SceneGraphRelationship(
            subject=1,
            predicate="next_to",
            object=2
        )
        
        assert rel.subject == 1
        assert rel.predicate == "next_to"
        assert rel.object == 2
    
    def test_invalid_relationship_ids(self):
        """Test validation of relationship IDs."""
        with pytest.raises(ValidationError):
            SceneGraphRelationship(subject=-1, predicate="next_to", object=2)
        
        with pytest.raises(ValidationError):
            SceneGraphRelationship(subject=1, predicate="next_to", object=-1)
    
    def test_empty_predicate(self):
        """Test validation of empty predicate."""
        with pytest.raises(ValidationError):
            SceneGraphRelationship(subject=1, predicate="", object=2)


class TestSceneGraph:
    """Tests for SceneGraph model."""
    
    def test_create_empty_scene_graph(self):
        """Test creating an empty scene graph."""
        sg = SceneGraph()
        
        assert sg.objects == []
        assert sg.relationships == []
    
    def test_create_scene_graph_with_data(self):
        """Test creating scene graph with objects and relationships."""
        objects = [
            SceneGraphObject(id=1, name="car", attributes=["red"]),
            SceneGraphObject(id=2, name="house", attributes=["blue"])
        ]
        relationships = [
            SceneGraphRelationship(subject=1, predicate="parked_next_to", object=2)
        ]
        
        sg = SceneGraph(objects=objects, relationships=relationships)
        
        assert len(sg.objects) == 2
        assert len(sg.relationships) == 1
        assert sg.objects[0].name == "car"
        assert sg.relationships[0].predicate == "parked_next_to"
    
    def test_scene_graph_from_dict(self):
        """Test creating scene graph from dictionary."""
        data = {
            "objects": [
                {"id": 1, "name": "car", "attributes": ["red"]},
                {"id": 2, "name": "house", "attributes": ["blue"]}
            ],
            "relationships": [
                {"subject": 1, "predicate": "parked_next_to", "object": 2}
            ]
        }
        
        sg = SceneGraph(**data)
        
        assert len(sg.objects) == 2
        assert len(sg.relationships) == 1
        assert sg.objects[0].name == "car"
    
    def test_scene_graph_to_dict(self):
        """Test converting scene graph to dictionary."""
        sg = SceneGraph(
            objects=[SceneGraphObject(id=1, name="car", attributes=["red"])],
            relationships=[SceneGraphRelationship(subject=1, predicate="is", object=1)]
        )
        
        data = sg.dict()
        
        assert "objects" in data
        assert "relationships" in data
        assert len(data["objects"]) == 1
        assert data["objects"][0]["name"] == "car"
    
    def test_scene_graph_json_serialization(self):
        """Test JSON serialization of scene graph."""
        sg = SceneGraph(
            objects=[SceneGraphObject(id=1, name="car", attributes=["red"])],
            relationships=[]
        )
        
        json_str = sg.json()
        parsed = json.loads(json_str)
        
        assert "objects" in parsed
        assert "relationships" in parsed
        assert len(parsed["objects"]) == 1
    
    def test_get_object_by_id(self):
        """Test getting object by ID."""
        objects = [
            SceneGraphObject(id=1, name="car"),
            SceneGraphObject(id=2, name="house")
        ]
        sg = SceneGraph(objects=objects)
        
        obj = sg.get_object_by_id(1)
        assert obj is not None
        assert obj.name == "car"
        
        obj = sg.get_object_by_id(999)
        assert obj is None
    
    def test_get_relationships_for_object(self):
        """Test getting relationships for an object."""
        relationships = [
            SceneGraphRelationship(subject=1, predicate="next_to", object=2),
            SceneGraphRelationship(subject=2, predicate="contains", object=3),
            SceneGraphRelationship(subject=1, predicate="is", object=1)
        ]
        sg = SceneGraph(relationships=relationships)
        
        # As subject
        rels = sg.get_relationships_for_object(1, as_subject=True)
        assert len(rels) == 2
        
        # As object
        rels = sg.get_relationships_for_object(2, as_object=True)
        assert len(rels) == 1
        
        # Both
        rels = sg.get_relationships_for_object(1)
        assert len(rels) == 3


class TestAnnotatedRow:
    """Tests for AnnotatedRow model."""
    
    def test_create_annotated_row(self):
        """Test creating an annotated row."""
        scene_graph = SceneGraph(
            objects=[SceneGraphObject(id=1, name="car")]
        )
        
        row = AnnotatedRow(
            input="A red car",
            output="Annotate this text",
            scene_graph=scene_graph
        )
        
        assert row.input == "A red car"
        assert row.output == "Annotate this text"
        assert len(row.scene_graph.objects) == 1
    
    def test_annotated_row_without_scene_graph(self):
        """Test creating annotated row without scene graph."""
        row = AnnotatedRow(
            input="A red car",
            output="Annotate this text"
        )
        
        assert row.input == "A red car"
        assert row.output == "Annotate this text"
        assert row.scene_graph is None
    
    def test_annotated_row_to_dict(self):
        """Test converting annotated row to dictionary."""
        scene_graph = SceneGraph(
            objects=[SceneGraphObject(id=1, name="car")]
        )
        
        row = AnnotatedRow(
            input="A red car",
            output="Annotate this text",
            scene_graph=scene_graph
        )
        
        data = row.dict()
        
        assert "input" in data
        assert "output" in data
        assert "scene_graph" in data
        assert data["scene_graph"]["objects"][0]["name"] == "car"
    
    def test_annotated_row_csv_format(self):
        """Test converting annotated row to CSV format."""
        scene_graph = SceneGraph(
            objects=[SceneGraphObject(id=1, name="car")]
        )
        
        row = AnnotatedRow(
            input="A red car",
            output="Annotate this text",
            scene_graph=scene_graph
        )
        
        csv_data = row.to_csv_row()
        
        assert "input" in csv_data
        assert "output" in csv_data
        assert "scene_graph" in csv_data
        assert isinstance(csv_data["scene_graph"], str)  # Should be JSON string


class TestGenerationConfig:
    """Tests for GenerationConfig model."""
    
    def test_create_basic_config(self):
        """Test creating basic generation config."""
        config = GenerationConfig(api_key="test_key")
        
        assert config.api_key == "test_key"
        assert config.model == "gemini-pro"  # Default value
        assert config.max_retries == 3  # Default value
    
    def test_create_full_config(self):
        """Test creating full generation config."""
        config = GenerationConfig(
            api_key="test_key",
            model="gemini-pro-vision",
            max_retries=5,
            timeout=60,
            batch_size=20,
            temperature=0.7
        )
        
        assert config.api_key == "test_key"
        assert config.model == "gemini-pro-vision"
        assert config.max_retries == 5
        assert config.timeout == 60
        assert config.batch_size == 20
        assert config.temperature == 0.7
    
    def test_config_validation(self):
        """Test validation of config parameters."""
        # Invalid max_retries
        with pytest.raises(ValidationError):
            GenerationConfig(api_key="test", max_retries=-1)
        
        # Invalid timeout
        with pytest.raises(ValidationError):
            GenerationConfig(api_key="test", timeout=0)
        
        # Invalid batch_size
        with pytest.raises(ValidationError):
            GenerationConfig(api_key="test", batch_size=0)
        
        # Invalid temperature
        with pytest.raises(ValidationError):
            GenerationConfig(api_key="test", temperature=2.0)
    
    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = GenerationConfig(
            api_key="test_key",
            model="gemini-pro",
            max_retries=3
        )
        
        data = config.dict()
        
        assert "api_key" in data
        assert "model" in data
        assert "max_retries" in data
        assert data["api_key"] == "test_key"
    
    def test_config_exclude_api_key(self):
        """Test excluding API key from serialization."""
        config = GenerationConfig(api_key="secret_key")
        
        data = config.dict(exclude={"api_key"})
        
        assert "api_key" not in data
        assert "model" in data