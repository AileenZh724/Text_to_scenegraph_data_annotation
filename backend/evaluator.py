"""
场景图评估模块
提供各种评估指标的计算功能，包括 Recall@K, Mean Recall@K, Zero-shot Recall@K, 和 Micro F1
"""

import json
import os
from typing import List, Tuple, Dict, Any, Iterable, Optional
import pandas as pd


class SceneGraphEvaluator:
    """场景图评估器类"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def load_json(path: str) -> Any:
        """加载JSON文件"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def flatten_edges(scenes: List[Dict[str, Any]]) -> List[Tuple[str, str, str]]:
        """从场景列表中提取所有边的三元组 (subject, predicate, object)"""
        triples: List[Tuple[str, str, str]] = []
        for scene in scenes:
            edges = scene.get('edges', [])
            for e in edges:
                # 期望格式 [subj, pred, obj]
                if isinstance(e, (list, tuple)) and len(e) == 3:
                    s, p, o = e
                    # 归一化为字符串并去除空白
                    triples.append((str(s).strip(), str(p).strip(), str(o).strip()))
        return triples
    
    @staticmethod
    def normalize_items(data: Any) -> Tuple[List[Optional[str]], List[List[Dict[str, Any]]]]:
        """
        将输入JSON归一化为并行列表：ids 和 scenes-per-item
        
        接受两种格式：
          - [ [ {time, nodes, edges}, ... ], ... ]
          - [ { id, scenegraph: [ {time, nodes, edges}, ... ] }, ... ]
        返回 (ids, scenes_list)，其中 ids 可能包含 None
        """
        if not isinstance(data, list):
            raise ValueError('顶级JSON必须是项目列表')
        
        ids: List[Optional[str]] = []
        scenes_list: List[List[Dict[str, Any]]] = []
        
        for idx, item in enumerate(data):
            if isinstance(item, dict) and 'scenegraph' in item:
                rid = item.get('id')
                scenes = item['scenegraph']
            else:
                rid = None
                scenes = item
            
            if not isinstance(scenes, list):
                raise ValueError(f'项目 {idx} 的场景图必须是列表')
            
            # 将id归一化为字符串或None
            try:
                ids.append(None if pd.isna(rid) else str(rid))
            except Exception:
                ids.append(None)
            
            scenes_list.append(scenes)
        
        return ids, scenes_list
    
    @classmethod
    def extract_all_triples_from_scenes_list(cls, scenes_list: List[List[Dict[str, Any]]]) -> List[List[Tuple[str, str, str]]]:
        """从场景列表中提取所有三元组"""
        all_triples: List[List[Tuple[str, str, str]]] = []
        for scenes in scenes_list:
            triples = cls.flatten_edges(scenes)
            all_triples.append(triples)
        return all_triples
    
    @staticmethod
    def setify(triples: Iterable[Tuple[str, str, str]]) -> set:
        """将三元组转换为集合"""
        return set(triples)
    
    def recall_at_k(self, pred_items: List[List[Tuple[str, str, str]]], 
                    gt_items: List[List[Tuple[str, str, str]]], 
                    k: int) -> float:
        """
        计算微观 Recall@K
        """
        assert len(pred_items) == len(gt_items), '预测和真实数据长度不匹配'
        tp_sum = 0
        gt_sum = 0
        
        for preds, gts in zip(pred_items, gt_items):
            gt_set = self.setify(gts)
            if not gt_set:
                continue
            k_slice = self.setify(preds[:k]) if k > 0 else set()
            tp_sum += len(k_slice & gt_set)
            gt_sum += len(gt_set)
        
        return (tp_sum / gt_sum) if gt_sum > 0 else 0.0
    
    def mean_recall_at_k(self, pred_items: List[List[Tuple[str, str, str]]], 
                         gt_items: List[List[Tuple[str, str, str]]], 
                         k: int) -> float:
        """
        计算按关系谓词的宏观平均 Recall@K
        """
        assert len(pred_items) == len(gt_items), '预测和真实数据长度不匹配'
        
        # 按谓词聚合
        per_pred_tp: Dict[str, int] = {}
        per_pred_gt: Dict[str, int] = {}
        
        for preds, gts in zip(pred_items, gt_items):
            pred_k = preds[:k]
            pred_k_set = self.setify(pred_k)
            gt_set = self.setify(gts)
            
            for (_, p, _) in gt_set:
                per_pred_gt[p] = per_pred_gt.get(p, 0) + 1
            
            for t in (pred_k_set & gt_set):
                _, p, _ = t
                per_pred_tp[p] = per_pred_tp.get(p, 0) + 1
        
        recalls: List[float] = []
        for p, gt_count in per_pred_gt.items():
            tp = per_pred_tp.get(p, 0)
            recalls.append(tp / gt_count if gt_count > 0 else 0.0)
        
        return float(sum(recalls) / len(recalls)) if recalls else 0.0
    
    def zero_shot_recall_at_k(self, pred_items: List[List[Tuple[str, str, str]]], 
                              gt_items: List[List[Tuple[str, str, str]]], 
                              seen_predicates: set, 
                              k: int) -> float:
        """
        计算未见谓词的 Recall@K
        """
        assert len(pred_items) == len(gt_items), '预测和真实数据长度不匹配'
        tp_sum = 0
        zs_gt_sum = 0
        
        for preds, gts in zip(pred_items, gt_items):
            pred_k_set = self.setify(preds[:k])
            gt_set = self.setify(gts)
            zs_gt = {t for t in gt_set if t[1] not in seen_predicates}
            
            if not zs_gt:
                continue
            
            tp_sum += len(pred_k_set & zs_gt)
            zs_gt_sum += len(zs_gt)
        
        return (tp_sum / zs_gt_sum) if zs_gt_sum > 0 else 0.0
    
    def micro_f1(self, pred_items: List[List[Tuple[str, str, str]]], 
                 gt_items: List[List[Tuple[str, str, str]]]) -> Dict[str, float]:
        """
        计算微观平均的精确率、召回率和F1分数
        """
        assert len(pred_items) == len(gt_items), '预测和真实数据长度不匹配'
        tp = 0
        fp = 0
        fn = 0
        
        for preds, gts in zip(pred_items, gt_items):
            pset = self.setify(preds)
            gset = self.setify(gts)
            tp += len(pset & gset)
            fp += len(pset - gset)
            fn += len(gset - pset)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {"precision": precision, "recall": recall, "f1": f1}
    
    def evaluate_from_json(self, pred_data: Any, gt_data: Any, 
                          seen_predicates: Optional[List[str]] = None, 
                          k_values: List[int] = [1, 5, 10, 20, 50, 100],
                          align_by: str = 'index',
                          align_mode: str = 'error') -> Dict[str, Any]:
        """
        从JSON数据进行评估
        
        Args:
            pred_data: 预测数据JSON
            gt_data: 真实数据JSON
            seen_predicates: 已见谓词列表（用于zero-shot评估）
            k_values: K值列表
            align_by: 对齐方式 ('index' 或 'id')
            align_mode: 长度不匹配时的处理方式 ('error', 'min', 'gt', 'pred')
        
        Returns:
            评估结果字典
        """
        # 预处理数据
        pred_ids, pred_scenes_list = self.normalize_items(pred_data)
        pred_triples_items = self.extract_all_triples_from_scenes_list(pred_scenes_list)
        
        gt_ids, gt_scenes_list = self.normalize_items(gt_data)
        gt_triples_items = self.extract_all_triples_from_scenes_list(gt_scenes_list)
        
        # 按ID对齐（如果需要）
        if align_by == 'id':
            if any(i is None for i in pred_ids) or any(i is None for i in gt_ids):
                raise ValueError('按ID对齐需要预测和真实数据都提供每个项目的ID')
            
            pred_map = {pid: (idx, triples) for idx, (pid, triples) in enumerate(zip(pred_ids, pred_triples_items))}
            aligned_pred: List[List[Tuple[str, str, str]]] = []
            aligned_gt: List[List[Tuple[str, str, str]]] = []
            missing = []
            
            for gid, gtriples in zip(gt_ids, gt_triples_items):
                if gid in pred_map:
                    aligned_pred.append(pred_map[gid][1])
                    aligned_gt.append(gtriples)
                else:
                    missing.append(gid)
            
            if missing:
                print(f"警告: {len(missing)} 个真实数据ID在预测中未找到")
            
            pred_triples_items = aligned_pred
            gt_triples_items = aligned_gt
        
        # 处理长度不匹配
        if len(gt_triples_items) != len(pred_triples_items):
            lp, lg = len(pred_triples_items), len(gt_triples_items)
            if align_mode == 'error':
                raise ValueError(f'预测/真实数据项目数量不匹配: pred={lp} gt={lg}')
            elif align_mode == 'min':
                n = min(lp, lg)
                pred_triples_items = pred_triples_items[:n]
                gt_triples_items = gt_triples_items[:n]
            elif align_mode == 'gt':
                n = lg
                pred_triples_items = pred_triples_items[:n]
            elif align_mode == 'pred':
                n = lp
                gt_triples_items = gt_triples_items[:n]
        
        # 计算指标
        results = {}
        
        # Recall@K 和 Mean Recall@K
        for k in sorted(set(k_values)):
            r_at_k = self.recall_at_k(pred_triples_items, gt_triples_items, k)
            mr_at_k = self.mean_recall_at_k(pred_triples_items, gt_triples_items, k)
            results[f'recall@{k}'] = r_at_k
            results[f'mean_recall@{k}'] = mr_at_k
            
            # Zero-shot Recall@K
            if seen_predicates:
                seen_set = set(seen_predicates)
                zr_at_k = self.zero_shot_recall_at_k(pred_triples_items, gt_triples_items, seen_set, k)
                results[f'zero_shot_recall@{k}'] = zr_at_k
        
        # Micro F1
        prf = self.micro_f1(pred_triples_items, gt_triples_items)
        results.update(prf)
        
        # 添加统计信息
        results['statistics'] = {
            'total_items': len(pred_triples_items),
            'total_pred_triples': sum(len(triples) for triples in pred_triples_items),
            'total_gt_triples': sum(len(triples) for triples in gt_triples_items),
            'avg_pred_triples_per_item': sum(len(triples) for triples in pred_triples_items) / len(pred_triples_items) if pred_triples_items else 0,
            'avg_gt_triples_per_item': sum(len(triples) for triples in gt_triples_items) / len(gt_triples_items) if gt_triples_items else 0
        }
        
        return results
    
    def evaluate_from_csv_data(self, pred_rows: List[Dict], gt_rows: List[Dict], 
                              seen_predicates: Optional[List[str]] = None,
                              k_values: List[int] = [1, 5, 10, 20, 50, 100]) -> Dict[str, Any]:
        """
        从CSV行数据进行评估
        
        Args:
            pred_rows: 预测数据行列表，每行包含 'id' 和 'scenegraph' 字段
            gt_rows: 真实数据行列表，每行包含 'id' 和 'scenegraph' 字段
            seen_predicates: 已见谓词列表
            k_values: K值列表
        
        Returns:
            评估结果字典
        """
        # 转换为JSON格式
        pred_data = []
        gt_data = []
        
        for row in pred_rows:
            try:
                scenegraph = json.loads(row['scenegraph']) if isinstance(row['scenegraph'], str) else row['scenegraph']
                pred_data.append({
                    'id': row['id'],
                    'scenegraph': scenegraph
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        for row in gt_rows:
            try:
                scenegraph = json.loads(row['scenegraph']) if isinstance(row['scenegraph'], str) else row['scenegraph']
                gt_data.append({
                    'id': row['id'],
                    'scenegraph': scenegraph
                })
            except (json.JSONDecodeError, KeyError):
                continue
        
        return self.evaluate_from_json(pred_data, gt_data, seen_predicates, k_values, 
                                     align_by='id', align_mode='min')