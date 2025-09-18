"""DeepSeek provider for scene graph generation."""

import requests
import json
import time
from typing import Dict, Any, Optional, List

from .base import BaseGenerator
from ..models import SceneGraph, Node, Edge, GenerationResult


class DeepseekProvider(BaseGenerator):
    """DeepSeek provider for scene graph generation using DeepSeek R1 API."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration
        self.api_key = self.config.get('api_key')
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        
        self.api_url = self.config.get('api_url', 'https://api.deepseek.com/chat/completions')
        self.model = self.config.get('model', 'deepseek-chat')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', 2048)
        self.top_p = self.config.get('top_p', 0.95)
        self.timeout = self.config.get('timeout', 60)
        
        # Headers
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Few-shot examples
        self.few_shot_examples = self._build_few_shot_examples()
        self.prompt_template = self._build_prompt_template()
    
    def _build_few_shot_examples(self) -> List[Dict[str, Any]]:
        """Build few-shot learning examples.
        
        Returns:
            List of example input-output pairs
        """
        examples = [
            {
                "input": "A young boy in a red shirt waves at a brown dog in a sunny park. The dog runs toward the boy wagging its tail, and the boy kneels down to pet it.",
                "output": [
                    {
                        "time": "T1",
                        "nodes": [
                            {"id": "boy", "attributes": ["young", "red_shirt"]},
                            {"id": "dog", "attributes": ["brown"]},
                            {"id": "park", "attributes": ["sunny"]}
                        ],
                        "edges": [["boy", "in", "park"], ["dog", "in", "park"], ["boy", "waves_at", "dog"]]
                    },
                    {
                        "time": "T2",
                        "nodes": [
                            {"id": "boy", "attributes": ["young", "red_shirt"]},
                            {"id": "dog", "attributes": ["brown", "running", "wagging_tail"]},
                            {"id": "park", "attributes": ["sunny"]}
                        ],
                        "edges": [["boy", "in", "park"], ["dog", "in", "park"], ["dog", "runs_toward", "boy"]]
                    },
                    {
                        "time": "T3",
                        "nodes": [
                            {"id": "boy", "attributes": ["young", "red_shirt", "kneeling"]},
                            {"id": "dog", "attributes": ["brown"]},
                            {"id": "park", "attributes": ["sunny"]}
                        ],
                        "edges": [["boy", "in", "park"], ["dog", "in", "park"], ["boy", "pets", "dog"]]
                    }
                ]
            }
        ]
        return examples
    
    def _build_prompt_template(self) -> str:
        """Build the prompt template with few-shot examples.
        
        Returns:
            Formatted prompt template string
        """
        prompt = """Generate Scene Graph JSON array for multiple time phases. Analyze the input text and identify different time phases, then generate a JSON array with scene graphs for each time phase.

Each scene graph should have:
- "time": Time phase identifier (T1, T2, T3, etc.)
- "nodes": Array of objects with "id" and "attributes" (array of strings)
- "edges": Array of relationships [subject, predicate, object]

Here are some examples:

"""
        
        # Add few-shot examples
        for i, example in enumerate(self.few_shot_examples, 1):
            prompt += f"Example {i}:\n"
            prompt += f"Input: \"{example['input']}\"\n"
            json_output = json.dumps(example['output'], indent=2)
            escaped_json = json_output.replace('{', '{{').replace('}', '}}')
            prompt += f"Output:\n{escaped_json}\n\n"
        
        prompt += "Now generate Scene Graph JSON array for the following input:\n"
        prompt += "Input: \"{text}\"\n"
        prompt += "Output (JSON array only, no additional text):"
        
        return prompt
    
    def generate(self, text: str, **kwargs) -> GenerationResult:
        """Generate scene graph using DeepSeek API.
        
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
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": kwargs.get('temperature', self.temperature),
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "top_p": kwargs.get('top_p', self.top_p),
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "stream": False
            }
            
            self.logger.info(f"Generating scene graph with DeepSeek model: {self.model}")
            
            # Make request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="Rate limit exceeded. Please try again later.",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            response.raise_for_status()
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="No choices returned from API",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            generated_text = result['choices'][0]['message']['content']
            
            if not generated_text or not generated_text.strip():
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="Empty response from API",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            self.logger.debug(f"Generated text: {generated_text[:200]}...")
            
            # Parse JSON response
            scene_data = self._parse_json_response(generated_text)
            if not scene_data:
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="Failed to parse JSON from API response",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            # Convert to SceneGraph (use first scene for now)
            if not scene_data:
                return GenerationResult(
                    success=False,
                    scenegraph=None,
                    error="No valid scenes found in response",
                    provider=self.name,
                    input_text=text,
                    generation_time=time.time() - start_time
                )
            
            first_scene = scene_data[0]
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
    
    def _parse_json_response(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """Parse JSON response from API.
        
        Args:
            response_text: Raw response text from API
            
        Returns:
            Parsed scene data or None if parsing fails
        """
        try:
            # Try to parse as direct JSON
            parsed = json.loads(response_text.strip())
            
            # Validate structure
            if isinstance(parsed, list):
                # Check if all items are valid scene objects
                if all(isinstance(item, dict) and 
                      'time' in item and 
                      'nodes' in item and 
                      'edges' in item 
                      for item in parsed):
                    return parsed
            elif isinstance(parsed, dict) and \
                 'time' in parsed and \
                 'nodes' in parsed and \
                 'edges' in parsed:
                return [parsed]
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from text (similar to Ollama approach)
        import re
        json_patterns = [
            r'```json\s*(\[.*?\])\s*```',
            r'```\s*(\[.*?\])\s*```',
            r'(\[\s*{.*?}\s*\])',
            r'({.*?"time".*?"edges".*?})',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    parsed = json.loads(match.strip())
                    if isinstance(parsed, list):
                        if all(isinstance(item, dict) and 
                              'time' in item and 
                              'nodes' in item and 
                              'edges' in item 
                              for item in parsed):
                            return parsed
                    elif isinstance(parsed, dict) and \
                         'time' in parsed and \
                         'nodes' in parsed and \
                         'edges' in parsed:
                        return [parsed]
                except json.JSONDecodeError:
                    continue
        
        self.logger.warning("Failed to parse JSON from API response")
        return None
    
    def _convert_to_scenegraph(self, scene_data: Dict[str, Any]) -> SceneGraph:
        """Convert scene data to SceneGraph object.
        
        Args:
            scene_data: Raw scene data from API
            
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
        """Validate DeepSeek configuration.
        
        Returns:
            True if configuration is valid
        """
        if not self.api_key:
            return False
        
        # Test API connection
        return self.test_connection()
    
    def test_connection(self) -> bool:
        """Test connection to DeepSeek API.
        
        Returns:
            True if connection is successful
        """
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get DeepSeek provider information.
        
        Returns:
            Provider information dictionary
        """
        info = super().get_provider_info()
        info.update({
            'api_url': self.api_url,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'has_api_key': bool(self.api_key)
        })
        return info

    def generate_with_colors(self, text: str, **kwargs) -> str:
        """Enrich text description with color information using DeepSeek API.
        
        Args:
            text: Input text description without color information
            **kwargs: Additional parameters
            
        Returns:
            Text description enriched with color information
        """
        try:
            # Prepare color enrichment prompt
            prompt = """Analyze the following text description and enrich it with color information for objects where colors are not mentioned. Use basic colors (red, blue, green, yellow, black, white, brown, gray, orange, purple, pink) and maintain the original meaning of the text.

Example input: "A cat sits on a chair watching birds through the window."
Example output: "A gray cat sits on a brown chair watching colorful birds through the clear window."

Input: "{text}"
Output (enriched text only, no additional text):""" 
            
            prompt = prompt.format(text=text)
            
            # Prepare payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 1024),
                "top_p": kwargs.get('top_p', 0.95),
                "stream": False
            }
            
            # Make request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                raise ValueError("No choices returned from API")
            
            enriched_text = result['choices'][0]['message']['content'].strip()
            
            if not enriched_text:
                raise ValueError("Empty response from API")
            
            # Remove any quotes or formatting
            enriched_text = enriched_text.strip('"').strip()
            
            return enriched_text
            
        except Exception as e:
            self.logger.error(f"Color enrichment failed: {e}")
            return text  # Return original text on failure