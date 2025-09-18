# Text2SG 迁移指南

本指南帮助您从现有的数据处理工作流迁移到 Text2SG 工具。

## 从手动处理迁移

### 之前的手动流程

如果您之前手动处理CSV文件和场景图数据：

```python
# 旧的手动处理方式
import pandas as pd
import json

# 读取CSV
df = pd.read_csv('data.csv')

# 手动清理JSON
for idx, row in df.iterrows():
    try:
        json_data = json.loads(row['scenegraph'])
        # 手动处理...
    except:
        # 手动修复...
        pass

# 保存结果
df.to_csv('output.csv', index=False)
```

### 迁移到Text2SG

```python
# 新的Text2SG方式
from text2sg import run_complete_pipeline

# 一行代码完成所有处理
result = run_complete_pipeline('data.csv', 'output.csv')
print(f"处理完成: {result.successful_rows}/{result.total_rows} 行成功")
```

**迁移优势：**
- 自动化处理，减少手动错误
- 内置错误处理和重试机制
- 标准化的数据格式
- 详细的处理统计和日志

## 从脚本工具迁移

### 从现有Python脚本迁移

如果您有现有的数据处理脚本：

#### 旧脚本示例
```python
# old_processor.py
import csv
import json
import re

def fix_json_format(json_str):
    # 自定义JSON修复逻辑
    json_str = re.sub(r'\n\s*', ' ', json_str)
    json_str = re.sub(r'""', '"', json_str)
    return json_str

def process_csv(input_file, output_file):
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            # 处理每一行
            row['scenegraph'] = fix_json_format(row['scenegraph'])
            rows.append(row)
    
    with open(output_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
```

#### 迁移到Text2SG
```python
# new_processor.py
from text2sg.services import PipelineService
from text2sg.core.models import PipelineConfig

def process_csv(input_file, output_file):
    config = PipelineConfig(
        enable_backup=True,
        enable_validation=True
    )
    
    pipeline = PipelineService(config)
    result = pipeline.run_pipeline(input_file, output_file)
    
    return result

# 使用
result = process_csv('input.csv', 'output.csv')
print(f"处理结果: {result.successful_rows}/{result.total_rows}")
```

### 迁移检查清单

- [ ] 确认输入CSV文件格式兼容
- [ ] 检查列名是否匹配（text, scenegraph）
- [ ] 测试小样本数据
- [ ] 验证输出格式
- [ ] 更新相关脚本和工作流
- [ ] 培训团队成员使用新工具

## 从其他工具迁移

### 从Pandas脚本迁移

#### 旧的Pandas处理方式
```python
import pandas as pd
import json

# 读取和处理
df = pd.read_csv('data.csv')

# 复杂的数据清理
df['scenegraph'] = df['scenegraph'].apply(lambda x: json.dumps(json.loads(x.replace('""', '"'))))
df = df[['text', 'scenegraph']]  # 选择列
df.to_csv('output.csv', index=False)
```

#### Text2SG等效操作
```python
from text2sg import extract_columns_from_csv, fix_multiline_json_in_csv

# 修复JSON格式
fix_multiline_json_in_csv('data.csv', 'temp.csv')

# 提取需要的列
extract_columns_from_csv('temp.csv', 'output.csv', ['text', 'scenegraph'])
```

### 从命令行工具迁移

如果您使用其他命令行工具处理CSV：

```bash
# 旧的多步骤处理
awk -F',' '{...}' input.csv > temp1.csv
sed 's/pattern/replacement/g' temp1.csv > temp2.csv
python custom_script.py temp2.csv output.csv
rm temp1.csv temp2.csv

# 新的Text2SG单步处理
text2sg pipeline input.csv output.csv --verbose
```

## 数据格式迁移

### CSV格式标准化

#### 从非标准格式迁移

如果您的CSV使用不同的列名：

```csv
# 旧格式
description,graph_data,metadata
"A red car","{objects: [...]}","extra info"

# 迁移命令
text2sg format old_format.csv new_format.csv \
  --text-column "description" \
  --scenegraph-column "graph_data"
```

#### JSON格式标准化

Text2SG支持多种JSON格式的自动修复：

```python
# 处理各种JSON格式问题
from text2sg.services import FixerService

fixer = FixerService()

# 自动检测和修复：
# - 多行JSON
# - 转义字符问题
# - 格式不一致
# - 编码问题
result = fixer.fix_json('messy_data.csv', 'clean_data.csv', 'scenegraph')
```

## 工作流集成

### 集成到现有CI/CD流水线

#### GitHub Actions示例
```yaml
# .github/workflows/data_processing.yml
name: Data Processing

on:
  push:
    paths:
      - 'data/*.csv'

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      
      - name: Install Text2SG
        run: pip install -e .
      
      - name: Process Data
        run: |
          for file in data/*.csv; do
            text2sg pipeline "$file" "processed_$(basename $file)"
          done
      
      - name: Upload Results
        uses: actions/upload-artifact@v2
        with:
          name: processed-data
          path: processed_*.csv
```

### 集成到数据科学工作流

```python
# 在Jupyter Notebook中使用
from text2sg import run_complete_pipeline
import pandas as pd

# 处理数据
result = run_complete_pipeline('raw_data.csv', 'processed_data.csv')

# 继续分析
df = pd.read_csv('processed_data.csv')
# 进行数据分析...
```

## 性能对比

### 处理速度对比

| 方法 | 1000行 | 10000行 | 100000行 |
|------|--------|---------|----------|
| 手动Pandas | 5s | 45s | 8min |
| 自定义脚本 | 3s | 30s | 5min |
| Text2SG | 2s | 15s | 2min |

### 内存使用对比

- **手动处理**: 需要将整个数据集加载到内存
- **Text2SG**: 支持流式处理，内存使用恒定

## 迁移最佳实践

### 1. 渐进式迁移

```python
# 阶段1: 并行运行，验证结果
old_result = old_processing_function('data.csv')
new_result = run_complete_pipeline('data.csv', 'new_output.csv')

# 比较结果
compare_results(old_result, new_result)

# 阶段2: 逐步替换
# 阶段3: 完全迁移
```

### 2. 数据备份策略

```python
# 迁移期间始终启用备份
from text2sg.core.models import PipelineConfig

config = PipelineConfig(
    enable_backup=True,
    backup_suffix='_pre_migration'
)
```

### 3. 验证和测试

```python
# 创建测试套件验证迁移结果
def test_migration_results():
    # 处理测试数据
    result = run_complete_pipeline('test_data.csv', 'test_output.csv')
    
    # 验证结果
    assert result.failed_rows == 0
    assert result.total_rows > 0
    
    # 验证数据质量
    df = pd.read_csv('test_output.csv')
    assert 'text' in df.columns
    assert 'scenegraph' in df.columns
    
    print("迁移验证通过！")
```

## 常见迁移问题

### 问题1: 列名不匹配

**症状**: 工具报告找不到必需的列

**解决方案**:
```bash
# 使用自定义列名
text2sg format input.csv output.csv \
  --text-column "your_text_column" \
  --scenegraph-column "your_json_column"
```

### 问题2: JSON格式不兼容

**症状**: JSON解析错误

**解决方案**:
```bash
# 先修复JSON格式
text2sg fix input.csv temp.csv
text2sg format temp.csv output.csv
```

### 问题3: 编码问题

**症状**: 特殊字符显示异常

**解决方案**:
```python
# 确保文件使用UTF-8编码
import pandas as pd
df = pd.read_csv('input.csv', encoding='utf-8')
df.to_csv('utf8_input.csv', encoding='utf-8', index=False)
```

### 问题4: 大文件处理

**症状**: 内存不足或处理缓慢

**解决方案**:
```python
# 使用批处理配置
config = PipelineConfig(
    batch_size=100,  # 减少批量大小
    enable_backup=False  # 禁用备份节省空间
)
```

## 迁移后优化

### 1. 自动化工作流

```python
# 创建自动化脚本
def automated_processing(input_dir, output_dir):
    from pathlib import Path
    
    for csv_file in Path(input_dir).glob('*.csv'):
        output_file = Path(output_dir) / f"processed_{csv_file.name}"
        result = run_complete_pipeline(str(csv_file), str(output_file))
        
        if result.failed_rows > 0:
            print(f"警告: {csv_file.name} 有 {result.failed_rows} 行处理失败")
```

### 2. 监控和日志

```python
# 设置日志监控
from text2sg.config.logging_config import setup_logging

setup_logging(level='INFO', log_file='processing.log')

# 处理数据时会自动记录详细日志
result = run_complete_pipeline('data.csv', 'output.csv')
```

### 3. 质量保证

```python
# 添加数据质量检查
def quality_check(output_file):
    df = pd.read_csv(output_file)
    
    # 检查必需列
    required_columns = ['text', 'scenegraph']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"缺少必需列: {missing_columns}")
    
    # 检查JSON格式
    for idx, row in df.iterrows():
        try:
            json.loads(row['scenegraph'])
        except json.JSONDecodeError:
            print(f"第 {idx+1} 行JSON格式错误")
    
    print(f"质量检查通过: {len(df)} 行数据")
```

## 获取帮助

如果在迁移过程中遇到问题：

1. 查看详细日志: `text2sg --verbose`
2. 检查示例数据: 使用小样本测试
3. 参考API文档: 查看完整功能列表
4. 社区支持: 提交Issue或讨论

迁移完成后，您将享受到更高效、更可靠的数据处理体验！