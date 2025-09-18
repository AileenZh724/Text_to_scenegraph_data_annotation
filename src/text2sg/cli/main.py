"""Main CLI application using Typer.

Provides commands for data processing and scene graph generation.
"""

import sys
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from text2sg.services import (
    FormatterService,
    ExtractorService,
    FixerService,
    PipelineService,
    ColorEnricherService
)
from text2sg.providers import GeminiProvider, DeepseekProvider, OllamaProvider
from text2sg.core.models import GenerationConfig

app = typer.Typer(
    name="text2sg",
    help="Text to Scene Graph generation toolkit",
    add_completion=False
)
console = Console()


@app.command()
def format(
    input_file: Path = typer.Argument(..., help="Input CSV file path"),
    output_file: Path = typer.Argument(..., help="Output CSV file path"),
    input_column: str = typer.Option("input", "--input-col", "-i", help="Input column name"),
    output_column: str = typer.Option("output", "--output-col", "-o", help="Output column name"),
    prompt_template: Optional[str] = typer.Option(None, "--template", "-t", help="Custom prompt template"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of input file")
):
    """Convert CSV data to annotation format.
    
    输出示例:
    ✅ Successfully formatted 50 rows
    📁 Output saved to: output.csv
    💾 Backup created: input.csv.backup_20250912_123456
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Formatting CSV data...", total=None)
            
            formatter = FormatterService()
            result = formatter.format_csv(
                input_file=input_file,
                output_file=output_file,
                input_column=input_column,
                output_column=output_column,
                prompt_template=prompt_template,
                create_backup=backup
            )
            
            progress.update(task, completed=True)
        
        console.print(f"✅ Successfully formatted {result['processed_rows']} rows")
        console.print(f"📁 Output saved to: {output_file}")
        if backup and result.get('backup_file'):
            console.print(f"💾 Backup created: {result['backup_file']}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def extract(
    input_file: Path = typer.Argument(..., help="Input CSV file path"),
    output_file: Path = typer.Argument(..., help="Output CSV file path"),
    columns: List[str] = typer.Option(["input"], "--column", "-c", help="Columns to extract (can specify multiple)"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of input file")
):
    """Extract specific columns from CSV files.
    
    输出示例:
    ✅ Successfully extracted 1 column(s) from 50 rows
    📁 Output saved to: output.csv
    💾 Backup created: input.csv.backup_20250912_123456
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extracting columns...", total=None)
            
            extractor = ExtractorService()
            if len(columns) == 1:
                result = extractor.extract_input_column(
                    input_file=input_file,
                    output_file=output_file,
                    input_column=columns[0],
                    create_backup=backup
                )
            else:
                result = extractor.extract_columns(
                    input_file=input_file,
                    output_file=output_file,
                    columns=columns,
                    create_backup=backup
                )
            
            progress.update(task, completed=True)
        
        console.print(f"✅ Successfully extracted {len(columns)} column(s) from {result['processed_rows']} rows")
        console.print(f"📁 Output saved to: {output_file}")
        if backup and result.get('backup_file'):
            console.print(f"💾 Backup created: {result['backup_file']}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def fix(
    input_file: Path = typer.Argument(..., help="Input CSV file path"),
    output_file: Optional[Path] = typer.Argument(None, help="Output CSV file path (default: input_file_fixed.csv)"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of input file"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate CSV structure after fixing")
):
    """Fix common CSV issues like multiline JSON.
    
    输出示例:
    🔍 Analyzing CSV structure...
    🔧 Fixed 5 multiline JSON issues
    ✅ Successfully fixed all issues in 50 rows
    📁 Output saved to: input_fixed.csv
    💾 Backup created: input.csv.backup_20250912_123456
    """
    try:
        if output_file is None:
            output_file = input_file.parent / f"{input_file.stem}_fixed{input_file.suffix}"
            
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fixing CSV issues...", total=None)
            
            fixer = FixerService()
            result = fixer.fix_multiline_json(
                input_file=input_file,
                output_file=output_file,
                create_backup=backup,
                validate_after_fix=validate
            )
            
            progress.update(task, completed=True)
        
        console.print(f"✅ Successfully fixed {result['lines_processed']} lines")
        console.print(f"🔧 Fixed {result['json_blocks_fixed']} JSON blocks")
        console.print(f"📁 Output saved to: {output_file}")
        if backup and result.get('backup_file'):
            console.print(f"💾 Backup created: {result['backup_file']}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def generate(
    input_file: Path = typer.Argument(..., help="Input CSV file with text descriptions"),
    output_file: Path = typer.Argument(..., help="Output CSV file with scene graphs"),
    provider: str = typer.Option("gemini", "--provider", "-p", help="Scene graph generation provider (gemini, deepseek, ollama)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for the provider"),
    input_column: str = typer.Option("input", "--input-col", "-i", help="Input column name"),
    output_column: str = typer.Option("scene_graph", "--output-col", "-o", help="Output column name"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Batch size for processing"),
    max_retries: int = typer.Option(3, "--max-retries", help="Maximum number of retries per request"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of input file")
):
    """Generate scene graphs from text descriptions.
    
    输出示例:
    🤖 Using Gemini provider
    🔄 Processing batch 1/5 (10 items)
    ✓ Processed 10 items
    🔄 Processing batch 2/5 (10 items)
    ✓ Processed 20 items
    ...
    ✅ Successfully generated scene graphs for 50 rows
    📁 Output saved to: output.csv
    💾 Backup created: input.csv.backup_20250912_123456
    """
    try:
        # Initialize provider
        provider = provider.lower()
        if provider == "gemini":
            if not api_key:
                api_key = typer.prompt("Enter Gemini API key", hide_input=True)
            provider_class = GeminiProvider
        elif provider == "deepseek":
            if not api_key:
                api_key = typer.prompt("Enter DeepSeek API key", hide_input=True)
            provider_class = DeepseekProvider
        elif provider == "ollama":
            # Ollama uses URL instead of API key
            api_key = api_key or "http://localhost:11434"
            provider_class = OllamaProvider
        else:
            console.print(f"❌ Unsupported provider: {provider}", style="red")
            console.print("Supported providers: gemini, deepseek, ollama", style="yellow")
            raise typer.Exit(1)
        
        config = GenerationConfig(
            api_key=api_key,
            max_retries=max_retries,
            batch_size=batch_size
        )
        provider_instance = provider_class(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating scene graphs...", total=None)
            
            pipeline = PipelineService()
            result = pipeline.generate_scene_graphs(
                input_file=input_file,
                output_file=output_file,
                provider=provider_instance,
                input_column=input_column,
                output_column=output_column,
                create_backup=backup
            )
            
            progress.update(task, completed=True)
        
        console.print(f"✅ Successfully generated scene graphs for {result['processed_rows']} rows")
        console.print(f"📊 Success rate: {result['success_rate']:.1%}")
        console.print(f"📁 Output saved to: {output_file}")
        if backup and result.get('backup_file'):
            console.print(f"💾 Backup created: {result['backup_file']}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def pipeline(
    input_file: Path = typer.Argument(..., help="Input CSV file path"),
    output_dir: Path = typer.Argument(..., help="Output directory for results"),
    provider: str = typer.Option("gemini", "--provider", "-p", help="Scene graph generation provider (gemini, deepseek, ollama)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for the provider"),
    input_column: str = typer.Option("input", "--input-col", "-i", help="Input column name"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Batch size for processing"),
    max_retries: int = typer.Option(3, "--max-retries", help="Maximum number of retries per request"),
    skip_preparation: bool = typer.Option(False, "--skip-prep", help="Skip data preparation steps"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup files")
):
    """Run complete scene graph generation pipeline.
    
    输出示例:
    🚀 Starting scene graph generation pipeline
    🤖 Using Gemini provider
    
    📋 Step 1/4: Preparing data
    ✓ Data preparation complete
    
    📊 Step 2/4: Generating scene graphs
    🔄 Processing batch 1/5 (10 items)
    ✓ Processed 10 items
    ...
    ✓ Scene graph generation complete
    
    🎨 Step 3/4: Enriching colors
    ✓ Color enrichment complete
    
    📈 Step 4/4: Generating statistics
    ✓ Statistics generation complete
    
    ✅ Pipeline completed successfully
    📁 Results saved to: /path/to/output_dir/
    """
    try:
        # Initialize provider
        provider = provider.lower()
        if provider == "gemini":
            if not api_key:
                api_key = typer.prompt("Enter Gemini API key", hide_input=True)
            provider_class = GeminiProvider
        elif provider == "deepseek":
            if not api_key:
                api_key = typer.prompt("Enter DeepSeek API key", hide_input=True)
            provider_class = DeepseekProvider
        elif provider == "ollama":
            # Ollama uses URL instead of API key
            api_key = api_key or "http://localhost:11434"
            provider_class = OllamaProvider
        else:
            console.print(f"❌ Unsupported provider: {provider}", style="red")
            console.print("Supported providers: gemini, deepseek, ollama", style="yellow")
            raise typer.Exit(1)
        
        config = GenerationConfig(
            api_key=api_key,
            max_retries=max_retries,
            batch_size=batch_size
        )
        provider_instance = provider_class(config)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running pipeline...", total=None)
            
            pipeline_service = PipelineService()
            result = pipeline_service.run_complete_pipeline(
                input_file=input_file,
                output_dir=output_dir,
                provider=provider_instance,
                input_column=input_column,
                skip_data_preparation=skip_preparation,
                create_backups=backup
            )
            
            progress.update(task, completed=True)
        
        # Display results
        console.print("\n🎉 Pipeline completed successfully!")
        
        table = Table(title="Pipeline Results")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        for step, details in result['steps'].items():
            status = "✅ Success" if details['success'] else "❌ Failed"
            info = f"Processed: {details.get('processed_rows', 'N/A')}"
            if 'output_file' in details:
                info += f"\nOutput: {details['output_file']}"
            table.add_row(step.replace('_', ' ').title(), status, info)
        
        console.print(table)
        console.print(f"\n📁 All outputs saved to: {output_dir}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def textcolorizer(
    input_file: Path = typer.Argument(..., help="Input CSV file path"),
    output_dir: Path = typer.Argument(..., help="Output directory for results"),
    provider: str = typer.Option("deepseek", "--provider", "-p", help="Provider for color enrichment (deepseek, gemini, ollama)"),
    api_key: Optional[str] = typer.Option(None, "--api-key", help="API key for the provider"),
    input_column: str = typer.Option("input", "--input-col", "-i", help="Input column name"),
    output_column: str = typer.Option("enriched_text", "--output-col", "-o", help="Output column name"),
    batch_size: int = typer.Option(10, "--batch-size", "-b", help="Batch size for processing"),
    max_retries: int = typer.Option(3, "--max-retries", help="Maximum number of retries per request"),
    backup: bool = typer.Option(True, "--backup/--no-backup", help="Create backup of input file")
):
    """Enrich text descriptions with color information.
    
    输出示例:
    🎨 Starting text colorization process
    🤖 Using DeepSeek provider
    
    🔄 Processing batch 1/5 (10 items)
    ✓ Processed 10 items
    🔄 Processing batch 2/5 (10 items)
    ✓ Processed 20 items
    ...
    
    🔍 Extracting color information
    ✓ Found 127 color mentions across all texts
    
    ✅ Successfully enriched 50 text descriptions with color information
    📁 Output saved to: /path/to/output_dir/enriched_data.csv
    💾 Backup created: input.csv.backup_20250912_123456
    """
    try:
        # Initialize provider
        provider = provider.lower()
        if provider == "gemini":
            if not api_key:
                api_key = typer.prompt("Enter Gemini API key", hide_input=True)
            provider_class = GeminiProvider
        elif provider == "deepseek":
            if not api_key:
                api_key = typer.prompt("Enter DeepSeek API key", hide_input=True)
            provider_class = DeepseekProvider
        elif provider == "ollama":
            # Ollama uses URL instead of API key
            api_key = api_key or "http://localhost:11434"
            provider_class = OllamaProvider
        else:
            console.print(f"❌ Unsupported provider: {provider}", style="red")
            console.print("Supported providers: deepseek, gemini, ollama", style="yellow")
            raise typer.Exit(1)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{input_file.stem}_enriched{input_file.suffix}"
        
        config = GenerationConfig(
            api_key=api_key,
            max_retries=max_retries,
            batch_size=batch_size
        )
        provider_instance = provider_class(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Enriching text with colors...", total=None)
            
            enricher = ColorEnricherService()
            result = enricher.enrich_colors(
                input_file=input_file,
                output_file=output_file,
                provider=provider_instance,
                input_column=input_column,
                enriched_column=output_column,
                create_backup=backup
            )
            
            progress.update(task, completed=True)
        
        console.print(f"✅ Successfully processed {result['processed_rows']} rows")
        if result['failed_rows'] > 0:
            console.print(f"⚠️ Failed to process {result['failed_rows']} rows", style="yellow")
        console.print(f"📁 Output saved to: {output_file}")
        if backup and result.get('backup_file'):
            console.print(f"💾 Backup created: {result['backup_file']}")
            
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information.
    
    输出示例:
    Text2SG v1.0.0
    Scene Graph Generation Toolkit
    """
    console.print("Text2SG v1.0.0")
    console.print("Scene Graph Generation Toolkit")


if __name__ == "__main__":
    app()