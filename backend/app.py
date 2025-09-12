from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from csv_handler import CSVHandler

app = Flask(__name__)
CORS(app)

# 全局CSV处理器实例
csv_handler = CSVHandler()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Scene Graph Annotator API is running'})

@app.route('/open', methods=['POST'])
def open_csv():
    """打开CSV文件"""
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'error': '缺少文件路径参数'}), 400
        
        file_path = data['path']
        result = csv_handler.load_csv(file_path)
        
        return jsonify(result), 200
    
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/row', methods=['GET'])
def get_row():
    """根据索引或ID获取行数据"""
    try:
        index = request.args.get('index', type=int)
        row_id = request.args.get('id')
        
        if index is not None:
            row = csv_handler.get_row_by_index(index)
        elif row_id:
            row = csv_handler.get_row_by_id(row_id)
        else:
            return jsonify({'error': '必须提供index或id参数'}), 400
        
        if row is None:
            return jsonify({'error': '未找到指定的行'}), 404
        
        return jsonify(row), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/row/<row_id>', methods=['GET'])
def get_row_by_id(row_id):
    """根据ID获取行数据"""
    try:
        row = csv_handler.get_row_by_id(row_id)
        
        if row is None:
            return jsonify({'error': f'未找到ID为{row_id}的行'}), 404
        
        return jsonify(row), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/row/<row_id>', methods=['PUT'])
def update_row(row_id):
    """更新行数据"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '缺少更新数据'}), 400
        
        # 验证更新字段
        allowed_fields = ['input', 'scenegraph', 'is_reasonable', 'is_annotated']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({'error': '没有有效的更新字段'}), 400
        
        success = csv_handler.update_row(row_id, updates)
        
        if not success:
            return jsonify({'error': f'未找到ID为{row_id}的行'}), 404
        
        # 保存到文件
        csv_handler.save_csv()
        
        return jsonify({'message': '更新成功'}), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress', methods=['GET'])
def get_progress():
    """获取标注进度统计"""
    try:
        progress = csv_handler.get_progress()
        return jsonify(progress), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rows', methods=['GET'])
def get_all_rows():
    """获取所有行的基本信息（用于导航）"""
    try:
        rows_info = []
        for i, row in enumerate(csv_handler.data):
            rows_info.append({
                'index': i,
                'id': row['id'],
                'is_annotated': row['is_annotated'],
                'is_reasonable': row['is_reasonable']
            })
        
        return jsonify(rows_info), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)