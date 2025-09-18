# Text2SG 使用示例

本文档提供了 Text2SG 工具的详细使用示例，帮助您快速上手各种功能。

## 基本使用流程

### 1. 数据准备

首先准备您的输入CSV文件，确保包含以下列：
- `text`: 需要转换为场景图的文本描述
- `scenegraph`: 对应的场景图JSON数据（可能包含多行格式问题）

示例CSV内容：
```csv
text,scenegraph
"A red car is parked next to a blue house","{""objects"": [{""name"": ""car"", ""attributes"": [""red""]}]}"
"The dog is running in the park","{""objects"": [
{""name"": ""dog"", ""attributes"": []},
{""name"": ""park"", ""attributes"": []}
]}"
```

### 2. 使用CLI命令

#### 格式化CSV文件
```bash
# 基本格式化
text2sg format input.csv output.csv

# 指定自定义列名
text2sg format input.csv output.csv --text-column "description" --scenegraph-column "graph_data"

# 启用详细输出
text2sg format input.csv output.csv --verbose
```

#### 提取特定列
```bash
# 提取默认列（text, scenegraph）
text2sg extract input.csv extracted.csv

# 提取自定义列
text2sg extract input.csv extracted.csv --columns "text,graph,metadata"

# 保持原始顺序
text2sg extract input.csv extracted.csv --preserve-order
```

#### 修复JSON格式问题
```bash
# 基本JSON修复
text2sg fix input.csv fixed.csv

# 指定JSON列
text2sg fix input.csv fixed.csv --json-column "scenegraph"

# 启用备份
text2sg fix input.csv fixed.csv --backup
```

#### 运行完整流水线
```bash
# 运行所有处理步骤
text2sg pipeline input.csv output.csv

# 自定义列名和选项
text2sg pipeline input.csv output.csv \
  --text-column "description" \
  --scenegraph-column "graph" \
  --backup \
  --verbose
```

## 编程接口使用

### 1. 基本服务使用

```python
from text2sg.services import FormatterService, ExtractorService, FixerService

# 初始化服务
formatter = FormatterService()
extractor = ExtractorService()
fixer = FixerService()

# 格式化CSV
result = formatter.format_csv('input.csv', 'output.csv')
print(f"处理了 {result.rows_processed} 行数据")

# 提取列
result = extractor.extract_columns('input.csv', 'extracted.csv', ['text', 'scenegraph'])
print(f"提取了 {len(result.extracted_columns)} 列")

# 修复JSON
result = fixer.fix_json('input.csv', 'fixed.csv', 'scenegraph')
print(f"修复了 {result.fixes_applied} 个JSON问题")
```

### 2. 使用流水线服务

```python
from text2sg.services import PipelineService
from text2sg.core.models import PipelineConfig

# 创建配置
config = PipelineConfig(
    text_column='text',
    scenegraph_column='scenegraph',
    enable_backup=True,
    batch_size=100
)

# 初始化流水线
pipeline = PipelineService(config)

# 运行完整流水线
result = pipeline.run_pipeline('input.csv', 'output.csv')

print(f"流水线执行结果:")
print(f"- 处理行数: {result.total_rows}")
print(f"- 成功行数: {result.successful_rows}")
print(f"- 失败行数: {result.failed_rows}")
print(f"- 执行时间: {result.execution_time:.2f}秒")
```

### 3. 便利函数使用

```python
from text2sg import format_csv_to_annotation, extract_columns_from_csv, fix_multiline_json_in_csv

# 使用便利函数
format_result = format_csv_to_annotation('input.csv', 'formatted.csv')
extract_result = extract_columns_from_csv('input.csv', 'extracted.csv', ['text', 'scenegraph'])
fix_result = fix_multiline_json_in_csv('input.csv', 'fixed.csv')
```

## 高级用法

### 1. 批量处理

```python
from text2sg.services import PipelineService
from pathlib import Path

pipeline = PipelineService()

# 批量处理多个文件
input_dir = Path('data/input')
output_dir = Path('data/output')

for csv_file in input_dir.glob('*.csv'):
    output_file = output_dir / f"processed_{csv_file.name}"
    result = pipeline.run_pipeline(str(csv_file), str(output_file))
    print(f"处理 {csv_file.name}: {result.successful_rows}/{result.total_rows} 成功")
```

### 2. 错误处理和重试

```python
from text2sg.services import PipelineService
from text2sg.core.exceptions import ValidationError, ProcessingError

pipeline = PipelineService()

try:
    result = pipeline.run_pipeline('input.csv', 'output.csv')
except ValidationError as e:
    print(f"数据验证错误: {e}")
except ProcessingError as e:
    print(f"处理错误: {e}")
    # 可以尝试重新处理或使用备份
except Exception as e:
    print(f"未知错误: {e}")
```

### 3. 自定义配置

```python
from text2sg.core.models import PipelineConfig
from text2sg.services import PipelineService

# 创建自定义配置
config = PipelineConfig(
    text_column='description',
    scenegraph_column='graph_data',
    enable_backup=True,
    backup_suffix='_backup',
    batch_size=50,
    max_retries=3,
    enable_validation=True
)

pipeline = PipelineService(config)
result = pipeline.run_pipeline('input.csv', 'output.csv')
```

## 常见使用场景

### 场景1：清理现有数据集

如果您有一个包含格式问题的现有数据集：

```bash
# 1. 首先修复JSON格式问题
text2sg fix messy_dataset.csv cleaned_dataset.csv --backup

# 2. 然后格式化整个文件
text2sg format cleaned_dataset.csv final_dataset.csv --verbose
```

### 场景2：准备训练数据

为机器学习模型准备标准化的训练数据：

```bash
# 运行完整流水线，确保数据质量
text2sg pipeline raw_data.csv training_data.csv \
  --backup \
  --verbose
```

### 场景3：数据验证和质量检查

```python
from text2sg.services import PipelineService

pipeline = PipelineService()
result = pipeline.run_pipeline('data.csv', 'validated_data.csv')

# 检查数据质量
if result.failed_rows > 0:
    print(f"警告: {result.failed_rows} 行数据处理失败")
    print("请检查日志文件获取详细信息")
else:
    print("所有数据处理成功！")
```

## 性能优化建议

1. **批量处理**: 对于大文件，使用适当的批量大小
2. **内存管理**: 处理超大文件时考虑分块处理
3. **并行处理**: 可以并行处理多个独立文件
4. **备份策略**: 根据数据重要性决定是否启用备份

```python
# 大文件处理示例
config = PipelineConfig(
    batch_size=1000,  # 增加批量大小
    enable_backup=False,  # 禁用备份以节省空间
    max_retries=1  # 减少重试次数
)
```

## 故障排除

### 常见问题

1. **CSV格式错误**: 确保CSV文件编码为UTF-8
2. **列名不匹配**: 使用 `--text-column` 和 `--scenegraph-column` 指定正确的列名
3. **JSON格式问题**: 使用 `fix` 命令预处理数据
4. **内存不足**: 减少批量大小或分割大文件

### 调试技巧

```bash
# 启用详细输出查看处理过程
text2sg pipeline input.csv output.csv --verbose

# 检查特定文件的问题
text2sg fix problematic.csv test_fix.csv --verbose
```

更多详细信息请参考项目文档和API参考。