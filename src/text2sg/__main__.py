"""Main entry point for Text2SG package.

Allows running the CLI with: python -m text2sg
"""

from .cli.main import app

if __name__ == "__main__":
    app()