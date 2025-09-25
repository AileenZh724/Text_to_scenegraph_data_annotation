import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from evaluator import SceneGraphEvaluator
import json

def test_evaluator():
    evaluator = SceneGraphEvaluator()
    
    # 测试JSON文件评估
    pred_file = "test_pred_data.json"
    gt_file = "test_gt_data.json"
    
    try:
        # 加载测试数据
        pred_data = evaluator.load_json(pred_file)
        gt_data = evaluator.load_json(gt_file)
        
        print("预测数据:")
        print(json.dumps(pred_data, indent=2, ensure_ascii=False))
        print("\n真实数据:")
        print(json.dumps(gt_data, indent=2, ensure_ascii=False))
        
        # 运行评估
        results = evaluator.evaluate_from_json(
            pred_data, gt_data, 
            seen_predicates=None,
            k_values=[1, 5, 10],
            align_by='id',
            align_mode='min'
        )
        
        print("\n评估结果:")
        for key, value in results.items():
            if key == 'statistics':
                print(f"\n统计信息:")
                for stat_key, stat_value in value.items():
                    print(f"  {stat_key}: {stat_value}")
            else:
                if isinstance(value, float):
                    print(f"{key}: {value:.4f}")
                else:
                    print(f"{key}: {value}")
        
        print("\n测试成功完成！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_evaluator()