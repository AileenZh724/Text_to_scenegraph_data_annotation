"""Color enrichment service for enhancing text descriptions with color information.

Provides functionality to:
- Standardize color mentions in text
- Supplement missing color information using LLM
- Enrich scene graph nodes with color attributes
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd

from ..core.models import GenerationConfig
from ..io.csv_io import CSVReader, CSVWriter
from ..providers.base import BaseGenerator


class ColorEnricherService:
    """Service for enriching text and scene graphs with color information."""

    BASIC_COLORS = [
        "red", "blue", "green", "yellow", "black", 
        "white", "brown", "gray", "orange", "purple", "pink"
    ]

    def __init__(self):
        """Initialize the color enricher service."""
        self.csv_reader = CSVReader()
        self.csv_writer = CSVWriter()

    def standardize_color(self, text: str) -> str:
        """Standardize color mention in text to basic color.
        
        Args:
            text: Input text that may contain color mentions
            
        Returns:
            Standardized color name or 'gray' as default
        """
        text = text.lower()
        for color in self.BASIC_COLORS:
            if color in text:
                return color
        return "gray"  # Default color

    def enrich_colors(
        self,
        input_file: Path,
        output_file: Path,
        provider: BaseGenerator,
        input_column: str = "input",
        enriched_column: str = "enriched_text",
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """Enrich text descriptions with color information using LLM.
        
        Args:
            input_file: Input CSV file path
            output_file: Output CSV file path
            provider: LLM provider instance
            input_column: Name of input text column
            enriched_column: Name of output enriched text column
            create_backup: Whether to create backup of input file
            
        Returns:
            Processing results including statistics
        """
        # Read input CSV
        df = self.csv_reader.read_csv(input_file)
        
        if input_column not in df.columns:
            raise ValueError(f"Input column '{input_column}' not found in CSV")
            
        # Create backup if requested
        if create_backup:
            backup_file = self.csv_writer.create_backup(input_file)
            
        # Process each text
        enriched_texts = []
        processed = 0
        failed = 0
        
        for text in df[input_column]:
            try:
                # Call LLM to enrich text with colors
                enriched = provider.generate_with_colors(text)
                enriched_texts.append(enriched)
                processed += 1
            except Exception as e:
                enriched_texts.append(text)  # Keep original on failure
                failed += 1
                
        # Add enriched texts to dataframe
        df[enriched_column] = enriched_texts
        
        # Save results
        self.csv_writer.write_csv(df, output_file)
        
        return {
            "success": True,
            "processed_rows": processed,
            "failed_rows": failed,
            "backup_file": backup_file if create_backup else None
        }

    def extract_colors(self, text: str) -> List[str]:
        """Extract color mentions from text.
        
        Args:
            text: Input text
            
        Returns:
            List of found color names
        """
        text = text.lower()
        return [color for color in self.BASIC_COLORS if color in text]