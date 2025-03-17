"""
Export processed files for use with Open WebUI RAG
"""
import os
import json
import zipfile
import tempfile
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class OpenWebUIExporter:
    """
    Export processed files for use with Open WebUI RAG system
    """

    @staticmethod
    def create_export_package(files: List[Path], export_id: str = None) -> Path:
        """
        Create a zip package of files for Open WebUI

        Args:
            files: List of file paths to include
            export_id: Optional custom ID for the export (defaults to timestamp)

        Returns:
            Path to the created export package
        """
        if not export_id:
            export_id = f"openwebui_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create manifest
            manifest = {
                "id": export_id,
                "created": datetime.now().isoformat(),
                "files": []
            }

            # Copy files to temp directory and add to manifest
            for file_path in files:
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                # Get relative name (remove parent directory)
                rel_name = file_path.name

                # Copy the file
                dst_path = temp_path / rel_name
                shutil.copy2(file_path, dst_path)

                # Add to manifest
                manifest["files"].append({
                    "name": rel_name,
                    "path": rel_name,
                    "size": os.path.getsize(file_path),
                    "type": file_path.suffix[1:] if file_path.suffix else "txt"
                })

            # Write manifest
            with open(temp_path / "manifest.json", 'w') as f:
                json.dump(manifest, f, indent=2)

            # Create README for import instructions
            instructions = """# Open WebUI Import Instructions

1. Go to your Open WebUI installation
2. Navigate to Collections
3. Click "Create Collection" or select an existing collection
4. Click "Import" and select this zip file
5. Configure chunking settings as needed
6. Start using your documents in RAG conversations!
"""
            with open(temp_path / "README.md", 'w') as f:
                f.write(instructions)

            # Create the zip file
            output_dir = Path.cwd() / "processed"
            output_dir.mkdir(exist_ok=True)

            output_path = output_dir / f"{export_id}.zip"
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in temp_path.glob('*'):
                    zipf.write(file_path, arcname=file_path.name)

            return output_path

def prepare_for_openwebui(processed_dir: Path, doc_names: List[str], formats: List[str]) -> Dict[str, Any]:
    """
    Prepare selected documents for export to Open WebUI

    Args:
        processed_dir: Directory containing processed documents
        doc_names: List of document names to include
        formats: List of file formats to include (e.g., ['.txt', '.md'])

    Returns:
        Dictionary with export information
    """
    # Find all matching files
    files_to_export = []
    for doc_name in doc_names:
        doc_dir = processed_dir / doc_name
        if not doc_dir.exists() or not doc_dir.is_dir():
            logger.warning(f"Document directory not found: {doc_dir}")
            continue

        for fmt in formats:
            # Find files with the specified format
            for file_path in doc_dir.glob(f"*{fmt}"):
                if file_path.is_file():
                    files_to_export.append(file_path)

    if not files_to_export:
        raise ValueError("No matching files found for export")

    # Create export ID from document names
    if len(doc_names) == 1:
        export_id = f"openwebui_{doc_names[0]}"
    else:
        export_id = f"openwebui_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create the export package
    exporter = OpenWebUIExporter()
    export_path = exporter.create_export_package(files_to_export, export_id)

    return {
        "export_id": export_id,
        "export_path": str(export_path),
        "file_count": len(files_to_export),
        "documents": doc_names,
        "formats": formats
    }
