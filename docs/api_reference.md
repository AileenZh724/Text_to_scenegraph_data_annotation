# Text2SG API 参考文档

本文档提供了 Text2SG 工具的完整 API 参考，包括所有类、方法和函数的详细说明。

## 核心模型 (Core Models)

### SceneGraph

场景图数据模型，表示文本对应的结构化场景信息。

```python
from text2sg.core.models import SceneGraph

class SceneGraph:
    """场景图数据模型"""
    
    def __init__(self, objects: List[Dict], relationships: List[Dict] = None):
        """初始化场景图
        
        Args:
            objects: 场景中的对象列表
            relationships: 对象间的关系列表（可选）
        """
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SceneGraph':
        """从字典创建场景图"""
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SceneGraph':
        """从JSON字符串创建场景图"""
    
    def validate(self) -> bool:
        """验证场景图数据的有效性"""
```

### AnnotatedRow

标注数据行模型，表示单行文本-场景图对应关系。

```python
from text2sg.core.models import AnnotatedRow

class AnnotatedRow:
    """标注数据行模型"""
    
    def __init__(self, text: str, scenegraph: Union[str, Dict, SceneGraph], 
                 metadata: Dict = None):
        """初始化标注行
        
        Args:
            text: 文本描述
            scenegraph: 场景图数据
            metadata: 额外元数据（可选）
        """
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
    
    def validate(self) -> bool:
        """验证数据有效性"""
    
    @property
    def scenegraph_dict(self) -> Dict:
        """获取场景图的字典表示"""
```

### PipelineConfig

流水线配置模型，定义处理流程的各种参数。

```python
from text2sg.core.models import PipelineConfig

class PipelineConfig:
    """流水线配置模型"""
    
    def __init__(self,
                 text_column: str = 'text',
                 scenegraph_column: str = 'scenegraph',
                 enable_backup: bool = True,
                 backup_suffix: str = '_backup',
                 batch_size: int = 100,
                 max_retries: int = 3,
                 enable_validation: bool = True,
                 output_format: str = 'csv'):
        """初始化配置
        
        Args:
            text_column: 文本列名
            scenegraph_column: 场景图列名
            enable_backup: 是否启用备份
            backup_suffix: 备份文件后缀
            batch_size: 批处理大小
            max_retries: 最大重试次数
            enable_validation: 是否启用验证
            output_format: 输出格式
        """
```

## 服务类 (Services)

### FormatterService

CSV格式化服务，负责标准化CSV文件格式。

```python
from text2sg.services import FormatterService

class FormatterService:
    """CSV格式化服务"""
    
    def __init__(self, config: PipelineConfig = None):
        """初始化格式化服务
        
        Args:
            config: 流水线配置（可选）
        """
    
    def format_csv(self, input_file: str, output_file: str, 
                   text_column: str = None, scenegraph_column: str = None) -> ProcessingResult:
        """格式化CSV文件
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            text_column: 文本列名（可选）
            scenegraph_column: 场景图列名（可选）
            
        Returns:
            ProcessingResult: 处理结果
        """
    
    def format_batch(self, file_pairs: List[Tuple[str, str]]) -> List[ProcessingResult]:
        """批量格式化多个文件
        
        Args:
            file_pairs: (输入文件, 输出文件) 对列表
            
        Returns:
            List[ProcessingResult]: 处理结果列表
        """
    
    def validate_format(self, file_path: str) -> ValidationResult:
        """验证文件格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            ValidationResult: 验证结果
        """
```

### ExtractorService

列提取服务，从CSV文件中提取指定列。

```python
from text2sg.services import ExtractorService

class ExtractorService:
    """列提取服务"""
    
    def __init__(self, config: PipelineConfig = None):
        """初始化提取服务"""
    
    def extract_columns(self, input_file: str, output_file: str, 
                       columns: List[str], preserve_order: bool = True) -> ProcessingResult:
        """提取指定列
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            columns: 要提取的列名列表
            preserve_order: 是否保持原始顺序
            
        Returns:
            ProcessingResult: 处理结果
        """
    
    def get_available_columns(self, file_path: str) -> List[str]:
        """获取文件中可用的列名
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[str]: 列名列表
        """
    
    def extract_sample(self, input_file: str, sample_size: int = 10) -> List[Dict]:
        """提取样本数据
        
        Args:
            input_file: 输入文件路径
            sample_size: 样本大小
            
        Returns:
            List[Dict]: 样本数据列表
        """
```

### FixerService

JSON修复服务，修复CSV中的JSON格式问题。

```python
from text2sg.services import FixerService

class FixerService:
    """JSON修复服务"""
    
    def __init__(self, config: PipelineConfig = None):
        """初始化修复服务"""
    
    def fix_json(self, input_file: str, output_file: str, 
                json_column: str = 'scenegraph') -> ProcessingResult:
        """修复JSON格式问题
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            json_column: JSON列名
            
        Returns:
            ProcessingResult: 处理结果
        """
    
    def fix_json_string(self, json_str: str) -> Tuple[str, bool]:
        """修复单个JSON字符串
        
        Args:
            json_str: 待修复的JSON字符串
            
        Returns:
            Tuple[str, bool]: (修复后的JSON, 是否成功修复)
        """
    
    def validate_json(self, json_str: str) -> bool:
        """验证JSON字符串有效性
        
        Args:
            json_str: JSON字符串
            
        Returns:
            bool: 是否有效
        """
    
    def get_fix_strategies(self) -> List[str]:
        """获取可用的修复策略
        
        Returns:
            List[str]: 修复策略列表
        """
```

### PipelineService

流水线服务，协调整个数据处理流程。

```python
from text2sg.services import PipelineService

class PipelineService:
    """流水线服务"""
    
    def __init__(self, config: PipelineConfig = None):
        """初始化流水线服务"""
    
    def run_pipeline(self, input_file: str, output_file: str) -> ProcessingResult:
        """运行完整流水线
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            
        Returns:
            ProcessingResult: 处理结果
        """
    
    def run_custom_pipeline(self, input_file: str, output_file: str, 
                           steps: List[str]) -> ProcessingResult:
        """运行自定义流水线
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            steps: 处理步骤列表
            
        Returns:
            ProcessingResult: 处理结果
        """
    
    def validate_pipeline(self, input_file: str) -> ValidationResult:
        """验证流水线输入
        
        Args:
            input_file: 输入文件路径
            
        Returns:
            ValidationResult: 验证结果
        """
    
    def get_pipeline_status(self) -> Dict:
        """获取流水线状态
        
        Returns:
            Dict: 状态信息
        """
```

## 结果模型 (Result Models)

### ProcessingResult

处理结果模型，包含处理统计信息。

```python
from text2sg.core.models import ProcessingResult

class ProcessingResult:
    """处理结果模型"""
    
    def __init__(self):
        self.total_rows: int = 0
        self.successful_rows: int = 0
        self.failed_rows: int = 0
        self.execution_time: float = 0.0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metadata: Dict = {}
    
    @property
    def success_rate(self) -> float:
        """成功率"""
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
```

### ValidationResult

验证结果模型，包含数据验证信息。

```python
from text2sg.core.models import ValidationResult

class ValidationResult:
    """验证结果模型"""
    
    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.checked_items: List[str] = []
        self.metadata: Dict = {}
    
    def add_error(self, error: str):
        """添加错误"""
    
    def add_warning(self, warning: str):
        """添加警告"""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
```

## 便利函数 (Convenience Functions)

### 格式化函数

```python
from text2sg import format_csv_to_annotation

def format_csv_to_annotation(input_file: str, output_file: str, 
                            text_column: str = 'text', 
                            scenegraph_column: str = 'scenegraph',
                            **kwargs) -> ProcessingResult:
    """格式化CSV为标注格式
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        text_column: 文本列名
        scenegraph_column: 场景图列名
        **kwargs: 其他配置参数
        
    Returns:
        ProcessingResult: 处理结果
    """
```

### 提取函数

```python
from text2sg import extract_columns_from_csv

def extract_columns_from_csv(input_file: str, output_file: str, 
                            columns: List[str], 
                            preserve_order: bool = True,
                            **kwargs) -> ProcessingResult:
    """从CSV提取指定列
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        columns: 要提取的列名列表
        preserve_order: 是否保持顺序
        **kwargs: 其他配置参数
        
    Returns:
        ProcessingResult: 处理结果
    """
```

### 修复函数

```python
from text2sg import fix_multiline_json_in_csv

def fix_multiline_json_in_csv(input_file: str, output_file: str, 
                              json_column: str = 'scenegraph',
                              **kwargs) -> ProcessingResult:
    """修复CSV中的多行JSON
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        json_column: JSON列名
        **kwargs: 其他配置参数
        
    Returns:
        ProcessingResult: 处理结果
    """
```

### 流水线函数

```python
from text2sg import run_complete_pipeline

def run_complete_pipeline(input_file: str, output_file: str, 
                         config: PipelineConfig = None,
                         **kwargs) -> ProcessingResult:
    """运行完整处理流水线
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        config: 流水线配置
        **kwargs: 其他配置参数
        
    Returns:
        ProcessingResult: 处理结果
    """
```

## 异常类 (Exceptions)

### 基础异常

```python
from text2sg.core.exceptions import Text2SGError

class Text2SGError(Exception):
    """Text2SG基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, 
                 context: Dict = None):
        """初始化异常
        
        Args:
            message: 错误消息
            error_code: 错误代码
            context: 错误上下文
        """
```

### 具体异常类

```python
from text2sg.core.exceptions import (
    ConfigurationError,
    ValidationError,
    ProcessingError,
    FileError,
    JSONError
)

class ConfigurationError(Text2SGError):
    """配置错误"""

class ValidationError(Text2SGError):
    """验证错误"""

class ProcessingError(Text2SGError):
    """处理错误"""

class FileError(Text2SGError):
    """文件错误"""

class JSONError(Text2SGError):
    """JSON错误"""
```

## 日志配置 (Logging)

### 日志设置

```python
from text2sg.config.logging_config import setup_logging, get_logger

def setup_logging(level: str = 'INFO', 
                 log_file: str = None, 
                 enable_rich: bool = True,
                 format_style: str = 'structured') -> None:
    """设置日志配置
    
    Args:
        level: 日志级别
        log_file: 日志文件路径
        enable_rich: 是否启用Rich输出
        format_style: 格式样式
    """

def get_logger(name: str = None) -> logging.Logger:
    """获取日志记录器
    
    Args:
        name: 记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
```

## CLI接口 (Command Line Interface)

### 主命令

```bash
# 查看版本
text2sg --version

# 查看帮助
text2sg --help
```

### 子命令

```bash
# 格式化命令
text2sg format INPUT OUTPUT [OPTIONS]

# 提取命令
text2sg extract INPUT OUTPUT [OPTIONS]

# 修复命令
text2sg fix INPUT OUTPUT [OPTIONS]

# 流水线命令
text2sg pipeline INPUT OUTPUT [OPTIONS]
```

### 通用选项

```bash
--text-column TEXT          文本列名 [默认: text]
--scenegraph-column TEXT    场景图列名 [默认: scenegraph]
--backup / --no-backup      是否创建备份 [默认: backup]
--verbose / --quiet         详细输出 [默认: quiet]
--batch-size INTEGER        批处理大小 [默认: 100]
--max-retries INTEGER       最大重试次数 [默认: 3]
```

## 配置文件 (Configuration)

### 配置文件格式

```yaml
# text2sg.yaml
default:
  text_column: "text"
  scenegraph_column: "scenegraph"
  enable_backup: true
  backup_suffix: "_backup"
  batch_size: 100
  max_retries: 3
  enable_validation: true
  output_format: "csv"

logging:
  level: "INFO"
  enable_rich: true
  format_style: "structured"
  log_file: null

processing:
  parallel_workers: 4
  memory_limit: "1GB"
  temp_directory: "/tmp/text2sg"
```

### 加载配置

```python
from text2sg.config import load_config

# 从文件加载配置
config = load_config('text2sg.yaml')

# 从环境变量加载配置
config = load_config(source='env')

# 使用默认配置
config = load_config()
```

## 扩展接口 (Extension Interface)

### 自定义处理器

```python
from text2sg.core.base import BaseProcessor

class CustomProcessor(BaseProcessor):
    """自定义处理器"""
    
    def process(self, data: Any) -> Any:
        """处理数据"""
        # 实现自定义处理逻辑
        pass
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        # 实现自定义验证逻辑
        pass
```

### 插件系统

```python
from text2sg.plugins import register_plugin

@register_plugin('custom_formatter')
class CustomFormatterPlugin:
    """自定义格式化插件"""
    
    def format(self, data: str) -> str:
        """格式化数据"""
        # 实现自定义格式化逻辑
        pass
```

## 性能监控 (Performance Monitoring)

### 性能指标

```python
from text2sg.monitoring import get_performance_metrics

# 获取性能指标
metrics = get_performance_metrics()
print(f"处理速度: {metrics.rows_per_second} 行/秒")
print(f"内存使用: {metrics.memory_usage_mb} MB")
print(f"CPU使用率: {metrics.cpu_usage_percent}%")
```

### 性能分析

```python
from text2sg.profiling import profile_pipeline

# 分析流水线性能
with profile_pipeline() as profiler:
    result = run_complete_pipeline('input.csv', 'output.csv')

# 查看分析结果
profiler.print_stats()
```

## 测试工具 (Testing Utilities)

### 测试数据生成

```python
from text2sg.testing import generate_test_data

# 生成测试CSV数据
test_data = generate_test_data(
    num_rows=1000,
    text_column='text',
    scenegraph_column='scenegraph'
)

# 保存测试数据
test_data.to_csv('test_data.csv', index=False)
```

### 断言工具

```python
from text2sg.testing import assert_csv_equal, assert_processing_result

# 比较CSV文件
assert_csv_equal('expected.csv', 'actual.csv')

# 验证处理结果
assert_processing_result(result, expected_rows=1000, min_success_rate=0.95)
```

这个API参考文档涵盖了Text2SG工具的所有主要组件和接口。更多详细信息和示例，请参考相应的模块文档和使用示例。