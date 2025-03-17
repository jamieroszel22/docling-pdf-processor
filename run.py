#!/usr/bin/env python
"""
Docling PDF Processor
Run script to start the application
"""
import os
import logging
from app import app

def main():
    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5001))

    # Start the application
    print(f"Starting Docling PDF Processor on port {port}...")
    print(f"Open your browser at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'True').lower() == 'true')

if __name__ == '__main__':
    main()
