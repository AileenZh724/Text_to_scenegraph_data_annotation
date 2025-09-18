import csv
import json
import os
from datetime import datetime
import shutil
from typing import List, Dict, Any, Optional

class CSVHandler:
    def __init__(self):
        self.csv_path = None
        self.data = []
        self.headers = ['id', 'input', 'scenegraph', 'is_reasonable', 'is_annotated']
    
    def validate_headers(self, headers: List[str]) -> bool:
        """验证CSV文件的表头是否正确"""
        return headers == self.headers
    
    def load_csv(self, file_path: str) -> Dict[str, Any]:
        """加载CSV文件"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as file:
                reader = csv.reader(file)
                rows = list(reader)
                
                if not rows:
                    raise ValueError("CSV文件为空")
                
                headers = rows[0]
                if not self.validate_headers(headers):
                    raise ValueError(f"CSV表头不正确。期望: {self.headers}, 实际: {headers}")
                
                self.csv_path = file_path
                self.data = []
                
                for i, row in enumerate(rows[1:], 1):
                    if len(row) != len(self.headers):
                        raise ValueError(f"第{i+1}行列数不正确。期望{len(self.headers)}列，实际{len(row)}列")
                    
                    # 验证scenegraph字段是否为有效JSON
                    try:
                        scenegraph_data = json.loads(row[2]) if row[2] else []
                        self.validate_scenegraph(scenegraph_data)
                    except json.JSONDecodeError:
                        raise ValueError(f"第{i+1}行scenegraph字段不是有效的JSON")
                    except Exception as e:
                        raise ValueError(f"第{i+1}行scenegraph验证失败: {str(e)}")
                    
                    # 验证布尔字段
                    if row[3].lower() not in ['true', 'false']:
                        raise ValueError(f"第{i+1}行is_reasonable字段必须是true或false")
                    if row[4].lower() not in ['true', 'false']:
                        raise ValueError(f"第{i+1}行is_annotated字段必须是true或false")
                    
                    self.data.append({
                        'id': row[0],
                        'input': row[1],
                        'scenegraph': row[2],
                        'is_reasonable': row[3].lower() == 'true',
                        'is_annotated': row[4].lower() == 'true'
                    })
                
                return {
                    'success': True,
                    'total_rows': len(self.data),
                    'headers_valid': True,
                    'message': f'成功加载{len(self.data)}行数据'
                }
        
        except Exception as e:
            raise Exception(f"加载CSV文件失败: {str(e)}")
    
    def validate_scenegraph(self, scenegraph_data: List[Dict]) -> bool:
        """验证scenegraph数据结构"""
        if not isinstance(scenegraph_data, list):
            raise ValueError("scenegraph必须是数组")
        
        for i, time_group in enumerate(scenegraph_data):
            if not isinstance(time_group, dict):
                raise ValueError(f"时间组{i}必须是对象")
            
            if 'time' not in time_group:
                raise ValueError(f"时间组{i}缺少time字段")
            
            if 'nodes' not in time_group or not isinstance(time_group['nodes'], list):
                raise ValueError(f"时间组{i}的nodes字段必须是数组")
            
            if 'edges' not in time_group or not isinstance(time_group['edges'], list):
                raise ValueError(f"时间组{i}的edges字段必须是数组")
            
            # 验证节点
            node_ids = set()
            for j, node in enumerate(time_group['nodes']):
                if not isinstance(node, dict) or 'id' not in node:
                    raise ValueError(f"时间组{i}节点{j}必须包含id字段")
                
                node_id = node['id']
                if node_id in node_ids:
                    raise ValueError(f"时间组{i}中节点ID '{node_id}' 重复")
                node_ids.add(node_id)
                
                if 'attributes' in node and not isinstance(node['attributes'], list):
                    raise ValueError(f"时间组{i}节点{j}的attributes必须是数组")
            
            # 验证边
            for j, edge in enumerate(time_group['edges']):
                if not isinstance(edge, list) or len(edge) != 3:
                    raise ValueError(f"时间组{i}边{j}必须是包含3个元素的数组")
                
                src_id, relation, dst_id = edge
                if src_id not in node_ids:
                    raise ValueError(f"时间组{i}边{j}的源节点'{src_id}'不存在")
                if dst_id not in node_ids:
                    raise ValueError(f"时间组{i}边{j}的目标节点'{dst_id}'不存在")
        
        return True
    
    def get_row_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """根据索引获取行数据"""
        if 0 <= index < len(self.data):
            return self.data[index]
        return None
    
    def get_row_by_id(self, row_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取行数据"""
        for row in self.data:
            if row['id'] == row_id:
                return row
        return None
    
    def update_row(self, row_id: str, updates: Dict[str, Any]) -> bool:
        """更新行数据"""
        for i, row in enumerate(self.data):
            if row['id'] == row_id:
                # 验证更新的scenegraph
                if 'scenegraph' in updates:
                    try:
                        scenegraph_data = json.loads(updates['scenegraph'])
                        self.validate_scenegraph(scenegraph_data)
                    except Exception as e:
                        raise ValueError(f"scenegraph验证失败: {str(e)}")
                
                # 更新数据
                for key, value in updates.items():
                    if key in ['id', 'input', 'scenegraph', 'is_reasonable', 'is_annotated']:
                        self.data[i][key] = value
                
                return True
        return False
    
    def save_csv(self) -> bool:
        """保存CSV文件"""
        if not self.csv_path:
            raise ValueError("没有加载的CSV文件")
        
        # 创建备份
        backup_path = f"{self.csv_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(self.csv_path, backup_path)
        
        try:
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)
                
                for row in self.data:
                    writer.writerow([
                        row['id'],
                        row['input'],
                        row['scenegraph'],
                        'true' if row['is_reasonable'] else 'false',
                        'true' if row['is_annotated'] else 'false'
                    ])
            
            return True
        except Exception as e:
            # 如果保存失败，恢复备份
            shutil.copy2(backup_path, self.csv_path)
            raise Exception(f"保存CSV文件失败: {str(e)}")
    
    def get_progress(self) -> Dict[str, int]:
        """获取标注进度统计"""
        total = len(self.data)
        annotated = sum(1 for row in self.data if row['is_annotated'])
        reasonable = sum(1 for row in self.data if row['is_reasonable'])
        
        return {
            'total': total,
            'annotated': annotated,
            'reasonable': reasonable
        }