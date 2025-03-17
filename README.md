# Docling PDF Processor

A Flask application for processing PDFs using local Ollama models. It efficiently extracts text, analyzes documents, and prepares them for RAG (Retrieval Augmented Generation) systems.

## Features

- **PDF Processing**: Extract text and structure from PDFs
- **Vision Model Support**: Optional vision model analysis for complex documents
- **Parallel Processing**: Process multiple pages simultaneously for faster results
- **Multiple Output Formats**: Generate TXT, JSON, and Markdown files
- **Open WebUI Integration**: Export processed documents for use with Open WebUI

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running locally
- At least one text model in Ollama (vision models optional but recommended)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/docling-pdf-processor.git
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

   To specify a different port (if 5000 is in use):
   ```bash
   PORT=5001 python run.py
   ```

## Usage

1. **Web Interface**
   - Open your browser at http://localhost:5000 (or the port you specified)
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

- **Port in Use**: On macOS, port 5000 is often used by AirPlay. Use `PORT=5001 python run.py` to use a different port.
- **Missing PyMuPDF**: If you see an error about missing `fitz` module, make sure PyMuPDF is installed: `pip install PyMuPDF`
- **Ollama Connection**: Ensure Ollama is running locally at http://localhost:11434

## License

[MIT License](LICENSE)
