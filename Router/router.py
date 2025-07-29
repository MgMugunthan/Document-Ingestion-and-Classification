import os
import requests
import datetime
import shutil
import json
from kafka import KafkaConsumer

def load_routes():
    routes_path =os.path.join(os.path.dirname(__file__), 'routes.json')
    with open(routes_path) as f:
        return json.load(f)
    
def log_action(data):
    log_dir= os.path.join(os.path.dirname(__file__),'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"routing_log_{datetime.date.today()}.json")
    with open(log_file,'a') as f:
        json.dump(data,f)
        f.write('\n')

def route_document(doc_data,routes):
    doc_type=doc_data.get("type","default")
    source_path = os.path.abspath(doc_data.get("path"))
    destination = routes.get(doc_type, routes["default"])

    log_data ={
        "document_id": doc_data.get("document_id"),
        "type": doc_type,
        "routed_to": destination,
        "timestamp": datetime.datetime.now().isoformat()
    }

    try:
        if destination.startswith("http"):
            response = requests.post(destination, json = doc_data)
            log_data["status"] = f"Sent to API, Response: {response.status_code}"
        else:
            os.makedirs(destination, exist_ok=True)
            print(f"[DEBUG] Copying from {source_path} to {destination}")
            print(f"[DEBUG] File exists: {os.path.exists(source_path)}")
            shutil.move(source_path, os.path.join(destination, os.path.basename(source_path)))
            log_data["status"] = f"Moved to '{doc_type}' folder → {destination}"
    except Exception as e:
        print(f"[ERROR] Failed to route {doc_data.get('document_id')}: {str(e)}")
        log_data["status"] = f"Failed:{str(e)}"

    log_action(log_data)
    print(f"[✓] Routed document: {doc_type}->{destination}")


if __name__ == "__main__":
        print("Starting Kafka Router...")
        routes = load_routes()

        consumer = KafkaConsumer(
            "doc.classified",
            bootstrap_servers="localhost:9092",
            group_id="router-group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )

        print("Listening for documents on 'doc.classified'...")

        for message in consumer:
            doc_data= message.value
            print(f"Recieved document: {doc_data['document_id']}")
            route_document(doc_data, routes)