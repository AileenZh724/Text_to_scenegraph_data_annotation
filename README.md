# Text2SG - Text to Scene Graph Generation Tool

一个强大的文本到场景图生成和评估工具，支持CSV数据处理、多行JSON修复、场景图生成、质量评估和完整的数据处理管道。

## 功能特性

- 🔧 **CSV格式化**：将原始CSV转换为标注格式，支持自定义提示模板
- 📊 **列提取**：从CSV文件中提取指定列，支持灵活的列处理策略
- 🛠️ **JSON修复**：自动修复CSV中的多行JSON格式问题
- 🤖 **场景图生成**：使用Google Gemini API生成高质量场景图
- 📈 **质量评估**：集成完整的场景图评估系统，支持多种评估指标
- ⚡ **完整管道**：一键运行完整的文本到场景图处理流程
- 🖥️ **命令行界面**：直观的CLI工具，支持批处理和自动化
- 📝 **配置管理**：灵活的配置系统，支持环境变量和配置文件
- 🧪 **全面测试**：完整的单元测试覆盖，确保代码质量
- 🎯 **Web界面**：现代化的Vue.js前端界面，支持实时编辑和可视化

## 数据格式

### 输入CSV格式

基本的输入CSV文件应包含：
- `input` - 原始输入文本（可自定义列名）
- `id` - 样本唯一标识符（用于评估对齐）
- `is_annotated` - 是否已标注（布尔值）
- `is_reasonable` - 是否合理（布尔值）
- 其他列会被保留并传递到输出文件

### 场景图JSON格式

生成的场景图采用时间序列格式，支持动态场景：

```json
[
  {
    "time": 0,
    "nodes": ["person", "chair", "table"],
    "edges": [
      ["person", "sits_on", "chair"],
      ["chair", "next_to", "table"]
    ]
  },
  {
    "time": 1,
    "nodes": ["person", "chair", "table", "book"],
    "edges": [
      ["person", "sits_on", "chair"],
      ["book", "on", "table"]
    ]
  }
]
```

### 评估数据格式

评估功能支持两种JSON格式：

#### 简单列表格式（按索引对齐）
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

#### 包含ID格式（按ID对齐）
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

### 输出CSV格式

处理后的CSV文件包含：
- 原始输入列
- `scenegraph` - 生成的场景图JSON（时间序列格式）
- `is_annotated` - 标注状态
- `is_reasonable` - 合理性标记
- 所有原始列都会被保留

## 安装和设置

### 前置要求

- Python 3.8+
- Node.js 16+ (用于前端开发)
- Google AI API密钥（用于场景图生成）
- DeepSeek API密钥（可选，用于场景图生成）

### 快速开始

1. **克隆项目**：
   ```bash
   git clone <repository-url>
   cd Text_to_scenegraph_data_annotation
   ```

2. **后端设置**：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **前端设置**：
   ```bash
   cd frontend
   npm install
   ```

4. **环境配置**：
   ```bash
   # 复制环境配置文件
   cp scripts/example.env .env
   # 编辑 .env 文件，填入您的API密钥
   ```

5. **启动应用**：
   ```bash
   # 启动后端服务器 (终端1)
   cd backend
   python app.py
   
   # 启动前端开发服务器 (终端2)
   cd frontend
   npm run dev
   ```

6. **访问应用**：
   - 前端界面：http://localhost:3000
   - 后端API：http://localhost:5000

### 安装方式

#### 方式1：从源码安装

```bash
# 克隆仓库
git clone <repository-url>
cd data_annotator

# 安装依赖
pip install -r requirements.txt

# 安装为可编辑包
pip install -e .
```

#### 方式2：使用setup.py安装

```bash
# 安装包
python setup.py install
```

### 配置设置

#### 环境变量配置

创建 `.env` 文件：

```bash
# Google AI API配置
GOOGLE_AI_API_KEY=your_api_key_here
GOOGLE_AI_MODEL=gemini-1.5-flash
GOOGLE_AI_TEMPERATURE=0.3

# 处理配置
BATCH_SIZE=10
MAX_RETRIES=3

# 路径配置
INPUT_DIR=./data/input
OUTPUT_DIR=./data/output
BACKUP_DIR=./data/backup

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=structured
```

#### 配置文件

也可以使用 `config.yaml` 文件：

```yaml
api:
  google_ai_api_key: "your_api_key_here"
  model: "gemini-1.5-flash"
  temperature: 0.3

processing:
  batch_size: 10
  max_retries: 3
  timeout: 30

paths:
  input_dir: "./data/input"
  output_dir: "./data/output"
  backup_dir: "./data/backup"

logging:
  level: "INFO"
  format: "structured"
```

## 使用说明

### Web界面操作

1. **加载文件**：在页面顶部输入CSV文件的完整路径，点击"加载文件"按钮

2. **查看数据**：
   - 上方显示当前样本的输入文本
   - 中间显示场景图的可视化（按时间分组）
   - 右侧提供JSON编辑器进行直接编辑

3. **编辑标注**：
   - 修改输入文本
   - 在JSON编辑器中编辑场景图
   - 切换"是否合理"和"已标注"开关

4. **评估功能**：
   - 点击"评估"按钮打开评估界面
   - 支持两种评估模式：
     - **当前数据评估**：评估已加载的CSV数据中已标注且合理的样本
     - **文件比较评估**：比较预测文件和真实数据文件
   - 配置评估参数：K值、已见谓词、对齐方式等
   - 查看详细的评估结果和统计信息
   - 导出评估结果为JSON、CSV或TXT格式

5. **保存和导航**：
   - 点击"保存"按钮保存修改
   - 使用"上一条"/"下一条"按钮导航
   - 查看标注进度统计

### 评估指标说明

- **Recall@K**：前K个预测中正确的比例（微观平均）
- **Mean Recall@K (mR@K)**：按关系谓词计算的平均召回率（宏观平均）
- **Zero-shot Recall@K (zR@K)**：未见谓词的召回率
- **精确率、召回率、F1**：整体预测质量指标

### 命令行工具

项目还提供了多个命令行脚本用于批量处理：

```bash
# 场景图生成
cd scripts
python gemini_2.0_flash_scenegraph_generator.py
python deepseek_v3_scenegraph_generator.py

# 数据处理
python data_annotation_formatter.py
python fix_csv_multiline_json.py
python text_color_enrichment.py

# 独立评估
python ../test_evaluation.py
```

## API接口

### 后端API

#### 数据管理API
- `GET /health` - 健康检查
- `POST /open` - 打开CSV文件
- `GET /row?index=N` - 根据索引获取行
- `GET /row/{id}` - 根据ID获取行
- `PUT /row/{id}` - 更新行数据
- `GET /progress` - 获取标注进度
- `GET /rows` - 获取所有行的基本信息

#### 评估API
- `POST /evaluate` - 执行场景图评估
  - 支持参数：
    - `type`: 评估类型 (`current`/`file`/`compare`)
    - `k_values`: K值列表 (默认: `[1,5,10,20,50,100]`)
    - `seen_predicates`: 已见谓词列表 (可选)
    - `pred_file`: 预测文件路径 (文件评估模式)
    - `gt_file`: 真实数据文件路径 (文件评估模式)
    - `align_by`: 对齐方式 (`index`/`id`)
    - `align_mode`: 长度不匹配处理 (`error`/`min`/`gt`/`pred`)

- `POST /evaluate/export` - 导出评估结果
  - 支持格式：JSON, CSV, TXT

### 评估API示例

```javascript
// 当前数据评估
fetch('/api/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    type: 'current',
    k_values: [1, 5, 10],
    seen_predicates: ['sits_on', 'next_to']
  })
})

// 文件比较评估
fetch('/api/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    type: 'file',
    pred_file: '/path/to/predictions.json',
    gt_file: '/path/to/ground_truth.json',
    align_by: 'id',
    align_mode: 'min'
  })
})
```

## 项目结构

```
Text_to_scenegraph_data_annotation/
├── backend/
│   ├── app.py              # Flask应用主文件
│   ├── csv_handler.py      # CSV处理模块
│   ├── evaluator.py        # 场景图评估模块
│   └── requirements.txt    # Python依赖
├── frontend/
│   ├── src/
│   │   ├── App.vue        # 主应用组件
│   │   ├── main.js        # 应用入口
│   │   └── style.css      # 样式文件
│   ├── index.html         # HTML模板
│   ├── package.json       # 项目配置
│   └── vite.config.js     # Vite配置
├── scripts/
│   ├── gemini_2.0_flash_scenegraph_generator.py  # Gemini场景图生成
│   ├── deepseek_v3_scenegraph_generator.py       # DeepSeek场景图生成
│   ├── data_annotation_formatter.py              # 数据格式化
│   ├── fix_csv_multiline_json.py                 # JSON修复
│   ├── text_color_enrichment.py                  # 文本增强
│   └── example.env        # 环境配置示例
├── src/text2sg/           # 核心Python包
│   ├── __init__.py
│   ├── models.py          # 数据模型
│   ├── cli/               # 命令行界面
│   ├── core/              # 核心功能
│   ├── services/          # 服务层
│   └── providers/         # API提供商
├── tests/                 # 测试文件
├── docs/                  # 文档目录
├── logs/                  # 日志文件
├── test_evaluation.py     # 评估功能测试
├── test_pred_data.json    # 测试预测数据
├── test_gt_data.json      # 测试真实数据
├── EVALUATION_INTEGRATION_GUIDE.md  # 评估集成指南
├── unmarked_dataset.csv   # 示例数据文件
└── README.md             # 项目文档
```

## 文档

### 完整文档
- [评估功能集成指南](EVALUATION_INTEGRATION_GUIDE.md) - 详细的评估功能说明和使用指南
- [使用示例](docs/usage_examples.md) - 详细的使用示例和最佳实践
- [迁移指南](docs/migration_guide.md) - 从其他工具迁移到Text2SG的指南
- [API参考](docs/api_reference.md) - 完整的API接口文档

### 开发说明

#### 数据验证

应用包含多层数据验证：
- 前端实时JSON格式验证
- 后端完整数据结构验证
- 场景图节点和边的引用完整性检查
- 评估数据格式自动检测和转换

#### 备份机制

每次保存时会自动创建备份文件，格式为：
`原文件名.backup_YYYYMMDD_HHMMSS`

#### 错误处理

- 友好的错误提示信息
- 自动错误恢复机制
- 详细的日志记录
- 评估过程异常处理

#### 评估系统架构

- **模块化设计**：评估功能独立封装，易于扩展
- **多种指标支持**：Recall@K, Mean Recall@K, Zero-shot Recall@K, F1等
- **灵活的数据对齐**：支持索引和ID两种对齐方式
- **多格式导出**：结果可导出为JSON、CSV、TXT格式

## 故障排除

### 常见问题

1. **文件路径错误**：确保使用完整的绝对路径
2. **端口冲突**：检查5000(后端)和3000(前端)端口是否被占用
3. **依赖安装失败**：尝试使用虚拟环境或更新包管理器
4. **API密钥错误**：检查`.env`文件中的API密钥是否正确配置
5. **评估文件格式错误**：确保JSON文件格式符合要求
6. **数据对齐问题**：检查ID字段是否存在且唯一

### 日志查看

- 后端日志：查看终端输出
- 前端日志：打开浏览器开发者工具
- 评估日志：查看Flask应用的详细输出

### 性能优化

- 对于大型数据集，建议分批处理
- 评估大量数据时可能需要较长时间，请耐心等待
- 使用合适的K值范围以避免不必要的计算开销

### 测试评估功能

运行评估功能测试：
```bash
python test_evaluation.py
```

这将使用示例数据测试评估模块的各项功能。

## 更新日志

### v2.0.0 - 2025-09-26
#### 新增功能
- ✨ **场景图评估系统**：集成完整的评估功能，支持多种评估指标
- 📊 **评估指标**：Recall@K, Mean Recall@K, Zero-shot Recall@K, Micro F1
- 🎯 **多种评估模式**：当前数据评估、文件比较评估、CSV比较评估
- 💾 **结果导出**：支持JSON、CSV、TXT三种格式的结果导出
- 🔧 **灵活配置**：支持K值自定义、已见谓词配置、数据对齐方式选择
- 📈 **统计信息**：提供详细的数据集统计和评估结果分析

#### 技术改进
- 🏗️ **模块化架构**：新增独立的`evaluator.py`模块
- 🚀 **API扩展**：新增评估和导出相关的REST API端点
- 🎨 **界面优化**：新增美观的评估模态框和结果展示界面
- 🧪 **测试完善**：添加评估功能的完整测试用例

#### 文档更新
- 📚 **评估集成指南**：新增详细的评估功能使用文档
- 📖 **README更新**：完善项目说明和使用指南
- 🔍 **API文档**：更新API接口文档，包含评估相关接口

## 许可证

本项目仅用于学术研究目的。