from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="docling-pdf-processor",
    version="0.1.0",
    author="Jamie Roszel",
    author_email="your.email@example.com",
    description="A Flask application for processing PDFs using local Ollama models",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/docling-pdf-processor",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "docling-pdf-processor=run:main",
        ],
    },
)
