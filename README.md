# 场景图数据标注工具

基于 Flask（后端）+ Vue 3（前端）的场景图（Scene Graph）数据标注应用。

## 功能特性

- 📁 **CSV文件管理**：读取和编辑本地CSV文件
- 🎨 **可视化展示**：使用Cytoscape.js渲染场景图
- ✏️ **实时编辑**：JSON编辑器支持实时编辑和验证
- 🔄 **数据同步**：前后端实时数据同步
- 📊 **进度跟踪**：标注进度统计和导航
- ✅ **数据验证**：完整的数据格式验证

## 数据格式

CSV文件必须包含以下列（按顺序）：

1. `id` - 唯一标识符
2. `input` - 原始输入文本
3. `scenegraph` - JSON格式的场景图数据
4. `is_reasonable` - 布尔值（true/false）
5. `is_annotated` - 布尔值（true/false）

### Scenegraph JSON 格式

```json
[
  {
    "time": "T1",
    "nodes": [
      {
        "id": "person1",
        "attributes": ["tall", "wearing_hat"]
      },
      {
        "id": "table1",
        "attributes": ["wooden", "round"]
      }
    ],
    "edges": [
      ["person1", "sits_on", "table1"]
    ]
  }
]
```

## 安装和运行

### 前置要求

- Python 3.11+
- Node.js 16+
- npm 或 yarn

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 安装Python依赖：
```bash
pip install -r requirements.txt
```

3. 启动Flask服务器：
```bash
python app.py
```

后端将在 `http://localhost:5000` 运行

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端将在 `http://localhost:3000` 运行

## 使用说明

1. **加载文件**：在页面顶部输入CSV文件的完整路径，点击"加载文件"按钮

2. **查看数据**：
   - 上方显示当前样本的输入文本
   - 中间显示场景图的可视化（按时间分组）
   - 右侧提供JSON编辑器进行直接编辑

3. **编辑标注**：
   - 修改输入文本
   - 在JSON编辑器中编辑场景图
   - 切换"是否合理"和"已标注"开关

4. **保存和导航**：
   - 点击"保存"按钮保存修改
   - 使用"上一条"/"下一条"按钮导航
   - 查看标注进度统计

## API接口

### 后端API

- `POST /open` - 打开CSV文件
- `GET /row?index=N` - 根据索引获取行
- `GET /row/{id}` - 根据ID获取行
- `PUT /row/{id}` - 更新行数据
- `GET /progress` - 获取标注进度
- `GET /rows` - 获取所有行的基本信息

## 项目结构

```
data_annotator/
├── backend/
│   ├── app.py              # Flask应用主文件
│   ├── csv_handler.py      # CSV处理模块
│   └── requirements.txt    # Python依赖
├── frontend/
│   ├── src/
│   │   ├── App.vue        # 主应用组件
│   │   ├── main.js        # 应用入口
│   │   └── style.css      # 样式文件
│   ├── index.html         # HTML模板
│   ├── package.json       # 项目配置
│   └── vite.config.js     # Vite配置
├── unmarked_dataset.csv   # 示例数据文件
└── README.md             # 项目文档
```

## 开发说明

### 数据验证

应用包含多层数据验证：
- 前端实时JSON格式验证
- 后端完整数据结构验证
- 场景图节点和边的引用完整性检查

### 备份机制

每次保存时会自动创建备份文件，格式为：
`原文件名.backup_YYYYMMDD_HHMMSS`

### 错误处理

- 友好的错误提示信息
- 自动错误恢复机制
- 详细的日志记录

## 故障排除

### 常见问题

1. **文件路径错误**：确保使用完整的绝对路径
2. **端口冲突**：检查5000和3000端口是否被占用
3. **依赖安装失败**：尝试使用虚拟环境或更新包管理器

### 日志查看

- 后端日志：查看终端输出
- 前端日志：打开浏览器开发者工具

## 许可证

本项目仅用于学术研究目的。