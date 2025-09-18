"""Setup script for Text2SG package."""

import os
import sys
from setuptools import setup, find_packages
from pathlib import Path

# Add src directory to PYTHONPATH
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
os.environ["PYTHONPATH"] = str(src_path)

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

# Read requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    with open(this_directory / "requirements.txt", "r", encoding="utf-8") as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="text2sg",
    version="1.0.0",
    description="Text to Scene Graph generation toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="COMP5703 Team",
    author_email="",
    url="https://github.com/your-org/text2sg",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "typer[all]>=0.9.0",
        "rich>=13.0.0",
        "pandas>=2.0.0",
        "requests>=2.31.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "google-generativeai>=0.3.0",
        "ujson>=5.8.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "text2sg=text2sg.cli.main:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="scene-graph, text-processing, ai, nlp, computer-vision",
    project_urls={
        "Bug Reports": "https://github.com/your-org/text2sg/issues",
        "Source": "https://github.com/your-org/text2sg",
        "Documentation": "https://your-org.github.io/text2sg/",
    },
)