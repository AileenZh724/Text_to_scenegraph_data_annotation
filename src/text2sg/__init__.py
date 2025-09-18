"""Text to Scene Graph Generator

A unified CLI tool for generating scene graphs from text descriptions.
Supports multiple AI providers including Ollama, DeepSeek, and Gemini.
"""

__version__ = "0.1.0"
__author__ = "Data Annotator Team"
__email__ = "team@example.com"

from .models import SceneGraph, Node, Edge, AnnotatedRow

__all__ = [
    "SceneGraph",
    "Node", 
    "Edge",
    "AnnotatedRow",
    "__version__",
    "__author__",
    "__email__"
]