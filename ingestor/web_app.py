import os
import threading
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from event_emitter import emit_event
from gmail_ingestor import fetch_emails_and_ingest_loop

app = Flask(__name__)
from config import FILES_DIR
UPLOAD_FOLDER = FILES_DIR

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    uploaded_files = request.files.getlist('files')
    for file in uploaded_files:
        if file.filename == '':
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        with open(filepath, 'rb') as f:
            emit_event(
                file_name=filename,
                source="upload",
                content_bytes=f.read(),
                summary="Uploaded via drag-drop UI",
                sender="N/A"
            )

    return jsonify({'message': f'{len(uploaded_files)} file(s) uploaded successfully'})

@app.route('/connect_gmail', methods=['POST'])
def connect_gmail():
    try:
        thread = threading.Thread(target=fetch_emails_and_ingest_loop, daemon=True)
        thread.start()
        return jsonify({'message': 'Gmail connected. Fetcher started.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
