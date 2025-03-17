# Team Guide: Docling PDF Processor with Ollama

This guide explains how to set up and use the Docling PDF Processor for team members.

## Why Use This Tool?

This tool makes it easy to extract text and structure from PDFs for use in RAG (Retrieval Augmented Generation) applications. Key benefits:

- **Local Processing**: All processing happens on your machine - no API keys, no data sent to external services
- **Fast Text Extraction**: Extract text while preserving structure from large documents in seconds
- **Optional Deep Analysis**: Enable vision model processing for complex documents when needed
- **Multiple Output Formats**: Generate TXT, JSON, and Markdown for different use cases
- **Open WebUI Ready**: Export processed documents directly for use with Open WebUI

## Installation Options

### Option 1: Direct Installation (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/jamieroszel22/docling-pdf-processor.git
   cd docling-pdf-processor
   ```

2. Install dependencies:
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

### Option 2: Install as Python Package

1. Clone the repository:
   ```bash
   git clone https://github.com/jamieroszel22/docling-pdf-processor.git
   cd docling-pdf-processor
   ```

2. Install as a local package:
   ```bash
   pip install -e .
   ```

3. Run using the entry point:
   ```bash
   docling-pdf-processor
   ```

## Using the Web Interface

1. Open your browser at http://localhost:5001
2. Select a model from the dropdown (vision models provide better analysis but are slower)
3. Upload PDFs individually or in batch
4. Process the documents
5. Download or export the processed files

## Performance Tips

### When to Use Vision Processing

Vision processing is useful for:
- Scanned documents
- Complex layouts with tables and figures
- Documents with mathematical formulas
- PDFs where text extraction is difficult

To enable vision processing, check the "Use Vision Model" option when uploading.

### Optimizing Processing Speed

For large batch jobs:
1. Disable vision processing unless absolutely necessary
2. Adjust worker threads based on your machine's capabilities (default: 4)
3. Use smaller, more specific documents rather than large, general ones

## Using the Processed Files

### Text Files (.txt)
- Best for simple RAG systems
- Contains plain text with minimal formatting
- Fast to process and search

### JSON Files (.json)
- Contains structured data with page information
- Includes vision analysis when enabled
- Good for applications that need metadata

### Markdown Files (.md)
- Preserves basic formatting
- Good middle ground between plain text and HTML
- Works well with most markdown-compatible systems

## Integrating with Open WebUI

1. Process your documents
2. Select the documents you want to use in Open WebUI
3. Click "Export for Open WebUI"
4. Download the export package
5. In Open WebUI:
   - Go to Collections
   - Create a new collection or select an existing one
   - Import the downloaded ZIP file
   - Configure chunking settings as needed

## Advanced Usage

### Command Line Processing

For batch processing without the web interface, you can import the processor in your Python scripts:

```python
from pathlib import Path
from app.utils.pdf_processor_ollama import process_pdf, batch_process_pdfs

# Process a single PDF
output_files = process_pdf(
    pdf_path=Path("path/to/document.pdf"),
    output_dir=Path("path/to/output"),
    model_name="granite3.2-vision:latest",
    use_vision=False,  # Set to True for vision processing
    max_workers=4
)

# Process multiple PDFs
pdf_paths = [Path("doc1.pdf"), Path("doc2.pdf")]
results = batch_process_pdfs(
    pdf_paths=pdf_paths,
    output_dir=Path("path/to/output"),
    model_name="granite3.2-vision:latest",
    use_vision=False,
    max_workers=4
)
```

## Troubleshooting

### Common Issues

- **Port in Use**: If port 5001 is already in use, specify a different port using `PORT=8080 python run.py`
- **Missing PyMuPDF**: If you see "ModuleNotFoundError: No module named 'fitz'", run `pip install PyMuPDF`
- **Ollama Connection Error**: Make sure Ollama is running at http://localhost:11434
- **Slow Processing**: If vision processing is slow, try a smaller document or disable vision processing
- **Missing Models**: If a model is missing in the dropdown, make sure it's installed in Ollama

### Getting Help

If you encounter issues not covered here, please:
1. Check the logs in the terminal running the application
2. Review the [GitHub README](https://github.com/jamieroszel22/docling-pdf-processor)
3. Open an issue on GitHub for persistent problems
