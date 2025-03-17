import logging
import time
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

logger = logging.getLogger(__name__)

class OllamaProcessor:
    """
    A class that handles PDF processing using local Ollama models
    """

    def __init__(self, model_name="granite3.2-vision:latest", use_vision=False, max_workers=4):
        """
        Initialize the Ollama processor

        Args:
            model_name: Name of the Ollama model to use
            use_vision: Whether to use vision model for enhanced analysis
            max_workers: Maximum number of parallel workers for processing
        """
        self.model_name = model_name
        self.use_vision = use_vision
        self.max_workers = max_workers
        self.ollama_api = "http://localhost:11434/api"

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

    def _process_page(self, page_num: int, page: fitz.Page, doc_output_dir: Path) -> Dict:
        """
        Process a single page of the PDF

        Args:
            page_num: Page number (1-based)
            page: PyMuPDF page object
            doc_output_dir: Output directory for the document

        Returns:
            Dictionary containing page data
        """
        logger.info(f"Processing page {page_num}/{self.total_pages}")

        # Extract text
        page_text = page.get_text()
        page_data = {
            "page_number": page_num,
            "text": page_text,
            "elements": []
        }

        # If using vision model, process the image
        if self.use_vision:
            try:
                # Convert the page to an image
                pix = page.get_pixmap(alpha=False)
                img_path = doc_output_dir / f"page_{page_num}.png"
                pix.save(img_path)
                logger.info(f"Saved page image: {img_path}")

                # Process with Ollama vision model
                vision_text = self._process_image_with_ollama(img_path)
                logger.info(f"Completed vision analysis for page {page_num}")
                page_data["vision_analysis"] = vision_text
            except Exception as e:
                logger.error(f"Error processing page image: {e}")

        return page_data

    def process_single_pdf(self, pdf_path: Path, output_dir: Path) -> List[str]:
        """
        Process a single PDF using Ollama

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
            # Open the PDF with PyMuPDF
            logger.info("Opening PDF document...")
            pdf_document = fitz.open(pdf_path)
            self.total_pages = len(pdf_document)
            logger.info(f"PDF opened successfully. Total pages: {self.total_pages}")

            # Process pages in parallel
            logger.info(f"Processing pages with {self.max_workers} workers...")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Create partial function with fixed arguments
                process_page_partial = partial(
                    self._process_page,
                    doc_output_dir=doc_output_dir
                )

                # Submit all pages for processing
                future_to_page = {
                    executor.submit(process_page_partial, page_num + 1, page): page_num + 1
                    for page_num, page in enumerate(pdf_document)
                }

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

            # Generate a markdown version with structure
            logger.info("Generating markdown version...")
            md_content = self._generate_markdown(text_content)
            md_path = doc_output_dir / f"{doc_filename}.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
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
                "page_count": len(pdf_document),
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

    def _generate_markdown(self, text_content: str) -> str:
        """
        Generate a structured markdown version of the text content

        Args:
            text_content: The raw text content

        Returns:
            Structured markdown content
        """
        try:
            # Call Ollama to structure the content
            response = requests.post(
                f"{self.ollama_api}/generate",
                json={
                    "model": self.model_name.split(":")[0],  # Use base model without 'vision' part
                    "prompt": f"Convert the following raw text from a PDF document into a well-structured markdown document. Add appropriate headers, lists, and formatting. Preserve the content exactly but improve the structure and readability.\n\nRaw text:\n{text_content[:4000]}",
                    "stream": False
                }
            )

            if response.status_code == 200:
                return response.json().get("response", text_content)
            else:
                # Fallback to basic formatting if Ollama fails
                return text_content
        except Exception as e:
            logger.error(f"Error generating markdown: {e}")
            return text_content

# Simplified interface functions
def process_pdf(pdf_path: Path, output_dir: Path, model_name="granite3.2-vision:latest", use_vision=False, max_workers=4) -> List[str]:
    """
    Process a single PDF using Ollama

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory where the processed files will be saved
        model_name: Ollama model to use
        use_vision: Whether to use vision model for enhanced analysis
        max_workers: Maximum number of parallel workers for processing

    Returns:
        List of output file paths
    """
    processor = OllamaProcessor(
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
    processor = OllamaProcessor(
        model_name=model_name,
        use_vision=use_vision,
        max_workers=max_workers
    )
    return processor.process_batch(pdf_paths, output_dir)
