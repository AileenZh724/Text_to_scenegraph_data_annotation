from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from csv_handler import CSVHandler
from evaluator import SceneGraphEvaluator

app = Flask(__name__)
CORS(app)

# 全局CSV处理器实例
csv_handler = CSVHandler()
# 全局评估器实例
evaluator = SceneGraphEvaluator()

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

@app.route('/evaluate', methods=['POST'])
def evaluate_scenegraphs():
    """评估场景图数据"""
    try:
        data = request.get_json()
        
        # 检查必需参数
        if not data:
            return jsonify({'error': '缺少请求数据'}), 400
        
        # 获取评估参数
        evaluation_type = data.get('type', 'current')  # 'current', 'file', 'compare'
        k_values = data.get('k_values', [1, 5, 10, 20, 50, 100])
        seen_predicates = data.get('seen_predicates', None)
        
        if evaluation_type == 'current':
            # 评估当前加载的CSV数据
            if not csv_handler.data:
                return jsonify({'error': '没有加载的数据可供评估'}), 400
            
            # 获取所有已标注且合理的数据作为预测数据
            pred_rows = [row for row in csv_handler.data if row.get('is_annotated') and row.get('is_reasonable')]
            
            if not pred_rows:
                return jsonify({'error': '没有找到已标注且合理的数据'}), 400
            
            # 如果没有提供真实数据，使用所有数据作为真实数据（用于统计分析）
            gt_rows = csv_handler.data
            
            results = evaluator.evaluate_from_csv_data(pred_rows, gt_rows, seen_predicates, k_values)
            
        elif evaluation_type == 'file':
            # 从文件评估
            pred_file = data.get('pred_file')
            gt_file = data.get('gt_file')
            
            if not pred_file or not gt_file:
                return jsonify({'error': '缺少预测文件或真实数据文件路径'}), 400
            
            # 检查文件是否存在
            if not os.path.exists(pred_file):
                return jsonify({'error': f'预测文件不存在: {pred_file}'}), 404
            if not os.path.exists(gt_file):
                return jsonify({'error': f'真实数据文件不存在: {gt_file}'}), 404
            
            # 加载JSON数据
            pred_data = evaluator.load_json(pred_file)
            gt_data = evaluator.load_json(gt_file)
            
            align_by = data.get('align_by', 'index')
            align_mode = data.get('align_mode', 'error')
            
            results = evaluator.evaluate_from_json(pred_data, gt_data, seen_predicates, 
                                                 k_values, align_by, align_mode)
        
        elif evaluation_type == 'compare':
            # 比较两个CSV文件
            pred_csv = data.get('pred_csv')
            gt_csv = data.get('gt_csv')
            
            if not pred_csv or not gt_csv:
                return jsonify({'error': '缺少要比较的CSV文件路径'}), 400
            
            # 加载CSV数据
            import pandas as pd
            pred_df = pd.read_csv(pred_csv)
            gt_df = pd.read_csv(gt_csv)
            
            pred_rows = pred_df.to_dict('records')
            gt_rows = gt_df.to_dict('records')
            
            results = evaluator.evaluate_from_csv_data(pred_rows, gt_rows, seen_predicates, k_values)
        
        else:
            return jsonify({'error': f'不支持的评估类型: {evaluation_type}'}), 400
        
        return jsonify({
            'success': True,
            'results': results,
            'evaluation_type': evaluation_type,
            'k_values': k_values
        }), 200
    
    except FileNotFoundError as e:
        return jsonify({'error': f'文件未找到: {str(e)}'}), 404
    except json.JSONDecodeError as e:
        return jsonify({'error': f'JSON解析错误: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'评估过程中出现错误: {str(e)}'}), 500

@app.route('/evaluate/export', methods=['POST'])
def export_evaluation_results():
    """导出评估结果"""
    try:
        data = request.get_json()
        
        if not data or 'results' not in data:
            return jsonify({'error': '缺少评估结果数据'}), 400
        
        results = data['results']
        export_format = data.get('format', 'json')  # 'json', 'csv', 'txt'
        output_file = data.get('output_file', 'evaluation_results')
        
        if export_format == 'json':
            output_path = f"{output_file}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        elif export_format == 'csv':
            output_path = f"{output_file}.csv"
            import pandas as pd
            
            # 将结果转换为DataFrame格式
            rows = []
            for key, value in results.items():
                if key != 'statistics' and isinstance(value, (int, float)):
                    rows.append({'metric': key, 'value': value})
            
            # 添加统计信息
            if 'statistics' in results:
                for stat_key, stat_value in results['statistics'].items():
                    rows.append({'metric': f'stats_{stat_key}', 'value': stat_value})
            
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)
        
        elif export_format == 'txt':
            output_path = f"{output_file}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("场景图评估结果\n")
                f.write("=" * 50 + "\n\n")
                
                for key, value in results.items():
                    if key == 'statistics':
                        f.write("\n统计信息:\n")
                        f.write("-" * 20 + "\n")
                        for stat_key, stat_value in value.items():
                            f.write(f"{stat_key}: {stat_value}\n")
                    elif isinstance(value, (int, float)):
                        f.write(f"{key}: {value:.4f}\n")
        
        else:
            return jsonify({'error': f'不支持的导出格式: {export_format}'}), 400
        
        return jsonify({
            'success': True,
            'message': f'评估结果已导出到: {output_path}',
            'output_path': output_path
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'导出过程中出现错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)