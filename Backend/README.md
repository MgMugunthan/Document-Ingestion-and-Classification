# Document Ingestion and Classification Backend

## Setup Instructions

### Quick Start (Recommended)

1. **Run the system directly:**
   ```bash
   cd Backend
   python main.py
   ```

The system automatically uses the unified virtual environment (`venv/`) for all components.

### Development Setup (Optional)

If you need to run individual components or install new packages:

1. **Activate the virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Or in bash/PowerShell:
   ./venv/Scripts/activate
   ```

2. **Install/Update dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Architecture

The system uses a single virtual environment (`venv/`) for all components:

- **Ingestor**: Monitors folder for new documents
- **Extractor**: Extracts text from various file formats
- **Classifier**: Classifies documents using ML and AI
- **Router**: Routes documents to appropriate folders

## Dependencies

All dependencies are consolidated in `requirements.txt` including:
- Kafka for message queuing
- ML libraries (scikit-learn, numpy)
- Document processing (pdfplumber, python-docx, openpyxl)
- Google Generative AI
- Flask for web interface

## Environment Variables

Create a `.env` file in the Backend directory with:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

## Running Individual Components

If needed, you can run individual components:
```bash
# Activate environment first
venv\Scripts\activate

# Then run specific component
python ingestor/ingestor.py
python extractor/extractor.py
python classifier/classifier.py
python router/router.py
```
