import logging
import time
from pathlib import Path
from typing import List, Dict, Any
import os
import json

from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

logger = logging.getLogger(__name__)

class DoclingProcessor:
    """
    A class that handles PDF processing using Docling
    """

    def __init__(self, debug_mode=False):
        """
        Initialize the Docling processor

        Args:
            debug_mode: Whether to enable debug visualizations
        """
        # Configure debug visualizations if needed
        if debug_mode:
            settings.debug.visualize_layout = True
            settings.debug.visualize_ocr = True
            settings.debug.visualize_tables = True
            settings.debug.visualize_cells = True

        # Configure pipeline options
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.generate_page_images = True

        # Create document converter
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self.pipeline_options)
            }
        )

    def process_single_pdf(self, pdf_path: Path, output_dir: Path) -> List[str]:
        """
        Process a single PDF using Docling

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory where the processed files will be saved

        Returns:
            List of output file paths
        """
        logger.info(f"Processing PDF: {pdf_path}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        start_time = time.time()

        # Convert the PDF
        try:
            conv_result = self.doc_converter.convert(pdf_path, raises_on_error=True)
            output_files = self._save_conversion_result(conv_result, output_dir)

            end_time = time.time() - start_time
            logger.info(f"Document conversion complete in {end_time:.2f} seconds.")

            return output_files
        except Exception as e:
            logger.error(f"Error converting PDF: {e}", exc_info=True)
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

        start_time = time.time()

        # Check if files exist
        for pdf_path in pdf_paths:
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Convert the PDFs
        try:
            conv_results = self.doc_converter.convert_all(
                pdf_paths,
                raises_on_error=True,
            )

            results = {}
            for conv_result in conv_results:
                input_filename = conv_result.input.file.name
                output_files = self._save_conversion_result(conv_result, output_dir)
                results[input_filename] = output_files

            end_time = time.time() - start_time
            logger.info(f"Batch conversion complete in {end_time:.2f} seconds.")

            return results
        except Exception as e:
            logger.error(f"Error in batch conversion: {e}", exc_info=True)
            raise

    def _save_conversion_result(self, conv_result: ConversionResult, output_dir: Path) -> List[str]:
        """
        Save conversion results to various formats

        Args:
            conv_result: Conversion result from Docling
            output_dir: Directory where the processed files will be saved

        Returns:
            List of output file paths
        """
        output_files = []

        if conv_result.status == ConversionStatus.SUCCESS:
            doc_filename = conv_result.input.file.stem

            # Create a subdirectory for this document
            doc_output_dir = output_dir / doc_filename
            doc_output_dir.mkdir(parents=True, exist_ok=True)

            # Save as JSON (good for structured RAG)
            json_path = doc_output_dir / f"{doc_filename}.json"
            conv_result.document.save_as_json(
                json_path,
                image_mode=ImageRefMode.PLACEHOLDER,
            )
            output_files.append(str(json_path))

            # Save as HTML (for preview)
            html_path = doc_output_dir / f"{doc_filename}.html"
            conv_result.document.save_as_html(
                html_path,
                image_mode=ImageRefMode.EMBEDDED,
            )
            output_files.append(str(html_path))

            # Save as Markdown (good for text-based RAG)
            md_path = doc_output_dir / f"{doc_filename}.md"
            conv_result.document.save_as_markdown(
                md_path,
                image_mode=ImageRefMode.PLACEHOLDER,
            )
            output_files.append(str(md_path))

            # Save as plain text (best for simple RAG)
            txt_path = doc_output_dir / f"{doc_filename}.txt"
            conv_result.document.save_as_markdown(
                txt_path,
                image_mode=ImageRefMode.PLACEHOLDER,
                strict_text=True,
            )
            output_files.append(str(txt_path))

            # Export metadata about the document for RAG context
            metadata = {
                "filename": doc_filename,
                "processed_time": time.time(),
                "status": "success",
                "output_files": [os.path.basename(f) for f in output_files]
            }

            metadata_path = doc_output_dir / f"{doc_filename}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            output_files.append(str(metadata_path))

            return output_files
        elif conv_result.status == ConversionStatus.PARTIAL_SUCCESS:
            logger.warning(
                f"Document {conv_result.input.file} was partially converted with errors"
            )
            # Handle partial success (could save what we have)
            return []
        else:
            logger.error(f"Document {conv_result.input.file} failed to convert")
            return []


# Simplified interface functions
def process_pdf(pdf_path: Path, output_dir: Path, debug_mode=False) -> List[str]:
    """
    Process a single PDF using Docling

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory where the processed files will be saved
        debug_mode: Whether to enable debug visualizations

    Returns:
        List of output file paths
    """
    processor = DoclingProcessor(debug_mode=debug_mode)
    return processor.process_single_pdf(pdf_path, output_dir)


def batch_process_pdfs(pdf_paths: List[Path], output_dir: Path, debug_mode=False) -> Dict[str, List[str]]:
    """
    Process multiple PDFs as a batch

    Args:
        pdf_paths: List of paths to PDF files
        output_dir: Directory where the processed files will be saved
        debug_mode: Whether to enable debug visualizations

    Returns:
        Dictionary mapping input file names to lists of output file paths
    """
    processor = DoclingProcessor(debug_mode=debug_mode)
    return processor.process_batch(pdf_paths, output_dir)
