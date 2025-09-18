"""Pydantic data models for scene graph generation."""

from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json


SCHEMA_VERSION = "1.0.0"


class Node(BaseModel):
    """Represents a node in the scene graph."""
    
    id: str = Field(..., description="Unique identifier for the node")
    attributes: List[str] = Field(default_factory=list, description="List of node attributes")
    
    class Config:
        json_encoders = {
            list: lambda v: v if v else []
        }


class Edge(BaseModel):
    """Represents an edge in the scene graph."""
    
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relation: str = Field(..., description="Relationship type between nodes")
    
    @validator('source', 'target')
    def validate_node_ids(cls, v):
        if not v or not v.strip():
            raise ValueError("Node IDs cannot be empty")
        return v.strip()
    
    @validator('relation')
    def validate_relation(cls, v):
        if not v or not v.strip():
            raise ValueError("Relation cannot be empty")
        return v.strip()


class SceneGraph(BaseModel):
    """Represents a complete scene graph."""
    
    time: Optional[str] = Field(None, description="Timestamp or time reference")
    nodes: List[Node] = Field(default_factory=list, description="List of nodes in the graph")
    edges: List[Edge] = Field(default_factory=list, description="List of edges in the graph")
    schema_version: str = Field(default=SCHEMA_VERSION, description="Schema version for compatibility")
    
    @validator('nodes')
    def validate_nodes(cls, v):
        if not v:
            return v
        
        # Check for duplicate node IDs
        node_ids = [node.id for node in v]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Duplicate node IDs found")
        
        return v
    
    @validator('edges')
    def validate_edges(cls, v, values):
        if not v or 'nodes' not in values:
            return v
        
        # Get valid node IDs
        valid_node_ids = {node.id for node in values['nodes']}
        
        # Validate edge references
        for edge in v:
            if edge.source not in valid_node_ids:
                raise ValueError(f"Edge source '{edge.source}' not found in nodes")
            if edge.target not in valid_node_ids:
                raise ValueError(f"Edge target '{edge.target}' not found in nodes")
        
        return v
    
    def to_json_str(self, **kwargs) -> str:
        """Convert to JSON string with proper formatting."""
        return self.json(ensure_ascii=False, **kwargs)
    
    @classmethod
    def from_json_str(cls, json_str: str) -> 'SceneGraph':
        """Create SceneGraph from JSON string."""
        try:
            data = json.loads(json_str)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse SceneGraph: {e}")


class AnnotatedRow(BaseModel):
    """Represents a row in the annotated dataset."""
    
    id: str = Field(..., description="Unique identifier for the row")
    input: str = Field(..., description="Input text description")
    scenegraph: Optional[SceneGraph] = Field(None, description="Generated scene graph")
    is_reasonable: Optional[bool] = Field(None, description="Whether the scene graph is reasonable")
    is_annotated: bool = Field(default=False, description="Whether the row has been annotated")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('input')
    def validate_input(cls, v):
        if not v or not v.strip():
            raise ValueError("Input text cannot be empty")
        return v.strip()
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not v.strip():
            raise ValueError("ID cannot be empty")
        return v.strip()
    
    def mark_annotated(self, is_reasonable: bool = True):
        """Mark the row as annotated."""
        self.is_annotated = True
        self.is_reasonable = is_reasonable
        self.updated_at = datetime.now()
    
    def to_csv_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for CSV export."""
        return {
            'id': self.id,
            'input': self.input,
            'scenegraph': self.scenegraph.to_json_str() if self.scenegraph else '',
            'is_reasonable': self.is_reasonable,
            'is_annotated': self.is_annotated
        }
    
    @classmethod
    def from_csv_dict(cls, data: Dict[str, Any]) -> 'AnnotatedRow':
        """Create AnnotatedRow from CSV dictionary."""
        # Parse scenegraph if present
        scenegraph = None
        if data.get('scenegraph') and data['scenegraph'].strip():
            try:
                scenegraph = SceneGraph.from_json_str(data['scenegraph'])
            except Exception:
                # If parsing fails, leave as None
                pass
        
        # Convert string booleans
        is_reasonable = None
        if data.get('is_reasonable') is not None:
            if isinstance(data['is_reasonable'], str):
                is_reasonable = data['is_reasonable'].lower() in ('true', '1', 'yes')
            else:
                is_reasonable = bool(data['is_reasonable'])
        
        is_annotated = False
        if data.get('is_annotated') is not None:
            if isinstance(data['is_annotated'], str):
                is_annotated = data['is_annotated'].lower() in ('true', '1', 'yes')
            else:
                is_annotated = bool(data['is_annotated'])
        
        return cls(
            id=str(data['id']),
            input=str(data['input']),
            scenegraph=scenegraph,
            is_reasonable=is_reasonable,
            is_annotated=is_annotated
        )


class GenerationResult(BaseModel):
    """Result of a scene graph generation operation."""
    
    success: bool = Field(..., description="Whether generation was successful")
    scenegraph: Optional[SceneGraph] = Field(None, description="Generated scene graph")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    provider: str = Field(..., description="Provider used for generation")
    input_text: str = Field(..., description="Original input text")
    generation_time: float = Field(..., description="Time taken for generation in seconds")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    
    @validator('generation_time')
    def validate_generation_time(cls, v):
        if v < 0:
            raise ValueError("Generation time cannot be negative")
        return v


class BatchGenerationStats(BaseModel):
    """Statistics for batch generation operations."""
    
    total_rows: int = Field(..., description="Total number of rows processed")
    successful: int = Field(default=0, description="Number of successful generations")
    failed: int = Field(default=0, description="Number of failed generations")
    skipped: int = Field(default=0, description="Number of skipped rows")
    total_time: float = Field(default=0.0, description="Total processing time in seconds")
    average_time: float = Field(default=0.0, description="Average time per row in seconds")
    provider: str = Field(..., description="Provider used for generation")
    
    def update_stats(self, result: GenerationResult, skipped: bool = False):
        """Update statistics with a new result."""
        if skipped:
            self.skipped += 1
        elif result.success:
            self.successful += 1
        else:
            self.failed += 1
        
        self.total_time += result.generation_time
        
        # Update average time
        processed = self.successful + self.failed
        if processed > 0:
            self.average_time = self.total_time / processed
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        processed = self.successful + self.failed
        if processed == 0:
            return 0.0
        return (self.successful / processed) * 100
    
    def summary(self) -> str:
        """Generate a summary string of the statistics."""
        return (
            f"Batch Generation Summary:\n"
            f"  Provider: {self.provider}\n"
            f"  Total Rows: {self.total_rows}\n"
            f"  Successful: {self.successful}\n"
            f"  Failed: {self.failed}\n"
            f"  Skipped: {self.skipped}\n"
            f"  Success Rate: {self.success_rate:.1f}%\n"
            f"  Total Time: {self.total_time:.2f}s\n"
            f"  Average Time: {self.average_time:.2f}s per row"
        )