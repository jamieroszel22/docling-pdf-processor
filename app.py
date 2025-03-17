import os
import logging
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from app.utils.pdf_processor_ollama import process_pdf, batch_process_pdfs
from app.utils.openwebui_exporter import prepare_for_openwebui, OpenWebUIExporter

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__,
            template_folder='app/templates',
            static_folder='app/static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-flask-sessions')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.getcwd(), 'processed')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['OLLAMA_MODEL'] = os.environ.get('OLLAMA_MODEL', 'granite3.2-vision:latest')

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Process the PDF with Ollama
            output_files = process_pdf(
                Path(filepath),
                Path(app.config['PROCESSED_FOLDER']),
                model_name=app.config['OLLAMA_MODEL']
            )

            flash(f'File {filename} processed successfully! Output files: {", ".join([os.path.basename(f) for f in output_files])}')
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            flash(f'Error processing file: {str(e)}')

        return redirect(url_for('index'))

    flash('Invalid file type. Only PDF files are allowed.')
    return redirect(url_for('index'))

@app.route('/batch', methods=['POST'])
def batch_upload():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files part'}), 400

    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected files'}), 400

    results = []
    file_paths = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            file_paths.append(Path(filepath))
            results.append({
                'name': filename,
                'status': 'uploaded'
            })
        else:
            results.append({
                'name': file.filename if file.filename else 'unknown',
                'status': 'invalid',
                'error': 'Invalid file type'
            })

    try:
        # Process all PDFs as a batch
        output_files = batch_process_pdfs(
            file_paths,
            Path(app.config['PROCESSED_FOLDER']),
            model_name=app.config['OLLAMA_MODEL']
        )

        return jsonify({
            'message': f'Processed {len(file_paths)} files successfully',
            'results': results,
            'output_files': output_files
        })
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Error processing batch: {str(e)}',
            'results': results
        }), 500

@app.route('/files')
def list_files():
    processed_files = []
    for root, dirs, files in os.walk(app.config['PROCESSED_FOLDER']):
        for file in files:
            # Only include text and json files for RAG
            if file.endswith('.txt') or file.endswith('.json') or file.endswith('.md'):
                rel_path = os.path.relpath(os.path.join(root, file), app.config['PROCESSED_FOLDER'])
                processed_files.append(rel_path)

    return jsonify({'files': processed_files})

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

@app.route('/openwebui-export')
def openwebui_export():
    """
    Export processed documents for Open WebUI
    """
    # Get selected documents from query parameters
    doc_names = request.args.get('docs', '').split(',')
    formats = request.args.get('formats', 'txt').split(',')

    if not doc_names or doc_names[0] == '':
        return render_template('openwebui_export.html')

    # Convert format strings to proper format with dot
    formats = [f".{fmt}" if not fmt.startswith('.') else fmt for fmt in formats]

    try:
        # Prepare the export
        export_info = prepare_for_openwebui(
            Path(app.config['PROCESSED_FOLDER']),
            doc_names,
            formats
        )

        # Get file size
        export_path = Path(export_info['export_path'])
        size_bytes = export_path.stat().st_size

        # Format file size
        if size_bytes < 1024:
            size_formatted = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            size_formatted = f"{size_bytes / 1024:.1f} KB"
        else:
            size_formatted = f"{size_bytes / (1024 * 1024):.1f} MB"

        # Add additional information
        export_info['size_bytes'] = size_bytes
        export_info['size_formatted'] = size_formatted
        export_info['download_url'] = url_for('download_export', filename=os.path.basename(export_path))
        export_info['instructions_url'] = url_for('view_instructions', export_id=os.path.basename(export_path).split('.')[0])

        # For API requests
        if request.headers.get('Accept') == 'application/json':
            return jsonify(export_info)

        # For web requests
        return render_template('openwebui_export.html', export_info=export_info)
    except Exception as e:
        logger.error(f"Error preparing OpenWebUI export: {str(e)}", exc_info=True)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({'error': str(e)}), 500
        flash(f'Error preparing export: {str(e)}')
        return render_template('openwebui_export.html')

@app.route('/download-export/<path:filename>')
def download_export(filename):
    """
    Download an export package
    """
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename, as_attachment=True)

@app.route('/instructions/<export_id>')
def view_instructions(export_id):
    """
    View export instructions for a specific export
    """
    # This can be expanded to show specific instructions for an export
    return render_template('openwebui_export.html')

@app.route('/ollama-models')
def ollama_models():
    """
    Get a list of available Ollama models
    """
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = [model['name'] for model in response.json().get('models', [])]
            return jsonify({'models': models, 'current': app.config['OLLAMA_MODEL']})
        else:
            return jsonify({'error': 'Failed to get models from Ollama API'}), 500
    except Exception as e:
        logger.error(f"Error getting Ollama models: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/set-model', methods=['POST'])
def set_model():
    """
    Set the Ollama model to use
    """
    model = request.json.get('model')
    if not model:
        return jsonify({'error': 'No model specified'}), 400

    app.config['OLLAMA_MODEL'] = model
    return jsonify({'success': True, 'model': model})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
