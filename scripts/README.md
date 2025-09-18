# Scripts 目录说明

这个目录包含了数据标注项目的各种实用脚本。以下是每个脚本的简单说明：

## 📝 数据处理脚本

### `data_annotation_formatter.py`
**用途**: 数据格式转换器  
**功能**: 将原始CSV文件转换为标注格式，包含5个字段：id, input, scenegraph, is_reasonable, is_annotated  
**使用**: `python data_annotation_formatter.py input.csv output.csv`

### `extract_input.py`
**用途**: 提取输入列  
**功能**: 从CSV文件中提取'input'列，生成新的CSV文件  
**使用**: `python extract_input.py --input dataset.csv --output output.csv`

### `fix_csv_multiline_json.py`
**用途**: CSV修复工具  
**功能**: 修复CSV文件中跨行的JSON数据问题，将多行JSON合并为单行  
**使用**: `python fix_csv_multiline_json.py input.csv [output.csv]`

## 🤖 AI场景图生成器

### `simple_generator.py`
**用途**: 简化场景图生成器  
**功能**: 使用本地Ollama模型生成场景图，支持交互模式  
**使用**: 
- 单次生成: `python simple_generator.py "你的文本描述"`
- 交互模式: `python simple_generator.py --interactive`

### `deepseek_v3_scenegraph_generator.py`
**用途**: DeepSeek API场景图生成器  
**功能**: 使用DeepSeek R1 API批量处理CSV文件，生成场景图  
**使用**: `python deepseek_v3_scenegraph_generator.py input.csv [output.csv]`  
**需要**: DEEPSEEK_API_KEY环境变量

### `gemini_2.0_flash_scenegraph_generator.py`
**用途**: Gemini API场景图生成器  
**功能**: 使用Google Gemini 2.0 Flash API批量处理CSV文件，生成场景图  
**使用**: `python gemini_2.0_flash_scenegraph_generator.py input.csv [output.csv]`  
**需要**: GEMINI_API_KEY环境变量

## ⚙️ 配置文件

### `example.env`
**用途**: 环境变量配置模板  
**功能**: 提供API密钥配置示例  
**使用**: 复制为`.env`文件并填入真实的API密钥

## 🚀 快速开始

1. **数据准备**: 使用 `data_annotation_formatter.py` 转换数据格式
2. **场景图生成**: 选择一个AI生成器脚本处理数据
3. **数据修复**: 如果遇到JSON格式问题，使用 `fix_csv_multiline_json.py`

## 📋 依赖要求

- Python 3.7+
- requests库（API调用）
- python-dotenv库（环境变量）
- csv, json等标准库

## 💡 提示

- 所有脚本都支持 `--help` 参数查看详细使用说明
- API生成器需要相应的API密钥
- 建议先用小数据集测试再处理大文件