import time
"""
scenegraph_from_text.py

Functionality:
- Read natural language text from a CSV file (one per row)
- For each text, call an LLM (e.g., OpenAI GPT/DeepSeek) to complete subject-verb-object structure, supplement commonsense (e.g., color), and standardize attributes
- Output a time-ordered scene graph in JSON format (scene graph with temporal annotation)

Dependencies:
- openai
- pandas

Usage:
python scenegraph_from_text.py --input text.csv --output output.json --enriched-output enriched.txt --deepseek-key sk-d8e737492d8d468f8a30ea344c9cef26
"""
import argparse
import json
import pandas as pd
import openai
import re
from typing import List, Dict, Any

BASIC_COLORS = ["red", "blue", "green", "yellow", "black", "white", "brown", "gray", "orange", "purple", "pink"]

def standardize_color(text: str) -> str:
    text = text.lower()
    for color in BASIC_COLORS:
        if color in text:
            return color
    return "gray"  # Default guess is gray

def call_llm(text: str, deepseek_key: str) -> Dict[str, Any]:
    """
    Call DeepSeek to complete SVO, supplement commonsense, standardize attributes, and return scene graph structure
    """
    openai.api_key = deepseek_key
    openai.base_url = "https://api.deepseek.com"
    prompt = f"""
You are a scene graph generation assistant. For the following natural language text:
1. Enrich the content by supplementing missing information (such as color, size, etc.) using commonsense, and rewrite the text in natural language with all entities described in detail. Assign a basic color to every entity, even if not mentioned, using commonsense or random assignment if necessary.
2. Then, generate a JSON scene graph with temporal annotation as before.
Return your output in the following format:
---
Enriched Text:
<your enriched natural language text here>
---
Scenegraph:
[{{"time": "T1", "nodes": [{{"id": "kitchen", "attributes": ["dimly_lit", "gray"]}}, ...], "edges": [["cutting_board", "sits_atop", "counter"], ...]}}]
---
Text: {text}
"""
    response = openai.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )
    # extract enriched text and scenegraph
    content = response.choices[0].message.content
    match_enriched = re.search(r'---\s*Enriched Text:\s*(.*?)\s*---', content, re.DOTALL)
    match_scenegraph = re.search(r'---\s*Scenegraph:\s*(\[\s*{.*}\s*\])', content, re.DOTALL)
    if match_enriched and match_scenegraph:
        enriched_text = match_enriched.group(1).strip()
        scenegraph = json.loads(match_scenegraph.group(1))
        return enriched_text, scenegraph
    else:
        raise ValueError("LLM does not return both enriched text and effective JSON")

def main():
    parser = argparse.ArgumentParser(description="Generate scene graph JSON and enriched text from natural language text")
    parser.add_argument('--input', type=str, required=True, help='Input CSV file, must have a text column')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for scenegraph')
    parser.add_argument('--enriched-output', type=str, required=True, help='Output file for enriched text')
    parser.add_argument('--deepseek-key', type=str, required=True, help='DeepSeek API Key')
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if 'text' not in df.columns:
        raise ValueError('CSV must contain a text column')

    all_scenegraphs = []
    enriched_texts = []
    for idx, row in df.iterrows():
        text = row['text']
        try:
            enriched_text, scenegraph = call_llm(text, args.deepseek_key)
            # Add time index if missing
            for i, sg in enumerate(scenegraph):
                if 'time' not in sg:
                    sg['time'] = f"T{idx+1}"
            all_scenegraphs.extend(scenegraph)
            enriched_texts.append(enriched_text)
        except Exception as e:
            print(f"Row {idx+1} failed: {e}")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(all_scenegraphs, f, ensure_ascii=False, indent=2)
    with open(args.enriched_output, 'w', encoding='utf-8') as f:
        for enriched in enriched_texts:
            f.write(enriched + '\n')
    print(f"Scene graphs saved to {args.output}")
    print(f"Enriched texts saved to {args.enriched_output}")

if __name__ == '__main__':
    main()
