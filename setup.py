from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Default requirements if file not found
default_requirements = [
    "flask==2.2.3",
    "pdfplumber==0.10.2",
    "python-dotenv==1.0.0",
    "requests==2.31.0",
    "pypdf==3.16.0",
    "python-multipart==0.0.6",
    "tqdm==4.66.1",
    "docling>=2.25.0",
    "Werkzeug==2.2.3",
    "Jinja2==3.1.2",
    "itsdangerous==2.1.2",
    "click==8.1.3",
    "MarkupSafe==2.1.2"
]

# Try to read requirements from file, fallback to defaults if file doesn't exist
try:
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        requirements = fh.read().splitlines()
except FileNotFoundError:
    requirements = default_requirements

setup(
    name="docling-pdf-processor",
    version="0.1.0",
    author="Jamie Roszel",
    author_email="your.email@example.com",
    description="A Flask application for processing PDFs using local Ollama models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jamieroszel22/docling-pdf-processor",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docling-pdf-processor=run:main",
        ],
    },
)
