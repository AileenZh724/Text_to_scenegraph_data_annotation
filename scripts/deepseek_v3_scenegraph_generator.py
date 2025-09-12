#!/usr/bin/env python3
"""
DeepSeek R1 Scene Graph Generator

This script uses DeepSeek's R1 API to generate scene graphs from text descriptions.
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


class DeepSeekSceneGraphGenerator:
    """Scene Graph Generator using DeepSeek R1 API"""
    
    def __init__(self, api_key: str):
        """
        Initialize the generator with API key
        
        Args:
            api_key (str): DeepSeek API key
        """
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
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
        
        log_filename = os.path.join(logs_dir, f"deepseek_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
            json_output = json.dumps(example['output'], indent=2)
            escaped_json = json_output.replace('{', '{{').replace('}', '}}')
            prompt += f"Output:\n{escaped_json}\n\n"
        
        prompt += "Now generate Scene Graph JSON array for the following input:\n"
        prompt += "Input: \"{text}\"\n"
        prompt += "Output (JSON array only, no additional text):"
        
        return prompt
    
    def generate_scene_graph(self, text: str, max_retries: int = 16) -> Optional[str]:
        """
        Generate scene graph using DeepSeek R1 API with exponential backoff retry mechanism
        
        Args:
            text (str): Input text description
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Optional[str]: Generated scene graph JSON string or None if failed
        """
        prompt = self.prompt_template.format(text=text)
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": False
        }
        
        base_wait_time = 2  # Initial wait time in seconds
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt} for text: {text[:100]}...")
                else:
                    self.logger.info(f"Calling DeepSeek API for text: {text[:100]}...")
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 429:
                    if attempt < max_retries:
                        wait_time = base_wait_time * (2 ** attempt)
                        self.logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry (attempt {attempt + 1}/{max_retries + 1})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        self.logger.error(f"API request failed after {max_retries + 1} attempts: {response.status_code} {response.reason}")
                        return None
                
                response.raise_for_status()
                
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    generated_text = result['choices'][0]['message']['content']
                    self.logger.info(f"Generated text: {generated_text[:200]}...")
                    
                    # Directly return the generated text without parsing
                    if generated_text and generated_text.strip():
                        self.logger.info("Successfully received response from API")
                        return generated_text.strip()
                    else:
                        self.logger.error("Empty response from API")
                        return None
                else:
                    self.logger.error("No choices in API response")
                    return None
                    
            except requests.RequestException as e:
                if ("429" in str(e) or "Too Many Requests" in str(e)) and attempt < max_retries:
                    wait_time = base_wait_time * (2 ** attempt)
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
    
    # JSON parsing and validation methods removed - now using direct API response
    
    def process_csv_file(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """Process CSV file and generate scene graphs with incremental saving"""
        if output_file is None:
            output_file = input_file
        
        try:
            if output_file != input_file and os.path.exists(output_file):
                backup_file = f"{output_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(output_file, backup_file)
                self.logger.info(f"Created backup: {backup_file}")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
            
            if not fieldnames:
                self.logger.error("No fieldnames found in CSV")
                return False
            
            if 'scenegraph' not in fieldnames:
                fieldnames.append('scenegraph')
            
            self.logger.info(f"Processing {len(rows)} rows from {input_file}")
            
            consecutive_failures = 0
            base_delay = 3
            
            for i, row in enumerate(rows):
                if row.get('scenegraph') and row['scenegraph'].strip():
                    self.logger.info(f"Row {i+1}: Scene graph already exists, skipping")
                    continue
                
                text = row.get('input', '').strip()
                if not text:
                    self.logger.warning(f"Row {i+1}: No input text found, skipping")
                    continue
                
                self.logger.info(f"Processing row {i+1}/{len(rows)}: {text[:100]}...")
                
                scene_graph = self.generate_scene_graph(text)
                
                if scene_graph:
                    row['scenegraph'] = scene_graph
                    self.logger.info(f"Row {i+1}: Successfully generated scene graph")
                    consecutive_failures = 0
                else:
                    row['scenegraph'] = ''
                    self.logger.error(f"Row {i+1}: Failed to generate scene graph")
                    consecutive_failures += 1
                
                try:
                    with open(output_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    self.logger.info(f"Row {i+1}: Saved to {output_file}")
                except Exception as save_error:
                    self.logger.error(f"Row {i+1}: Failed to save to file: {save_error}")
                
                if consecutive_failures > 0:
                    delay = base_delay + (consecutive_failures * 2)
                    delay = min(delay, 15)
                    self.logger.info(f"Consecutive failures: {consecutive_failures}, waiting {delay} seconds...")
                    time.sleep(delay)
                else:
                    time.sleep(base_delay)
            
            self.logger.info(f"Processing completed. Results saved to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test the API connection"""
        test_payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, this is a test message."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 10
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_payload,
                timeout=30
            )
            response.raise_for_status()
            self.logger.info("API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            return False


def main():
    """Main function to run the scene graph generator"""
    load_dotenv()
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("Error: DEEPSEEK_API_KEY not found in environment variables")
        print("Please set your DeepSeek API key in the .env file")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python deepseek_v3_scenegraph_generator.py <input_csv_file> [output_csv_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    generator = DeepSeekSceneGraphGenerator(api_key)
    
    print("Testing API connection...")
    if not generator.test_connection():
        print("API connection test failed. Please check your API key and network connection.")
        sys.exit(1)
    
    print("API connection successful. Starting processing...")
    
    success = generator.process_csv_file(input_file, output_file)
    
    if success:
        print("Processing completed successfully!")
    else:
        print("Processing failed. Check the logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()