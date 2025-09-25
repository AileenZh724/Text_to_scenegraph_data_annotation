# 场景图评估功能集成指南

## 概述

本项目已成功将场景图评估功能集成到现有的文本到场景图数据标注系统中。评估功能支持多种评估指标，帮助用户量化评估场景图生成的质量。

## 集成内容

### 1. 后端API扩展

#### 新增评估模块 (`backend/evaluator.py`)
- **SceneGraphEvaluator类**：提供完整的场景图评估功能
- 支持多种评估指标：
  - **Recall@K**：微观召回率
  - **Mean Recall@K (mR@K)**：按谓词的宏观平均召回率
  - **Zero-shot Recall@K (zR@K)**：未见谓词的召回率
  - **Micro F1**：微观精确率、召回率和F1分数

#### 新增API端点

1. **POST `/api/evaluate`**：执行评估
   ```json
   {
     "type": "current|file|compare",
     "k_values": [1, 5, 10, 20, 50, 100],
     "seen_predicates": ["sits_on", "next_to", "in"],
     "pred_file": "path/to/predictions.json",
     "gt_file": "path/to/ground_truth.json",
     "align_by": "index|id",
     "align_mode": "error|min|gt|pred"
   }
   ```

2. **POST `/api/evaluate/export`**：导出评估结果
   ```json
   {
     "results": {...},
     "format": "json|csv|txt",
     "output_file": "evaluation_results"
   }
   ```

### 2. 前端界面增强

#### 新增评估功能界面
- **评估按钮**：在主界面的控制区域添加评估按钮
- **评估模态框**：提供直观的评估配置和结果展示界面
- **两种评估模式**：
  - **当前数据评估**：评估当前加载的CSV数据
  - **文件比较评估**：比较两个JSON文件

#### 评估结果展示
- **网格布局**：清晰显示所有评估指标
- **统计信息**：显示数据集统计信息
- **导出功能**：支持JSON、CSV、TXT格式导出

## 使用方法

### 1. 启动系统

1. **启动后端**：
   ```bash
   cd backend
   pip install -r requirements.txt
   python app.py
   ```

2. **启动前端**：
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

### 2. 使用评估功能

#### 方式一：当前数据评估
1. 加载CSV数据文件
2. 确保有已标注且合理的数据
3. 点击"评估"按钮
4. 选择"当前数据评估"标签页
5. 配置K值和已见谓词（可选）
6. 点击"开始评估"

#### 方式二：文件比较评估
1. 点击"评估"按钮
2. 选择"文件比较评估"标签页
3. 输入预测文件和真实数据文件路径
4. 选择对齐方式和长度不匹配处理方式
5. 配置K值和已见谓词（可选）
6. 点击"开始评估"

### 3. 评估结果解读

#### 主要指标
- **Recall@K**：前K个预测中正确的比例（微观平均）
- **Mean Recall@K**：按关系谓词计算的平均召回率（宏观平均）
- **Zero-shot Recall@K**：未见谓词的召回率（如果提供已见谓词列表）
- **精确率、召回率、F1**：整体预测质量指标

#### 统计信息
- **总项目数**：参与评估的样本数量
- **三元组数量**：预测和真实数据的三元组总数
- **平均三元组数**：每个样本的平均三元组数量

## 数据格式要求

### JSON格式
支持两种JSON格式：

#### 格式一：简单列表格式
```json
[
  [
    {
      "time": 0,
      "nodes": ["person", "chair"],
      "edges": [["person", "sits_on", "chair"]]
    }
  ]
]
```

#### 格式二：包含ID的格式
```json
[
  {
    "id": "sample_1",
    "scenegraph": [
      {
        "time": 0,
        "nodes": ["person", "chair"],
        "edges": [["person", "sits_on", "chair"]]
      }
    ]
  }
]
```

### CSV格式
CSV文件需包含以下字段：
- **id**：样本唯一标识符
- **scenegraph**：JSON格式的场景图数据
- **is_annotated**：是否已标注（可选，用于筛选）
- **is_reasonable**：是否合理（可选，用于筛选）

## 测试示例

项目包含测试文件供快速验证：
- `test_evaluation.py`：评估模块测试脚本
- `test_pred_data.json`：示例预测数据
- `test_gt_data.json`：示例真实数据

运行测试：
```bash
python test_evaluation.py
```

## 技术实现

### 后端技术栈
- **Flask**：Web框架
- **pandas**：数据处理
- **Python标准库**：JSON处理、文件操作

### 前端技术栈
- **Vue.js 3**：前端框架
- **Composition API**：响应式状态管理
- **CSS Grid**：布局系统
- **Axios**：HTTP客户端

### 评估算法
- **集合操作**：基于Python set进行高效的三元组比较
- **微观/宏观平均**：支持不同的平均策略
- **灵活对齐**：支持按索引或ID对齐数据
- **错误处理**：完善的异常处理和用户友好的错误信息

## 扩展和定制

### 添加新的评估指标
1. 在 `SceneGraphEvaluator` 类中添加新的方法
2. 在 `evaluate_from_json` 方法中调用新指标
3. 更新前端的 `formatMetricName` 函数以支持新指标的显示

### 自定义数据格式
1. 修改 `normalize_items` 方法以支持新的输入格式
2. 更新 `extract_all_triples_from_scenes_list` 方法以适应新的数据结构

### 性能优化
- 对于大型数据集，可考虑实现批量处理
- 添加进度显示功能
- 实现结果缓存机制

## 故障排除

### 常见问题

1. **文件路径错误**：
   - 确保文件路径使用绝对路径
   - 检查文件是否存在和可读

2. **JSON格式错误**：
   - 验证JSON文件格式是否正确
   - 检查场景图数据结构是否符合要求

3. **数据对齐问题**：
   - 使用合适的对齐模式
   - 检查ID字段是否存在和唯一

4. **依赖安装问题**：
   - 确保安装了所有必需的Python包
   - 检查pandas版本兼容性

### 调试建议
- 查看浏览器控制台的错误信息
- 检查Flask后端的日志输出
- 使用测试数据验证功能是否正常

## 总结

场景图评估功能的集成为文本到场景图数据标注系统提供了强大的质量评估能力。通过直观的用户界面和丰富的评估指标，用户可以更好地理解和改进场景图生成的质量。系统的模块化设计也便于未来的扩展和定制。