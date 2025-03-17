# Docling PDF Processor

A Flask application for processing PDFs using local Ollama models. It efficiently extracts text, analyzes documents, and prepares them for RAG (Retrieval Augmented Generation) systems.

## Features

- **PDF Processing**: Extract text and structure from PDFs
- **Vision Model Support**: Optional vision model analysis for complex documents
- **Parallel Processing**: Process multiple pages simultaneously for faster results
- **Multiple Output Formats**: Generate TXT, JSON, and Markdown files
- **Open WebUI Integration**: Export processed documents for use with Open WebUI

## Technical Overview

### PDF Processing Technology Stack

The Docling PDF Processor combines several powerful technologies to achieve efficient and accurate PDF extraction:

#### Core Technologies

- **PyMuPDF (fitz)**: Provides the foundation for PDF access and parsing with its robust and fast C++ backend
- **Ollama**: Leverages local large language models for text analysis and vision processing
- **Flask**: Serves the web interface and API endpoints
- **ThreadPoolExecutor**: Enables parallel processing of PDF pages

#### Processing Methodology

The PDF extraction process follows these key steps:

1. **Document Loading**: PyMuPDF loads the PDF document and identifies individual pages
2. **Text Extraction**: For each page:
   - Extract raw text preserving positions and formatting
   - Identify and extract text blocks and paragraphs
   - Preserve document hierarchy (headings, paragraphs, lists)

3. **Parallel Processing**: Multiple pages are processed simultaneously using Python's ThreadPoolExecutor:
   - Each page is processed in a separate thread
   - Results are collected and combined in the correct order
   - Configurable thread count balances speed vs. resource usage

4. **Vision Model Analysis** (optional):
   - For complex documents, vision models can analyze page images
   - Improves extraction of tables, complex layouts, and images
   - Uses Ollama vision models to interpret visual elements
   - Significantly enhances accuracy but increases processing time

5. **Output Generation**:
   - Text files (.txt): Pure text content with minimal formatting
   - JSON files (.json): Structured data with metadata and hierarchy
   - Markdown files (.md): Preserves formatting for human readability
   - Metadata: Information about document structure and processing stats

### Technical Differentiation

What makes the Docling PDF Processor different from other solutions:

- **Local Processing**: All processing happens on your machine with no data sent to external services
- **Model Flexibility**: Works with any Ollama model you have installed
- **Adaptive Processing**: Can use lightweight text-only processing for speed or vision processing for complex documents
- **Optimized Performance**: Parallel processing dramatically reduces processing time for large documents
- **Open WebUI Integration**: Purpose-built for seamless integration with Open WebUI RAG systems

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running locally
- At least one text model in Ollama (vision models optional but recommended)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/jamieroszel22/docling-pdf-processor.git
   cd docling-pdf-processor
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python run.py
   ```

   The application runs on port 5001 by default. To specify a different port:
   ```bash
   PORT=8080 python run.py
   ```

## Usage

1. **Web Interface**
   - Open your browser at http://localhost:5001
   - Select an Ollama model from the dropdown
   - Upload PDFs individually or in batch
   - Choose processing options
   - Download or export the processed files

2. **API**
   - `POST /upload`: Upload and process a single PDF
   - `POST /batch`: Upload and process multiple PDFs
   - `GET /files`: List all processed files
   - `GET /download/<path>`: Download a processed file
   - `GET /openwebui-export`: Export processed files for Open WebUI

## Advanced Options

The PDF processor has several performance optimization options:

- **Vision Processing**: Enable/disable vision model analysis (disabled by default for speed)
- **Parallel Processing**: Adjust the number of worker threads (default: 4)
- **Model Selection**: Choose any text or vision model available in your Ollama installation

## Performance Notes

- Text-only processing is very fast, even for large documents
- Vision model processing provides better analysis for complex layouts but is significantly slower
- Increasing worker threads helps with large documents but may impact system performance

## Troubleshooting

- **Port in Use**: If port 5001 is already in use, specify a different port: `PORT=8080 python run.py`
- **Missing PyMuPDF**: If you see an error about missing `fitz` module, make sure PyMuPDF is installed: `pip install PyMuPDF`
- **Ollama Connection**: Ensure Ollama is running locally at http://localhost:11434

## License

[MIT License](LICENSE)
