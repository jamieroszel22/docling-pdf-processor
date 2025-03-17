import logging
import time
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

# Import Docling for PDF processing using the correct classes
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.settings import settings
from docling.datamodel.document import DoclingDocument
from docling_core.types.doc import ImageRefMode

logger = logging.getLogger(__name__)

class DoclingProcessor:
    """
    A class that handles PDF processing using local Ollama models and Docling for PDF extraction
    """

    def __init__(self, model_name="granite3.2-vision:latest", use_vision=False, max_workers=4):
        """
        Initialize the Docling processor with Ollama integration

        Args:
            model_name: Name of the Ollama model to use
            use_vision: Whether to use vision model for enhanced analysis
            max_workers: Maximum number of parallel workers for processing
        """
        self.model_name = model_name
        self.use_vision = use_vision
        self.max_workers = max_workers
        self.ollama_api = "http://localhost:11434/api"

        # Configure Docling pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.generate_page_images = self.use_vision  # Only generate images if vision is enabled

        # Initialize the document converter
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        # Verify Ollama is running and the model is available
        try:
            response = requests.get(f"{self.ollama_api}/tags")
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                if self.model_name not in models:
                    logger.warning(f"Model {self.model_name} not found in Ollama. Available models: {models}")
                    if models:
                        self.model_name = models[0]  # Use the first available model
                        logger.info(f"Using model {self.model_name} instead")
            else:
                logger.error("Failed to get models from Ollama API")
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")

    def _process_page(self, page_data, page_num: int, doc_output_dir: Path) -> Dict:
        """
        Process a single page of the PDF

        Args:
            page_data: Page data from Docling document
            page_num: Page number (1-based)
            doc_output_dir: Output directory for the document

        Returns:
            Dictionary containing page data
        """
        logger.info(f"Processing page {page_num}/{self.total_pages}")

        # Extract text from the page
        page_text = ""
        if hasattr(page_data, "texts"):
            # Collect text from all text elements on the page
            for text_element in page_data.texts:
                if hasattr(text_element, "content"):
                    page_text += text_element.content + " "

        page_data = {
            "page_number": page_num,
            "text": page_text.strip(),
            "elements": []
        }

        # If using vision model, process the page image
        if self.use_vision:
            try:
                # Look for page image
                img_path = doc_output_dir / f"page_{page_num}.png"

                if not img_path.exists():
                    # If image doesn't exist, try to get it from Docling
                    # This part depends on how Docling saves page images
                    pass

                if img_path.exists():
                    # Process with Ollama vision model
                    vision_text = self._process_image_with_ollama(img_path)
                    logger.info(f"Completed vision analysis for page {page_num}")
                    page_data["vision_analysis"] = vision_text
            except Exception as e:
                logger.error(f"Error processing page image: {e}")

        return page_data

    def process_single_pdf(self, pdf_path: Path, output_dir: Path) -> List[str]:
        """
        Process a single PDF using Docling and Ollama

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory where the processed files will be saved

        Returns:
            List of output file paths
        """
        logger.info(f"Starting PDF processing: {pdf_path}")
        logger.info(f"Using model: {self.model_name}")
        logger.info(f"Vision processing: {'enabled' if self.use_vision else 'disabled'}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        start_time = time.time()

        # Create a subdirectory for this document
        doc_filename = pdf_path.stem
        doc_output_dir = output_dir / doc_filename
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {doc_output_dir}")

        output_files = []

        try:
            # Convert the PDF with Docling
            logger.info("Converting PDF document with Docling...")
            conv_result = self.doc_converter.convert(pdf_path, raises_on_error=True)

            # Check if conversion was successful
            if conv_result.status != ConversionStatus.SUCCESS:
                error_messages = [e.error_message for e in conv_result.errors]
                raise Exception(f"PDF conversion failed: {', '.join(error_messages)}")

            # Get the Docling document
            docling_document = conv_result.document
            self.total_pages = len(docling_document.pages)
            logger.info(f"PDF converted successfully. Total pages: {self.total_pages}")

            # Process pages in parallel
            logger.info(f"Processing pages with {self.max_workers} workers...")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Process all pages for further analysis
                future_to_page = {}
                for page_num, (page_idx, page_data) in enumerate(docling_document.pages.items(), 1):
                    future = executor.submit(self._process_page, page_data, page_num, doc_output_dir)
                    future_to_page[future] = page_num

                # Collect results as they complete
                json_content = {"pages": []}
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        page_data = future.result()
                        json_content["pages"].append(page_data)
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")

            # Sort pages by page number
            json_content["pages"].sort(key=lambda x: x["page_number"])

            # Combine text content
            text_content = "\n".join(
                f"--- Page {page['page_number']} ---\n{page['text']}"
                for page in json_content["pages"]
            )

            logger.info("Saving processed files...")

            # Save the extracted text
            txt_path = doc_output_dir / f"{doc_filename}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            output_files.append(str(txt_path))
            logger.info(f"Saved text file: {txt_path}")

            # Save as JSON
            json_path = doc_output_dir / f"{doc_filename}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2)
            output_files.append(str(json_path))
            logger.info(f"Saved JSON file: {json_path}")

            # Save the Docling document as Markdown
            md_path = doc_output_dir / f"{doc_filename}.md"
            docling_document.save_as_markdown(
                md_path,
                image_mode=ImageRefMode.PLACEHOLDER
            )
            output_files.append(str(md_path))
            logger.info(f"Saved markdown file: {md_path}")

            # Export metadata about the document
            logger.info("Generating metadata...")
            metadata = {
                "filename": doc_filename,
                "processed_time": time.time(),
                "status": "success",
                "model_used": self.model_name,
                "vision_processing": self.use_vision,
                "page_count": self.total_pages,
                "output_files": [os.path.basename(f) for f in output_files]
            }

            metadata_path = doc_output_dir / f"{doc_filename}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata file: {metadata_path}")

            output_files.append(str(metadata_path))

            end_time = time.time() - start_time
            logger.info(f"PDF processing complete in {end_time:.2f} seconds.")
            logger.info(f"Generated {len(output_files)} output files")

            return output_files
        except Exception as e:
            logger.error(f"Error processing PDF: {e}", exc_info=True)
            raise

    def process_batch(self, pdf_paths: List[Path], output_dir: Path) -> Dict[str, List[str]]:
        """
        Process multiple PDFs as a batch

        Args:
            pdf_paths: List of paths to PDF files
            output_dir: Directory where the processed files will be saved

        Returns:
            Dictionary mapping input file names to lists of output file paths
        """
        logger.info(f"Processing batch of {len(pdf_paths)} PDFs")

        results = {}

        for pdf_path in pdf_paths:
            try:
                output_files = self.process_single_pdf(pdf_path, output_dir)
                results[pdf_path.name] = output_files
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                results[pdf_path.name] = []

        return results

    def _process_image_with_ollama(self, image_path: Path) -> str:
        """
        Process an image with an Ollama vision model

        Args:
            image_path: Path to the image file

        Returns:
            Text description or analysis of the image
        """
        try:
            # Convert image to base64
            import base64
            with open(image_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_api}/generate",
                json={
                    "model": self.model_name,
                    "prompt": "Please analyze this document image and extract the text content, tables, and any other visible information. Provide a comprehensive description of the layout and content.",
                    "images": [base64_image],
                    "stream": False
                }
            )

            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                logger.error(f"Error from Ollama API: {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Error calling Ollama vision model: {e}")
            return ""

# Simplified interface functions
def process_pdf(pdf_path: Path, output_dir: Path, model_name="granite3.2-vision:latest", use_vision=False, max_workers=4) -> List[str]:
    """
    Process a single PDF using Docling and Ollama

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory where the processed files will be saved
        model_name: Ollama model to use
        use_vision: Whether to use vision model for enhanced analysis
        max_workers: Maximum number of parallel workers for processing

    Returns:
        List of output file paths
    """
    processor = DoclingProcessor(
        model_name=model_name,
        use_vision=use_vision,
        max_workers=max_workers
    )
    return processor.process_single_pdf(pdf_path, output_dir)

def batch_process_pdfs(pdf_paths: List[Path], output_dir: Path, model_name="granite3.2-vision:latest", use_vision=False, max_workers=4) -> Dict[str, List[str]]:
    """
    Process multiple PDFs as a batch

    Args:
        pdf_paths: List of paths to PDF files
        output_dir: Directory where the processed files will be saved
        model_name: Ollama model to use
        use_vision: Whether to use vision model for enhanced analysis
        max_workers: Maximum number of parallel workers for processing

    Returns:
        Dictionary mapping input file names to lists of output file paths
    """
    processor = DoclingProcessor(
        model_name=model_name,
        use_vision=use_vision,
        max_workers=max_workers
    )
    return processor.process_batch(pdf_paths, output_dir)
