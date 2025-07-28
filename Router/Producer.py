from kafka import KafkaProducer
import json
import os

# Kafka setup
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

SAMPLES_DIR = 'samples'
SENT_LOG = 'sent_log.json'
FAIL_LOG = 'fail_log.json'

# Load previously sent IDs
if os.path.exists(SENT_LOG):
    with open(SENT_LOG) as f:
        sent_ids = set(json.load(f))
else:
    sent_ids = set()

# Load previously failed log (optional)
if os.path.exists(FAIL_LOG):
    with open(FAIL_LOG) as f:
        fail_log = json.load(f)
else:
    fail_log = []

# Classifier based on filename
def classify(filename):
    name = filename.lower()
    if "invoice" in name:
        return "invoice"
    elif "resume" in name:
        return "resume"
    elif "form" in name:
        return "form"
    else:
        return "default"

count = 0
fail_count = 0

# Go through all sample files
for fname in os.listdir(SAMPLES_DIR):
    file_path = os.path.join(SAMPLES_DIR, fname)

    if not os.path.isfile(file_path):
        continue  # skip folders

    doc_id = os.path.splitext(fname)[0]

    if doc_id in sent_ids:
        print(f"⏭️ Skipping already sent: {doc_id}")
        continue

    doc_type = classify(fname)

    msg = {
        "document_id": doc_id,
        "type": doc_type,
        "path": os.path.abspath(file_path)
    }

    try:
        print(f"📤 Sending: {doc_id} as {doc_type}")
        producer.send("doc.classified", value=msg).get(timeout=10)
        sent_ids.add(doc_id)
        count += 1

    except Exception as e:
        reason = str(e)
        print(f"[❌] Failed to send {doc_id}: {reason}")
        fail_log.append({
            "document_id": doc_id,
            "filename": fname,
            "path": file_path,
            "error": reason
        })
        fail_count += 1

# Save logs
with open(SENT_LOG, 'w') as f:
    json.dump(list(sent_ids), f, indent=2)

with open(FAIL_LOG, 'w') as f:
    json.dump(fail_log, f, indent=2)

producer.flush()

print(f"[✓] Sent {count} new document(s)")
if fail_count:
    print(f"[⚠️] {fail_count} file(s) failed to send. See {FAIL_LOG} for details.")
else:
    print("✅ All documents sent to 'doc.classified'")
