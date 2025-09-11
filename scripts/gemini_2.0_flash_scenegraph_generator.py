#!/usr/bin/env python3
"""
Gemini 2.0 Flash Scene Graph Generator

This script uses Google's Gemini 2.0 Flash API to generate scene graphs from text descriptions.
It processes input data from CSV files and saves the generated scene graphs back to the CSV.
"""

import requests
import json
import csv
import sys
import os
import re
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv


class GeminiSceneGraphGenerator:
    """Scene Graph Generator using Gemini 2.0 Flash API"""
    
    def __init__(self, api_key: str):
        """
        Initialize the generator with API key
        
        Args:
            api_key (str): Google AI API key for Gemini
        """
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # Setup logging
        self._setup_logging()
        
        # Few-shot learning examples from the provided samples
        self.few_shot_examples = self._build_few_shot_examples()
        
        # Build the prompt template with few-shot examples
        self.prompt_template = self._build_prompt_template()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Ensure logs directory exists
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        log_filename = os.path.join(logs_dir, f"gemini_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _build_few_shot_examples(self) -> List[Dict[str, Any]]:
        """Build few-shot learning examples from the sample data"""
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
            },
            {
                "input": "A fluffy white cat sits on a windowsill watching the rain. Suddenly, the cat jumps down and walks toward a bowl of milk.",
                "output": [
                    {
                        "time": "T1",
                        "nodes": [
                            {"id": "cat", "attributes": ["fluffy", "white", "sitting"]},
                            {"id": "windowsill", "attributes": []},
                            {"id": "rain", "attributes": []}
                        ],
                        "edges": [["cat", "sits_on", "windowsill"], ["cat", "watches", "rain"]]
                    },
                    {
                        "time": "T2",
                        "nodes": [
                            {"id": "cat", "attributes": ["fluffy", "white", "jumping"]},
                            {"id": "windowsill", "attributes": []},
                            {"id": "bowl", "attributes": ["of_milk"]}
                        ],
                        "edges": [["cat", "jumps_down_from", "windowsill"], ["cat", "walks_toward", "bowl"]]
                    },
                    {
                        "time": "T3",
                        "nodes": [
                            {"id": "cat", "attributes": ["fluffy", "white", "walking"]},
                            {"id": "bowl", "attributes": ["of_milk"]}
                        ],
                        "edges": [["cat", "walks_toward", "milk"]]
                    }
                ]
            },
            {
                "input": "A girl pedals her blue bicycle down a quiet street. She slows near a mailbox and ties her shoelace. After fastening the lace, she hops back on and continues down the street with a small grin.",
                "output": [
                    {
                        "time": "T1",
                        "nodes": [
                            {"id": "girl", "attributes": ["pedaling"]},
                            {"id": "bicycle", "attributes": ["blue"]},
                            {"id": "street", "attributes": ["quiet"]}
                        ],
                        "edges": [["girl", "pedals", "bicycle"], ["girl", "on", "street"], ["bicycle", "on", "street"]]
                    },
                    {
                        "time": "T2",
                        "nodes": [
                            {"id": "girl", "attributes": ["slowing", "tying_shoelace"]},
                            {"id": "bicycle", "attributes": ["blue"]},
                            {"id": "mailbox", "attributes": []},
                            {"id": "shoelace", "attributes": []}
                        ],
                        "edges": [["girl", "near", "mailbox"], ["girl", "ties", "shoelace"], ["bicycle", "on", "street"]]
                    },
                    {
                        "time": "T3",
                        "nodes": [
                            {"id": "girl", "attributes": ["pedaling", "small_grin"]},
                            {"id": "bicycle", "attributes": ["blue"]},
                            {"id": "street", "attributes": ["quiet"]},
                            {"id": "shoelace", "attributes": ["fastened"]}
                        ],
                        "edges": [["girl", "pedals", "bicycle"], ["girl", "on", "street"]]
                    }
                ]
            },
            {
                "input": "A girl with a yellow kite stands on a windy hill. She lets go and the kite soars above the trees. She runs down the hill chasing the kite.",
                "output": [
                    {
                        "time": "T1",
                        "nodes": [
                            {"id": "girl", "attributes": []},
                            {"id": "kite", "attributes": ["yellow"]},
                            {"id": "hill", "attributes": ["windy"]}
                        ],
                        "edges": [["girl", "with", "kite"], ["girl", "stands_on", "hill"]]
                    },
                    {
                        "time": "T2",
                        "nodes": [
                            {"id": "girl", "attributes": []},
                            {"id": "kite", "attributes": ["yellow", "soaring"]},
                            {"id": "trees", "attributes": []}
                        ],
                        "edges": [["girl", "lets_go_of", "kite"], ["kite", "soars_above", "trees"]]
                    },
                    {
                        "time": "T3",
                        "nodes": [
                            {"id": "girl", "attributes": ["running"]},
                            {"id": "kite", "attributes": ["yellow"]},
                            {"id": "hill", "attributes": ["windy"]}
                        ],
                        "edges": [["girl", "runs_down", "hill"], ["girl", "chases", "kite"]]
                    }
                ]
            },
            {
                "input": "A woman in a blue apron opens the small kitchen window. A black cat perched on the windowsill watches steam rising from a whistling kettle. She sets a small cup on the wooden table. The cat leaps down to sniff the cup.",
                "output": [
                    {
                        "time": "T1",
                        "nodes": [
                            {"id": "woman", "attributes": ["blue_apron"]},
                            {"id": "window", "attributes": []},
                            {"id": "kitchen", "attributes": ["small"]}
                        ],
                        "edges": [["woman", "opens", "window"], ["window", "in", "kitchen"]]
                    },
                    {
                        "time": "T2",
                        "nodes": [
                            {"id": "cat", "attributes": ["black", "perched"]},
                            {"id": "windowsill", "attributes": []},
                            {"id": "steam", "attributes": ["rising"]},
                            {"id": "kettle", "attributes": ["whistling"]}
                        ],
                        "edges": [["cat", "on", "windowsill"], ["cat", "watches", "steam"], ["steam", "from", "kettle"]]
                    },
                    {
                        "time": "T3",
                        "nodes": [
                            {"id": "woman", "attributes": ["blue_apron"]},
                            {"id": "cup", "attributes": ["small"]},
                            {"id": "table", "attributes": ["wooden"]}
                        ],
                        "edges": [["woman", "sets", "cup"], ["cup", "on", "table"]]
                    },
                    {
                        "time": "T4",
                        "nodes": [
                            {"id": "cat", "attributes": ["black", "leaping"]},
                            {"id": "cup", "attributes": ["small"]}
                        ],
                        "edges": [["cat", "leaps_down_to", "cup"], ["cat", "sniffs", "cup"]]
                    }
                ]
            }
        ]
        return examples
    
    def _build_prompt_template(self) -> str:
        """Build the prompt template with few-shot examples"""
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
            # Escape curly braces in JSON output to avoid format string conflicts
            json_output = json.dumps(example['output'], indent=2)
            escaped_json = json_output.replace('{', '{{').replace('}', '}}')
            prompt += f"Output:\n{escaped_json}\n\n"
        
        prompt += "Now generate Scene Graph JSON array for the following input:\n"
        prompt += "Input: \"{text}\"\n"
        prompt += "Output (JSON array only, no additional text):"
        
        return prompt
    
    def generate_scene_graph(self, text: str, max_retries: int = 16) -> Optional[List[Dict[str, Any]]]:
        """
        Generate scene graph using Gemini 2.0 Flash API with exponential backoff retry mechanism
        
        Args:
            text (str): Input text description
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Optional[List[Dict[str, Any]]]: Generated scene graph or None if failed
        """
        prompt = self.prompt_template.format(text=text)
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2048
            }
        }
        
        base_wait_time = 2  # Initial wait time in seconds
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt} for text: {text[:100]}...")
                else:
                    self.logger.info(f"Calling Gemini API for text: {text[:100]}...")
                
                response = requests.post(
                    f"{self.api_url}?key={self.api_key}",
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 429:
                    if attempt < max_retries:
                        # Exponential backoff: 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536 seconds
                        wait_time = base_wait_time * (2 ** attempt)
                        # No cap on maximum wait time, allow exponential growth beyond 256 seconds
                        self.logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry (attempt {attempt + 1}/{max_retries + 1})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"API request failed after {max_retries + 1} attempts: {response.status_code} {response.reason}")
                        return None
                
                response.raise_for_status()
                
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    generated_text = result['candidates'][0]['content']['parts'][0]['text']
                    self.logger.info(f"Generated text: {generated_text[:200]}...")
                    
                    # Extract and parse JSON
                    scene_graph = self._extract_and_parse_json(generated_text)
                    if scene_graph:
                        self.logger.info(f"Successfully generated scene graph with {len(scene_graph)} time phases")
                        return scene_graph
                    else:
                        self.logger.error("Failed to extract valid JSON from generated text")
                        return None
                else:
                    self.logger.error("No candidates in API response")
                    return None
                    
            except requests.RequestException as e:
                if ("429" in str(e) or "Too Many Requests" in str(e)) and attempt < max_retries:
                    # Rate limit hit, exponential backoff
                    wait_time = base_wait_time * (2 ** attempt)
                    # No cap on maximum wait time, allow exponential growth beyond 256 seconds
                    self.logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry (attempt {attempt + 1}/{max_retries + 1})...")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"API request failed after {attempt + 1} attempts: {e}")
                    return None
            except Exception as e:
                self.logger.error(f"Scene graph generation failed: {e}")
                return None
        
        return None
    
    def _extract_and_parse_json(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Extract and parse JSON from the generated text
        
        Args:
            text (str): Generated text containing JSON
            
        Returns:
            Optional[List[Dict[str, Any]]]: Parsed scene graph or None if failed
        """
        # Try multiple JSON extraction patterns
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # JSON in code blocks
            r'```\s*([\s\S]*?)\s*```',      # Generic code blocks
            r'(\[[\s\S]*?\])',              # JSON arrays
            r'({[\s\S]*?})',                # JSON objects
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    cleaned_match = match.strip()
                    parsed = json.loads(cleaned_match)
                    
                    # Validate the structure
                    if isinstance(parsed, list):
                        if all(self._validate_scene_graph_item(item) for item in parsed):
                            return parsed
                    elif isinstance(parsed, dict) and self._validate_scene_graph_item(parsed):
                        return [parsed]  # Wrap single object in array
                        
                except json.JSONDecodeError:
                    continue
        
        # If no valid JSON found, try to extract from the entire text
        try:
            # Remove any markdown formatting
            cleaned_text = re.sub(r'```[a-zA-Z]*\n?', '', text)
            cleaned_text = cleaned_text.strip()
            
            parsed = json.loads(cleaned_text)
            if isinstance(parsed, list):
                if all(self._validate_scene_graph_item(item) for item in parsed):
                    return parsed
            elif isinstance(parsed, dict) and self._validate_scene_graph_item(parsed):
                return [parsed]
        except json.JSONDecodeError:
            pass
        
        self.logger.error("Could not extract valid JSON from generated text")
        return None
    
    def _validate_scene_graph_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate a single scene graph item
        
        Args:
            item (Dict[str, Any]): Scene graph item to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['time', 'nodes', 'edges']
        if not all(field in item for field in required_fields):
            return False
        
        # Validate nodes structure
        if not isinstance(item['nodes'], list):
            return False
        for node in item['nodes']:
            if not isinstance(node, dict) or 'id' not in node or 'attributes' not in node:
                return False
            if not isinstance(node['attributes'], list):
                return False
        
        # Validate edges structure
        if not isinstance(item['edges'], list):
            return False
        for edge in item['edges']:
            if not isinstance(edge, list) or len(edge) != 3:
                return False
        
        return True
    
    def process_csv_file(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """
        Process CSV file and generate scene graphs for all input texts with incremental saving
        
        Args:
            input_file (str): Path to input CSV file
            output_file (Optional[str]): Path to output CSV file (defaults to input_file)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if output_file is None:
            output_file = input_file
        
        try:
            # Read the CSV file
            with open(input_file, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.logger.info(f"Processing {len(rows)} rows from {input_file}")
            
            # Create backup of original file if output is different from input
            if output_file != input_file and os.path.exists(output_file):
                backup_file = f"{output_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(output_file, backup_file)
                self.logger.info(f"Existing output file backed up to {backup_file}")
            
            # Process each row
            processed_count = 0
            failed_count = 0
            consecutive_failures = 0
            base_delay = 3  # Increased base delay to 3 seconds
            
            for i, row in enumerate(rows):
                if 'input' not in row:
                    self.logger.error(f"Row {i+1}: Missing 'input' column")
                    failed_count += 1
                    continue
                
                input_text = row['input'].strip()
                if not input_text:
                    self.logger.warning(f"Row {i+1}: Empty input text")
                    row['scenegraph'] = ''
                    continue
                
                # Skip if scenegraph already exists and is not empty
                if row.get('scenegraph') and row['scenegraph'].strip():
                    self.logger.info(f"Row {i+1}: Scene graph already exists, skipping")
                    continue
                
                self.logger.info(f"Processing row {i+1}/{len(rows)}: {input_text[:50]}...")
                
                # Generate scene graph
                scene_graph = self.generate_scene_graph(input_text)
                
                if scene_graph:
                    # Convert to JSON string for CSV storage
                    row['scenegraph'] = json.dumps(scene_graph, ensure_ascii=False)
                    processed_count += 1
                    consecutive_failures = 0  # Reset failure counter on success
                    self.logger.info(f"Row {i+1}: Successfully generated scene graph")
                else:
                    row['scenegraph'] = ''
                    failed_count += 1
                    consecutive_failures += 1
                    self.logger.error(f"Row {i+1}: Failed to generate scene graph")
                
                # Incremental save after each row processing
                try:
                    with open(output_file, 'w', encoding='utf-8', newline='') as f:
                        if rows:
                            writer = csv.DictWriter(f, fieldnames=rows[0].keys(), quoting=csv.QUOTE_ALL)
                            writer.writeheader()
                            writer.writerows(rows)
                    self.logger.info(f"Row {i+1}: Progress saved to {output_file}")
                except Exception as save_error:
                    self.logger.error(f"Row {i+1}: Failed to save progress: {save_error}")
                
                # Dynamic delay between requests based on failure rate
                if i < len(rows) - 1:  # Don't delay after the last row
                    if consecutive_failures > 0:
                        # Increase delay after consecutive failures
                        dynamic_delay = base_delay + (consecutive_failures * 2)  # 3, 5, 7, 9... seconds
                        dynamic_delay = min(dynamic_delay, 15)  # Cap at 15 seconds
                        self.logger.info(f"Adding extended delay of {dynamic_delay} seconds due to {consecutive_failures} consecutive failures")
                        time.sleep(dynamic_delay)
                    else:
                        time.sleep(base_delay)
            
            self.logger.info(f"Processing complete. Processed: {processed_count}, Failed: {failed_count}")
            self.logger.info(f"Final results saved to: {output_file}")
            
            return failed_count == 0
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {e}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test the API connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        test_payload = {
            "contents": [{
                "parts": [{
                    "text": "Hello, this is a test."
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": 10
            }
        }
        
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=self.headers,
                json=test_payload,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False


def main():
    """Main function"""
    import argparse
    
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description='Generate scene graphs using Gemini 2.0 Flash API')
    parser.add_argument('--api-key', help='Google AI API key (can also be set via GEMINI_API_KEY environment variable)')
    parser.add_argument('--input-file', required=True, help='Input CSV file path')
    parser.add_argument('--output-file', help='Output CSV file path (defaults to input file)')
    parser.add_argument('--test-connection', action='store_true', help='Test API connection only')
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    
    # Validate API key
    if not api_key or len(api_key.strip()) < 10:
        print("Error: Invalid or missing API key.")
        print("Please provide API key via:")
        print("  1. --api-key argument")
        print("  2. GEMINI_API_KEY environment variable")
        print("  3. Create a .env file with GEMINI_API_KEY=your_api_key")
        sys.exit(1)
    
    # Initialize generator
    generator = GeminiSceneGraphGenerator(api_key)
    
    if args.test_connection:
        print("Testing API connection...")
        if generator.test_connection():
            print("✓ API connection successful!")
        else:
            print("✗ API connection failed!")
            sys.exit(1)
        return
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
    
    # Process CSV file
    print(f"Processing CSV file: {args.input_file}")
    success = generator.process_csv_file(args.input_file, args.output_file)
    
    if success:
        output_path = args.output_file or args.input_file
        print(f"✓ Processing completed successfully! Results saved to: {output_path}")
    else:
        print("✗ Processing completed with errors. Check the log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()