

## data_annotation_formatter.py
**使用方法**: `python data_annotation_formatter.py <input_file> [output_file]`  
**作用**: 将原始CSV文件转换为标注格式，生成包含id、input、scenegraph、is_reasonable、is_annotated五个字段的CSV文件

## extract_input.py
**使用方法**: `python extract_input.py --input <input_file> --output <output_file>`  
**作用**: 从CSV文件中提取input列，生成只包含input字段的新CSV文件

## fix_csv_multiline_json.py
**使用方法**: `python fix_csv_multiline_json.py <input_csv_file> [output_csv_file]`  
**作用**: 修复CSV文件中跨行的JSON数据问题，将多行JSON合并为单行

## simple_generator.py
**使用方法**: 
- 单次生成: `python simple_generator.py "文本描述"`
- 交互模式: `python simple_generator.py --interactive`

**作用**: 使用本地Ollama模型生成场景图，支持单次生成和交互式生成模式

## deepseek_v3_scenegraph_generator.py
**使用方法**: `python deepseek_v3_scenegraph_generator.py <input_csv_file> [output_csv_file]`  
**作用**: 使用DeepSeek R1 API批量处理CSV文件中的文本，生成对应的场景图数据

## gemini_2.0_flash_scenegraph_generator.py
**使用方法**: `python gemini_2.0_flash_scenegraph_generator.py <input_csv_file> [output_csv_file]`  
**作用**: 使用Google Gemini 2.0 Flash API批量处理CSV文件中的文本，生成对应的场景图数据

## example.env
**使用方法**: 复制为`.env`文件并填入API密钥  
**作用**: 提供环境变量配置模板，包含GEMINI_API_KEY和DEEPSEEK_API_KEY的配置示例