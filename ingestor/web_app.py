from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
from event_emitter import emit_event
from email_ingestor import fetch_emails_from_user

app = Flask(__name__)
UPLOAD_FOLDER = "./watched"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)

        with open(file_path, "rb") as f:
            content = f.read()
            emit_event(filename, source="folder", content_bytes=content)

        return jsonify({"status": "success", "message": "File uploaded and event emitted"})
    return jsonify({"status": "error", "message": "No file found"})

@app.route("/connect_mailbox", methods=["POST"])
def connect_mailbox():
    email = request.form.get("email")
    password = request.form.get("password")
    success = fetch_emails_from_user(email, password)
    return jsonify({"status": "done" if success else "failed"})

if __name__ == "__main__":
    app.run(debug=True)
