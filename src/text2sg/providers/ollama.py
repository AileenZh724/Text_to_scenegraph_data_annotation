"""Ollama provider for scene graph generation."""

import requests
import json
import re
import time
from typing import Dict, Any, Optional, List

from .base import BaseGenerator
from ..models import SceneGraph, Node, Edge, GenerationResult


class OllamaProvider(BaseGenerator):
    """Ollama provider for local scene graph generation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Default configuration
        self.ollama_url = self.config.get('ollama_url', 'http://localhost:11434')
        self.model = self.config.get('model', 'qwen3:0.6b')
        self.temperature = self.config.get('temperature', 0.2)
        self.num_predict = self.config.get('num_predict', 1024)
        self.timeout = self.config.get('timeout', 60)
        
        # Prompt template
        self.prompt_template = """Generate Scene Graph JSON file for multiple time phases. Analyze the input text and identify different time phases, then generate a JSON array with scene graphs for each time phase.

Example for single time phase:
{{input："A young boy in a red shirt waves at a brown dog in a sunny park.",
output:
[
{{
 "time": "T1",
 "nodes": [
 {{"id": "boy", "attributes": ["young", "red_shirt", "standing"]}},
 {{"id": "dog", "attributes": ["brown", "standing"]}},
 {{"id": "park", "attributes": ["sunny", "green_grass"]}}
 ],
 "edges": [
 ["boy", "in", "park"],
 ["dog", "in", "park"],
 ["boy", "waves_at", "dog"]
 ]
}}
]
}}

Example for multiple time phases:
{{input："A cat sits on a windowsill. Then it jumps down. Finally it walks to a milk bowl.",
output:
[
{{
 "time": "T1",
 "nodes": [
 {{"id": "cat", "attributes": ["sitting"]}},
 {{"id": "windowsill", "attributes": []}}
 ],
 "edges": [
 ["cat", "sits_on", "windowsill"]
 ]
}},
{{
 "time": "T2", 
 "nodes": [
 {{"id": "cat", "attributes": ["jumping"]}},
 {{"id": "windowsill", "attributes": []}}
 ],
 "edges": [
 ["cat", "jumps_from", "windowsill"]
 ]
}},
{{
 "time": "T3",
 "nodes": [
 {{"id": "cat", "attributes": ["walking"]}},
 {{"id": "milk_bowl", "attributes": ["milk"]}}
 ],
 "edges": [
 ["cat", "walks_to", "milk_bowl"]
 ]
}}
]
}}

Now generate Scene Graph JSON array for:
input: "{text}"
output:"""
    
    def generate(self, text: str, **kwargs) -> GenerationResult:
        """Generate scene graph using Ollama.
        
        Args:
            text: Input text description
            **kwargs: Additional parameters
            
        Returns:
            GenerationResult
        """
        start_time = time.time()
        
        try:
            # Prepare prompt
            prompt = self.prompt_template.format(text=text)
            
            # Prepare payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.temperature),
                    "num_predict": kwargs.get('num_predict', self.num_predict)
                }
            }
            
            self.logger.info(f"Generating scene graph with model: {self.model}")
            
            # Make request
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            self.logger.debug(f"Model output: {generated_text[:200]}...")
            
            # Extract and parse JSON
            scene_data = self._extract_json(generated_text)
            if not scene_data:
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="Failed to extract valid JSON from model output",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            # Convert to SceneGraph objects
            scenes = scene_data.get('scenes', [])
            if not scenes:
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="No valid scenes found in generated output",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            # For now, return the first scene as SceneGraph
            # TODO: Handle multiple time phases properly
            first_scene = scenes[0]
            scenegraph = self._convert_to_scenegraph(first_scene)
            
            return GenerationResult(
                success=True,
                scenegraph=scenegraph,
                error=None,
                provider=self.name,
                input_text=text,
                generation_time=time.time() - start_time
            )
            
        except requests.RequestException as e:
            return GenerationResult(
                success=False,
                scenegraph=None,
                error=f"Request failed: {str(e)}",
                provider=self.name,
                input_text=text,
                generation_time=time.time() - start_time
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                scenegraph=None,
                error=f"Generation failed: {str(e)}",
                provider=self.name,
                input_text=text,
                generation_time=time.time() - start_time
            )
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from model output text.
        
        Args:
            text: Raw model output text
            
        Returns:
            Extracted JSON data or None if extraction fails
        """
        # JSON extraction patterns (from original script)
        json_patterns = [
            # Match JSON arrays in code blocks
            r'```json\s*(\[[^`]*\])\s*```',
            r'```\s*(\[[^`]*\])\s*```',
            # Match JSON objects in code blocks
            r'```json\s*({[^`]*})\s*```',
            r'```\s*({[^`]*})\s*```',
            # Match JSON arrays after output:
            r'output:\s*(\[[\s\S]*?\])(?=\n\n|\n[a-zA-Z]|$)',
            # Match JSON objects after output:
            r'output:\s*({[\s\S]*?})(?=\n\n|\n[a-zA-Z]|$)',
            # Match JSON arrays containing "time"
            r'(\[\s*{[\s\S]*?"time"[\s\S]*?"edges"[\s\S]*?\]\s*\])',
            # Match JSON objects containing "time"
            r'({\s*"time"[\s\S]*?"edges"[\s\S]*?\]\s*})',
            # Match complete JSON arrays with time, nodes, edges
            r'(\[[\s\S]*?"time"[\s\S]*?"nodes"[\s\S]*?"edges"[\s\S]*?\])',
            # Match complete JSON objects with time, nodes, edges
            r'({[\s\S]*?"time"[\s\S]*?"nodes"[\s\S]*?"edges"[\s\S]*?})',
            # Last resort: any JSON array
            r'(\[[\s\S]*?\])',
            # Last resort: any JSON object
            r'({[\s\S]*?})'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    # Clean up the match
                    cleaned_match = match.strip()
                    parsed = json.loads(cleaned_match)
                    
                    # Validate structure
                    if isinstance(parsed, list):
                        # Check if all items are valid scene objects
                        if all(isinstance(item, dict) and 
                              'time' in item and 
                              'nodes' in item and 
                              'edges' in item 
                              for item in parsed):
                            return {"scenes": parsed}
                    elif isinstance(parsed, dict) and \
                         'time' in parsed and \
                         'nodes' in parsed and \
                         'edges' in parsed:
                        return {"scenes": [parsed]}
                        
                except json.JSONDecodeError:
                    continue
        
        self.logger.warning("Failed to extract valid JSON from model output")
        return None
    
    def _convert_to_scenegraph(self, scene_data: Dict[str, Any]) -> SceneGraph:
        """Convert scene data to SceneGraph object.
        
        Args:
            scene_data: Raw scene data from model
            
        Returns:
            SceneGraph object
        """
        # Convert nodes
        nodes = []
        for node_data in scene_data.get('nodes', []):
            node = Node(
                id=node_data['id'],
                attributes=node_data.get('attributes', [])
            )
            nodes.append(node)
        
        # Convert edges
        edges = []
        for edge_data in scene_data.get('edges', []):
            if isinstance(edge_data, list) and len(edge_data) >= 3:
                edge = Edge(
                    source=edge_data[0],
                    target=edge_data[2],
                    relation=edge_data[1]
                )
                edges.append(edge)
        
        return SceneGraph(
            time=scene_data.get('time'),
            nodes=nodes,
            edges=edges
        )
    
    def _validate_config(self) -> bool:
        """Validate Ollama configuration.
        
        Returns:
            True if configuration is valid
        """
        try:
            # Test connection to Ollama
            response = requests.get(
                f"{self.ollama_url}/api/tags", 
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def test_connection(self) -> bool:
        """Test connection to Ollama service.
        
        Returns:
            True if connection is successful
        """
        return self._validate_config()
    
    def list_models(self) -> List[str]:
        """List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.ollama_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            return models
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get Ollama provider information.
        
        Returns:
            Provider information dictionary
        """
        info = super().get_provider_info()
        info.update({
            'ollama_url': self.ollama_url,
            'model': self.model,
            'available_models': self.list_models() if self._validate_config() else [],
            'temperature': self.temperature,
            'timeout': self.timeout
        })
        return info

    def generate_with_colors(self, text: str, **kwargs) -> Dict[str, Any]:
        """Generate color information for text using Ollama.
        
        Args:
            text: Input text description
            **kwargs: Additional parameters
            
        Returns:
            Dict containing color information and enriched text
        """
        start_time = time.time()
        
        try:
            # Prepare prompt for color generation
            prompt = """Analyze the text and identify colors for objects and scenes. For each object mentioned, 
            suggest appropriate colors based on context and common sense. If a color is already mentioned, 
            use that color. Format the response as a JSON object with 'colors' array containing color 
            assignments and 'enriched_text' with the text including color information.

            Example input: "A boy waves at a dog in the park"
            Example output: {
                "colors": [
                    {"object": "boy", "color": "blue", "context": "wearing casual clothes"},
                    {"object": "dog", "color": "brown", "context": "common dog color"},
                    {"object": "park", "color": "green", "context": "grass and trees"}
                ],
                "enriched_text": "A boy in a blue shirt waves at a brown dog in the green park"
            }

            Now analyze this text: "{text}"""

            # Prepare payload
            payload = {
                "model": self.model,
                "prompt": prompt.format(text=text),
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', self.temperature),
                    "num_predict": kwargs.get('num_predict', self.num_predict)
                }
            }
            
            # Make request
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            # Extract JSON from response
            try:
                # Try to parse the entire response as JSON first
                color_data = json.loads(generated_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON using regex
                json_match = re.search(r'\{[\s\S]*\}', generated_text)
                if json_match:
                    try:
                        color_data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        return {
                            "success": False,
                            "error": "Failed to parse color information from model output",
                            "generation_time": time.time() - start_time
                        }
                else:
                    return {
                        "success": False,
                        "error": "No valid JSON found in model output",
                        "generation_time": time.time() - start_time
                    }
            
            # Validate response structure
            if not isinstance(color_data, dict) or \
               'colors' not in color_data or \
               'enriched_text' not in color_data:
                return {
                    "success": False,
                    "error": "Invalid response structure from model",
                    "generation_time": time.time() - start_time
                }
            
            return {
                "success": True,
                "colors": color_data['colors'],
                "enriched_text": color_data['enriched_text'],
                "generation_time": time.time() - start_time
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}",
                "generation_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Generation failed: {str(e)}",
                "generation_time": time.time() - start_time
            }