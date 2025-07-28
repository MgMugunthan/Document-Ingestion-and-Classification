from flask import Flask, request
import os, json

app = Flask(__name__)
RECEIVED_FOLDER = "./received_docs"

if not os.path.exists(RECEIVED_FOLDER):
    os.makedirs(RECEIVED_FOLDER)

@app.route("/receive", methods=["POST"])
def receive_file():
    file = request.files["file"]
    metadata = json.loads(request.form.get("event", "{}"))

    file_path = os.path.join(RECEIVED_FOLDER, file.filename)
    file.save(file_path)

    json_path = os.path.join(RECEIVED_FOLDER, file.filename + ".json")
    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[✅ RECEIVED] {file.filename} and metadata saved.")
    return {"status": "success", "file": file.filename}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)