import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from evaluator import SceneGraphEvaluator
import json

def test_evaluator():
    evaluator = SceneGraphEvaluator()
    
    # Test JSON file evaluation
    pred_file = "test_pred_data.json"
    gt_file = "test_gt_data.json"
    
    try:
        # Load test data
        pred_data = evaluator.load_json(pred_file)
        gt_data = evaluator.load_json(gt_file)
        
        print("Predicted data:")
        print(json.dumps(pred_data, indent=2, ensure_ascii=False))
        print("\nGround truth data:")
        print(json.dumps(gt_data, indent=2, ensure_ascii=False))
        
        # Run evaluation
        results = evaluator.evaluate_from_json(
            pred_data, gt_data, 
            seen_predicates=None,
            k_values=[1, 5, 10],
            align_by='id',
            align_mode='min'
        )
        
        print("\nEvaluation results:")
        for key, value in results.items():
            if key == 'statistics':
                print(f"\nStatistics:")
                for stat_key, stat_value in value.items():
                    print(f"  {stat_key}: {stat_value}")
            else:
                if isinstance(value, float):
                    print(f"{key}: {value:.4f}")
                else:
                    print(f"{key}: {value}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_evaluator()