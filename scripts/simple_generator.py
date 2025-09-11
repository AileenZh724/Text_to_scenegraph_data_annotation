#!/usr/bin/env python3
"""简化的场景图生成器

使用用户自定义的提示词格式
"""

import requests
import json
import sys
import re
from typing import Dict, Any, Optional


class SceneGraphGenerator:
    """场景图生成器"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "qwen3:0.6b"):
        self.ollama_url = ollama_url
        self.model = model
        
        # 用户自定义的提示词
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
    
    def generate_scene_graph(self, text: str) -> Optional[Dict[str, Any]]:
        """生成场景图"""
        prompt = self.prompt_template.format(text=text)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1024
            }
        }
        
        try:
            print(f"正在调用 {self.model} 生成场景图...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            generated_text = result.get("response", "")
            
            print(f"\n模型输出:\n{generated_text}")
            
            # 尝试提取JSON
            json_result = self._extract_json(generated_text)
            return json_result
            
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
        except Exception as e:
            print(f"生成失败: {e}")
            return None
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取JSON（支持单个对象或数组）"""
        # 尝试多种JSON提取模式
        json_patterns = [
            # 匹配代码块中的JSON数组
            r'```json\s*(\[[^`]*\])\s*```',
            r'```\s*(\[[^`]*\])\s*```',
            # 匹配代码块中的JSON对象
            r'```json\s*({[^`]*})\s*```',
            r'```\s*({[^`]*})\s*```',
            # 匹配output:后的JSON数组
            r'output:\s*(\[[\s\S]*?\])(?=\n\n|\n[a-zA-Z]|$)',
            # 匹配output:后的JSON对象
            r'output:\s*({[\s\S]*?})(?=\n\n|\n[a-zA-Z]|$)',
            # 匹配包含"time"的JSON数组
            r'(\[\s*{[\s\S]*?"time"[\s\S]*?"edges"[\s\S]*?\]\s*\])',
            # 匹配包含"time"的完整JSON对象
            r'({\s*"time"[\s\S]*?"edges"[\s\S]*?\]\s*})',
            # 匹配任何完整的JSON数组（包含time, nodes, edges）
            r'(\[[\s\S]*?"time"[\s\S]*?"nodes"[\s\S]*?"edges"[\s\S]*?\])',
            # 匹配任何完整的JSON对象（包含time, nodes, edges）
            r'({[\s\S]*?"time"[\s\S]*?"nodes"[\s\S]*?"edges"[\s\S]*?})',
            # 最后尝试匹配任何JSON数组
            r'(\[[\s\S]*?\])',
            # 最后尝试匹配任何JSON对象
            r'({[\s\S]*?})'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    # 清理可能的格式问题
                    cleaned_match = match.strip()
                    # 验证是否包含必要的字段
                    parsed = json.loads(cleaned_match)
                    
                    # 如果是数组，验证每个元素
                    if isinstance(parsed, list):
                        if all(isinstance(item, dict) and 'time' in item and 'nodes' in item and 'edges' in item for item in parsed):
                            return {"scenes": parsed}  # 包装成统一格式
                    # 如果是单个对象，验证字段
                    elif isinstance(parsed, dict) and 'time' in parsed and 'nodes' in parsed and 'edges' in parsed:
                        return {"scenes": [parsed]}  # 包装成统一格式
                        
                except json.JSONDecodeError:
                    continue
        
        print("无法提取有效的JSON格式")
        return None
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python simple_generator.py \"你的文本描述\"")
        print("  python simple_generator.py --interactive")
        sys.exit(1)
    
    generator = SceneGraphGenerator()
    
    # 检查连接
    if not generator.test_connection():
        print("错误: 无法连接到Ollama服务")
        print("请确保Ollama正在运行: ollama serve")
        sys.exit(1)
    
    if sys.argv[1] == "--interactive":
        # 交互模式
        print("=== 场景图生成器 - 交互模式 ===")
        print("输入 'quit' 退出")
        
        while True:
            text = input("\n请输入文本描述: ").strip()
            if text.lower() == 'quit':
                break
            
            if not text:
                continue
            
            result = generator.generate_scene_graph(text)
            if result:
                scenes = result.get('scenes', [])
                if len(scenes) == 1:
                    print("\n生成的场景图:")
                    print(json.dumps(scenes[0], indent=2, ensure_ascii=False))
                else:
                    print(f"\n生成的场景图 (共{len(scenes)}个时间片段):")
                    for i, scene in enumerate(scenes, 1):
                        print(f"\n=== 时间片段 {i} ({scene.get('time', 'Unknown')}) ===")
                        print(json.dumps(scene, indent=2, ensure_ascii=False))
                
                # 询问是否保存
                save = input("\n是否保存到文件? (y/n): ").strip().lower()
                if save == 'y':
                    filename = input("文件名 (默认: scene_graph.json): ").strip()
                    if not filename:
                        filename = "scene_graph.json"
                    
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            json.dump(result, f, indent=2, ensure_ascii=False)
                        print(f"已保存到: {filename}")
                    except Exception as e:
                        print(f"保存失败: {e}")
            else:
                print("生成失败")
    else:
        # 命令行模式
        text = sys.argv[1]
        print(f"输入文本: {text}")
        
        result = generator.generate_scene_graph(text)
        if result:
            scenes = result.get('scenes', [])
            if len(scenes) == 1:
                print("\n生成的场景图:")
                print(json.dumps(scenes[0], indent=2, ensure_ascii=False))
            else:
                print(f"\n生成的场景图 (共{len(scenes)}个时间片段):")
                for i, scene in enumerate(scenes, 1):
                    print(f"\n=== 时间片段 {i} ({scene.get('time', 'Unknown')}) ===")
                    print(json.dumps(scene, indent=2, ensure_ascii=False))
        else:
            print("生成失败")
            sys.exit(1)


if __name__ == "__main__":
    main()