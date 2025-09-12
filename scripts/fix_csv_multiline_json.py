#!/usr/bin/env python3
"""
CSV多行JSON修复脚本

此脚本用于修复CSV文件中跨行的JSON数据问题，将多行JSON合并为单行。
"""

import csv
import json
import re
import sys
import os
from datetime import datetime


def fix_multiline_json_in_csv(input_file: str, output_file: str = None) -> bool:
    """
    修复CSV文件中的多行JSON数据
    
    Args:
        input_file (str): 输入CSV文件路径
        output_file (str): 输出CSV文件路径，如果为None则覆盖原文件
        
    Returns:
        bool: 处理是否成功
    """
    if output_file is None:
        # 创建备份文件
        backup_file = f"{input_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(input_file, backup_file)
        output_file = input_file
        print(f"已创建备份文件: {backup_file}")
    
    try:
        # 读取原始文件内容
        with open(backup_file if output_file == input_file else input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"原始文件大小: {len(content)} 字符")
        
        # 修复多行JSON的策略：
        # 1. 找到所有的JSON字段（scenegraph列）
        # 2. 将跨行的JSON合并为单行
        
        # 首先按行分割
        lines = content.split('\n')
        print(f"总行数: {len(lines)}")
        
        # 处理CSV数据
        fixed_lines = []
        current_row = ""
        in_json = False
        json_bracket_count = 0
        json_quote_count = 0
        
        for i, line in enumerate(lines):
            if i == 0:  # 头部行
                fixed_lines.append(line)
                continue
                
            # 检查是否在JSON字段中
            if not in_json:
                # 检查这一行是否开始了JSON数据
                # 寻找包含JSON开始标记的行
                if '"[' in line or '","[' in line:
                    in_json = True
                    current_row = line
                    # 计算括号和引号
                    json_bracket_count = line.count('[') - line.count(']')
                    # 计算未转义的引号数量（简化处理）
                    json_quote_count = line.count('"') - line.count('\\"')
                else:
                    fixed_lines.append(line)
            else:
                # 在JSON中，继续累积行
                current_row += " " + line.strip()
                json_bracket_count += line.count('[') - line.count(']')
                json_quote_count += line.count('"') - line.count('\\"')
                
                # 检查JSON是否结束
                # 简化的结束检测：当括号平衡且行以特定模式结束时
                if (json_bracket_count <= 0 and 
                    (line.strip().endswith('"]"') or 
                     line.strip().endswith(']",true,false') or
                     line.strip().endswith(']",false,false') or
                     line.strip().endswith(']",true,true') or
                     line.strip().endswith(']",false,true'))):
                    
                    # JSON结束，添加到结果中
                    fixed_lines.append(current_row)
                    current_row = ""
                    in_json = False
                    json_bracket_count = 0
                    json_quote_count = 0
        
        # 如果还有未完成的行
        if current_row:
            fixed_lines.append(current_row)
        
        # 写入修复后的文件
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write('\n'.join(fixed_lines))
        
        print(f"修复完成！")
        print(f"原始行数: {len(lines)}")
        print(f"修复后行数: {len(fixed_lines)}")
        print(f"输出文件: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        return False


def validate_csv_structure(file_path: str) -> bool:
    """
    验证CSV文件结构是否正确
    
    Args:
        file_path (str): CSV文件路径
        
    Returns:
        bool: 结构是否正确
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        print(f"CSV验证结果:")
        print(f"- 总行数: {len(rows)}")
        print(f"- 列名: {reader.fieldnames}")
        
        # 检查JSON格式
        json_valid_count = 0
        json_invalid_count = 0
        
        for i, row in enumerate(rows[:10]):  # 只检查前10行
            scenegraph = row.get('scenegraph', '')
            if scenegraph:
                try:
                    json.loads(scenegraph)
                    json_valid_count += 1
                except json.JSONDecodeError:
                    json_invalid_count += 1
                    print(f"第{i+1}行JSON格式错误")
        
        print(f"- 前10行中有效JSON: {json_valid_count}")
        print(f"- 前10行中无效JSON: {json_invalid_count}")
        
        return json_invalid_count == 0
        
    except Exception as e:
        print(f"验证过程中出现错误: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python fix_csv_multiline_json.py <input_csv_file> [output_csv_file]")
        print("如果不指定输出文件，将覆盖原文件（会自动创建备份）")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 '{input_file}' 不存在")
        sys.exit(1)
    
    print(f"开始处理文件: {input_file}")
    
    # 修复多行JSON
    if fix_multiline_json_in_csv(input_file, output_file):
        print("\n修复完成！")
        
        # 验证修复结果
        result_file = output_file if output_file else input_file
        print(f"\n验证修复结果...")
        if validate_csv_structure(result_file):
            print("✓ CSV文件结构验证通过")
        else:
            print("✗ CSV文件结构验证失败，可能需要手动检查")
    else:
        print("修复失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()