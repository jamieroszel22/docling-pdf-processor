"""
Docling PDF Processor for Open WebUI RAG

A Flask application that processes PDF documents using Docling
and prepares them for integration with Open WebUI for RAG.
"""

import os
from pathlib import Path
from flask import Flask

# Create and configure Flask app
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-flask-sessions')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['PROCESSED_FOLDER'] = os.path.join(os.getcwd(), 'processed')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.config['OLLAMA_MODEL'] = os.environ.get('OLLAMA_MODEL', 'granite3.2-vision:latest')

# Ensure upload and processed directories exist
upload_dir = Path(app.config['UPLOAD_FOLDER'])
processed_dir = Path(app.config['PROCESSED_FOLDER'])

upload_dir.mkdir(exist_ok=True, parents=True)
processed_dir.mkdir(exist_ok=True, parents=True)

# Import routes
from app import routes

__version__ = '0.1.0'
__author__ = 'Docling PDF Processor Team'
