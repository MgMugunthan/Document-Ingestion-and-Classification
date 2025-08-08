# Comprehensive Guide to the Document Ingestion and Classification System

*This document is your ultimate guide to understanding, running, and modifying this project. We'll explain everything from the big picture to the tiny details, so even if you're new to coding, you can follow along!*

---

## 🌟 **Part 1: The Big Picture - What Does This Project Do?**

Imagine you have a big pile of papers on your desk: some are drawings, some are homework, and some are letters from friends. It would be a mess to find what you need, right?

This project is like a magical robot that takes any document you give it, figures out what it is (like a resume, an invoice, or a receipt), and automatically files it in the correct folder for you. It can even grab documents directly from your email!

**What it can do:**
1.  **Upload Documents:** You can give it files from your computer.
2.  **Connect to Gmail:** It can watch your Gmail and automatically grab new attachments.
3.  **Read Documents:** It uses smart technology (like OCR) to read the text from PDFs, images, and Word documents.
4.  **Understand & Classify:** It uses Artificial Intelligence (AI) to guess what the document is (e.g., "This looks like a resume!").
5.  **File It Away:** It moves the document into a specific folder based on its type (e.g., all resumes go into the `resumes` folder).
6.  **See Everything:** It gives you a beautiful website (a dashboard) where you can see all your documents, search for them, and manage them.

---

## 💻 **Part 2: The Technology We're Using**

To build our magical robot, we use a few different tools and languages. Think of these as the different parts of a robot: the brain, the arms, the legs, etc.

### **Backend (The Robot's Brain and Body)**

The backend is where all the heavy lifting happens. It's the smart part of our system that does all the work.

*   **Python:** The main programming language for the backend. It's like the language we use to give instructions to our robot.
*   **Flask:** A tool for building the robot's communication system (the API). It allows the backend to talk to the frontend (the website).
*   **PostgreSQL (Postgres):** The robot's memory or database. This is where we store information about every document, like its name, where it's stored, and what type it is.
*   **Kafka:** A super-fast messaging system. Imagine our robot has different parts (one for reading, one for thinking, one for filing). Kafka is like a conveyor belt that passes the document from one part to the next, ensuring nothing gets lost.
*   **Docker:** A tool that lets us package our robot and all its parts into a neat box. This makes it easy to run the project on any computer without a complicated setup.

### **Frontend (The Robot's Control Panel)**

The frontend is the website you see and interact with. It's the control panel for our robot.

*   **TypeScript:** A special version of JavaScript that helps us avoid bugs by checking our code as we write it.
*   **React & Next.js:** Tools for building modern, fast, and beautiful websites. Think of them as the kit we use to build the buttons, screens, and layout of our control panel.
*   **Tailwind CSS:** A tool for styling our website and making it look good. It's like the paint and stickers we use to decorate our robot's control panel.

---

## ⚙️ **Part 3: How It All Works Together - The Grand Tour**

Our project is split into two main parts: the **Backend** (the engine) and the **Frontend** (the dashboard). They are like two separate robots that talk to each other.

### **How the Backend and Frontend Talk: The API**

The Frontend doesn't connect directly to the database. Instead, it sends requests to the Backend over the network. This is called an **API (Application Programming Interface)**.

*   **Frontend asks:** "Hey Backend, can you give me a list of all the recent documents?"
*   **Backend answers:** "Sure, here is a list in a special format called JSON."

This is great because it means we can change the Frontend or the Backend without breaking the other, as long as they agree on the API questions and answers.

### **The Backend's Micro-Factory: A Microservices Architecture**

The Backend isn't just one big program. It's a team of smaller, specialized programs called **microservices**. Each one has a single job to do. This is like an assembly line in a factory.

Here are our factory workers (microservices):

1.  **Orchestrator (`main.py`):** The factory manager. Its job is to start all the other workers and make sure they are running.
2.  **Ingestor:** The receptionist. It receives new documents, either from a file upload or from Gmail.
3.  **Extractor:** The reader. It takes a document and reads all the text out of it.
4.  **Classifier:** The brain. It takes the text from the Extractor and uses AI to decide what kind of document it is.
5.  **Router:** The filer. It takes the classified document and moves it to the correct final folder.
6.  **API & Auth Services:** The communicators. They talk to the Frontend, handle user login, and fetch information from the database to show on the website.

### **The Conveyor Belt: How Documents Move Through the System (Kafka)**

So how does a document get from the Ingestor to the Extractor, then to the Classifier, and so on? We use a super-fast conveyor belt called **Kafka**.

When one worker finishes its job, it doesn't hand the document directly to the next worker. Instead, it puts a message on a specific Kafka "channel" (called a **topic**). The next worker in line is always listening to that channel, and as soon as it sees a new message, it picks up the document and starts its job.

**The Journey of a Document:**

1.  **Upload:** You upload a `my_resume.pdf` file.
2.  **Ingestor:** The Ingestor sees the new file. It saves it and puts a message on the `doc.ingested` Kafka channel saying, "Hey, there's a new document ready to be processed!"
3.  **Extractor:** The Extractor is listening to `doc.ingested`. It sees the message, grabs `my_resume.pdf`, reads all the text, and puts a new message on the `doc.extracted` channel with the text inside.
4.  **Classifier:** The Classifier is listening to `doc.extracted`. It sees the message, reads the text, and uses its AI model to determine, "This is a 'resume' with 95% confidence." It then puts a message on the `doc.classified` channel with this information.
5.  **Router:** The Router is listening to `doc.classified`. It sees the message, checks its rulebook (`routes.json`), and sees that 'resume' documents should go into the `resumes` folder. It then moves the file and updates the database to say the job is done.

This conveyor belt system is amazing because if one worker is busy, the messages just wait in line on the channel. No work is ever lost!

---

## 💾 **Part 4: The Backend Deep Dive - Inside the Engine Room**

Let's open up the robot's engine room (`Backend` folder) and see how each part works.

### **Backend Folder Structure**

The `Backend` folder is neatly organized. Each microservice gets its own folder, which contains all the code and files it needs to do its job.

```
Backend/
├── api/              # Handles requests from the frontend for document data
├── auth/             # Handles user login and authentication
├── classifier/       # The "brain" that decides what a document is
├── database/         # Manages the connection and communication with our PostgreSQL database
├── extractor/        # Reads the text from files
├── ingestor/         # Gets new documents from uploads or Gmail
├── router/           # Files documents into the correct final folders
├── logs/             # Where all the log files are saved
├── main.py           # The manager/orchestrator that starts everything
├── logger.py         # A special tool to create pretty, colorful logs
├── requirements.txt  # A list of all the Python tools (packages) we need
└── ...
```

### **File-by-File Code Explanation**

Let's go through the most important files one by one.

#### **1. `main.py` - The Factory Manager**

This is the master script. When you run `python main.py`, you are telling the factory manager to start the entire assembly line.

*   **What it does:**
    1.  **Initializes Kafka:** It first checks if the Kafka conveyor belt system is running. If not, it tries to create the necessary channels (topics).
    2.  **Defines the Workers:** It has a list of all the microservice scripts that need to be run (`agents`).
    3.  **Starts Everyone:** It uses a technique called "threading" to start each microservice at the same time. Each worker runs in its own separate process, so they don't interfere with each other.

*   **Code Highlights (`main.py`):**

    ```python
    # A list of all the services (our "workers") to start.
    # Each item is a tuple with the path to the script and a friendly name.
    agents = [
        ("auth/auth.py", "Auth Service"),
        ("api/api.py", "Documents API"),
        ("ingestor/ingestor.py", "Ingestor"),
        ("extractor/extractor.py", "Extractor"),
        ("classifier/classifier.py", "Classifier"),
        ("router/router.py", "Router"),
    ]

    # Loop through the list of agents
    for script, label in agents:
        # Create a new "thread" for each worker. This is like giving
        # each worker their own set of instructions to follow simultaneously.
        t = threading.Thread(target=run_script, args=(script, label))
        t.daemon = True  # This ensures that if the main script stops, all workers stop too.
        t.start()        # Tell the worker to start their job!
    ```

#### **2. `database/database.py` - The Memory Keeper**

This file is incredibly important. It manages everything related to our database (the robot's memory). It's designed as a **Singleton**, which is a fancy way of saying "no matter how many times you ask for the memory keeper, you always get the exact same one." This prevents us from having multiple, confusing connections to the database.

*   **What it does:**
    1.  **Connects to PostgreSQL:** It knows how to connect to our Postgres database using the username, password, etc.
    2.  **Creates Tables (Schema):** The first time it runs, it creates all the tables we need to store our data. This is called the **database schema**.
    3.  **Provides Helper Functions:** It has simple functions like `insert_document()`, `get_documents()`, and `update_document_status()`. This means other parts of our code don't need to know how to write complicated database queries. They can just ask the `db_manager` to do it for them.

*   **Database Schema:** Our database has three main tables:

    1.  `users`: Stores information about users who can log in.
        *   `id`: A unique number for each user.
        *   `email`: The user's email address.
        *   `password_hash`: The user's password (stored securely, not as plain text!).
        *   ...and more.

    2.  `documents`: Stores information about every single document.
        *   `document_id`: A unique ID for the document.
        *   `original_filename`: The name of the file when it was uploaded.
        *   `processing_status`: Where the document is in the assembly line (e.g., `uploaded`, `extracted`, `classified`, `routed`).
        *   `category`: What the AI thinks the document is (e.g., `resume`, `invoice`).
        *   `final_path`: The final folder location where the document is stored.
        *   ...and more.

    3.  `processing_logs`: Keeps a diary of every step a document takes.
        *   `document_id`: The ID of the document this log entry is about.
        *   `stage`: The step in the process (e.g., `extraction`, `classification`).
        *   `status`: Whether the step was a `success` or `failure`.
        *   `message`: Any important notes about the step.

*   **Code Highlights (`database.py`):**

    ```python
    # This is the Singleton pattern. It ensures we only ever have one DatabaseManager.
    class DatabaseManager:
        _instance = None
        def __new__(cls):
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
            return cls._instance

        # This function gets a list of documents from the database.
        # It builds a SQL query based on the filters you provide.
        def get_documents(self, user_id=None, status=None, category=None, limit=100, offset=0):
            # ... builds a SQL SELECT query here ...
    ```

#### **3. `ingestor/` - The Receptionist**

The Ingestor's job is to be the front door for all new documents.

*   **What it does:**
    1.  **Watches a Folder:** It constantly watches the `ingestor/uploads` folder. As soon as a new file appears there, it grabs it.
    2.  **Provides an Upload API:** The frontend website sends files to an API endpoint run by the Ingestor.
    3.  **Connects to Gmail:** It can be told to log in to a user's Gmail account and look for emails with attachments.
    4.  **Starts the Process:** Once it gets a new document, it saves it, adds its details to the database, and puts a message on the `doc.ingested` Kafka channel to kick off the assembly line.

*   **Key Files:**
    *   `ingestor.py`: Starts the Ingestor service.
    *   `ingestor_core.py`: Contains the main logic for handling new files.
    *   `gmail_handler.py`: Contains all the logic for connecting to and reading from Gmail.
    *   `flask_routes.py`: Defines the API endpoints for file uploads and managing Gmail connection.

#### **4. `extractor/extractor.py` - The Reader**

The Extractor is a specialist. Its only job is to read text.

*   **What it does:**
    1.  **Listens for Jobs:** It listens to the `doc.ingested` Kafka channel.
    2.  **Supports Multiple File Types:** It knows how to handle different kinds of files:
        *   `.pdf`: Uses a library called `pdfplumber`.
        *   `.docx`: Uses a library called `python-docx`.
        *   `.txt`, `.json`, etc.: Reads them directly.
        *   Images (`.png`, `.jpg`): Uses a technology called **OCR (Optical Character Recognition)** with a tool called `pytesseract` to read text from the image.
    3.  **Passes it On:** Once it has all the text, it updates the database and puts a message on the `doc.extracted` Kafka channel.

#### **5. `classifier/` - The AI Brain**

This is where the magic happens. The Classifier figures out what each document is about.

*   **What it does:**
    1.  **Listens for Jobs:** It listens to the `doc.extracted` Kafka channel.
    2.  **Uses a Pre-trained Model:** It loads two special files, `document_classifier.pkl` and `tfidf_vectorizer.pkl`. These files contain a machine learning model that has already been trained to recognize different types of documents.
    3.  **Makes a Guess:** It feeds the document's text into the model and gets back a prediction (e.g., `resume`) and a confidence score.
    4.  **Handles Uncertainty:** If the model's confidence is too low (e.g., less than 70%), it will classify the document as `needs_action` so a human can check it later.
    5.  **Passes it On:** It updates the database with the category and confidence score and puts a message on the `doc.classified` Kafka channel.

*   **Key Files:**
    *   `classifier.py`: The main service that listens to Kafka and uses the model.
    *   `genai_utils.py`: A helper file containing the classification logic.
    *   `*.pkl` files: The saved, pre-trained AI models.

#### **6. `router/router.py` - The Filer**

The Router is the final worker on the assembly line. Its job is to put the document in its final home.

*   **What it does:**
    1.  **Listens for Jobs:** It listens to the `doc.classified` Kafka channel.
    2.  **Reads the Rulebook:** It looks at a file called `router/routes.json`. This file tells it exactly where each category of document should go.
    3.  **Moves the File:** It moves the document from the initial upload location to the final destination folder (e.g., `router/routed_documents/resumes/`).
    4.  **Finishes the Job:** It updates the document's status in the database to `routed` and sets its `final_path`. The document's journey is now complete!

*   **The Rulebook (`routes.json`):**

    ```json
    {
      "routes": {
        "resume": "resumes",
        "cv": "resumes",
        "receipt": "receipts",
        "invoice": "invoices"
      },
      "default_folder": "others",
      "needs_action_folder": "needs_action",
      "confidence_threshold": 0.7
    }
    ```

#### **7. `api/` and `auth/` - The Public Face**

These two services are special. They don't work on the main assembly line. Instead, they are dedicated to talking with the Frontend website.

*   **`auth/auth.py` (The Bouncer):**
    *   Handles user registration (`/api/register`).
    *   Handles user login (`/api/login`).
    *   Checks if a user is logged in correctly.

*   **`api/api.py` & `api/documents_api.py` (The Librarian):**
    *   Provides all the data the frontend needs to display.
    *   `GET /api/documents`: Gets a list of all documents (with filters for searching, sorting, etc.).
    *   `GET /api/documents/stats`: Gets statistics for the dashboard (e.g., how many invoices, how many resumes).
    *   `DELETE /api/documents/<id>`: Deletes a document.
    *   `POST /api/documents/<id>/reroute`: Allows the user to manually move a document to a different folder.

---

## 🧠 Part 5: The Database Deep Dive – Our Robot’s Memory in Detail

This project uses PostgreSQL as its memory. The file `Backend/database/database.py` is the only doorway to the database. Every service uses the same doorway thanks to a Singleton called `DatabaseManager`.

- Where it lives: host=localhost, port=5432, database=document_system, user=postgres, password=1234567890
- When the app starts: `DatabaseManager.initialize_database()` creates the database (if missing) and the tables (if missing) exactly once.

Tables we use (columns simplified):
- users
  - id (serial, primary key)
  - user_id (unique), email (unique), password_hash, user_type, department
  - created_at, last_login
- documents
  - id (serial, primary key), document_id (unique)
  - original_filename, file_path, file_size, file_extension
  - uploaded_by, upload_timestamp
  - processing_status (uploaded, extracted, classified, routed, needs_review)
  - classification_type, classification_confidence, classification_method
  - final_path, created_at, updated_at
- processing_logs
  - id (serial, primary key), document_id
  - stage (ingestion, extraction, classification, routing, etc.)
  - status (success/failure), message, processing_time_ms, timestamp

How services talk to the DB (important helper methods):
- insert_document(doc_data): Add a row to `documents` when a file arrives.
- update_document_status(doc_id, status, classification_data): Move a document along the pipeline.
- log_processing_step(doc_id, stage, status, message, processing_time): Keep a diary entry.
- get_document_status(doc_id): Fetch a single document’s details.
- get_user_documents(user_id) and get_documents(...): Paginated/filtered lists for the UI.
- update_document_final_path(doc_id, final_path, status): Save final destination.
- get_dashboard_analytics(user_id): Aggregated counts and trends for charts.

How to check the database (non-technical):
- Use any Postgres client (e.g., pgAdmin, TablePlus). Connect with the values above.
- Look at tables: users, documents, processing_logs. You will see rows appear as documents move.

How to check the database (technical quick checks):
- Confirm the DB exists: connect to Postgres and ensure `document_system` is listed.
- Inspect a document: select from `documents` where `document_id` matches what the app shows.
- See a document’s history: select from `processing_logs` filtered by the same `document_id`.

How to change the schema safely:
- Add a column in `initialize_database()` and deploy. Postgres’ CREATE TABLE IF NOT EXISTS will not drop your data. For altering existing columns, write an ALTER TABLE block guarded by checks.
- Update corresponding code paths that read/write the new column (DatabaseManager and the APIs that surface it).

---

## 🧩 Part 6: Backend Code – File-by-File and How It Works

This section explains what each backend file does and how the code flows.

1) Backend/main.py – The Orchestrator
- Purpose: Starts all services (Auth, API, Ingestor, Extractor, Classifier, Router) in parallel threads.
- Flow:
  - Ensures Kafka topics exist.
  - Spins up each service script with a friendly name.
  - If the main process exits, all children are stopped.
- Why this matters: A single command can boot the whole factory.

2) Backend/logger.py – Consistent Logging
- Purpose: Central helper to create per-service loggers that write to `Backend/logs` and to the console.
- Why this matters: Uniform logs make debugging simple. Every service calls `logger.get_agent_logger("ServiceName")`.

3) Backend/database/database.py – The DatabaseManager (Singleton)
- Purpose: One shared gatekeeper for Postgres. Prevents duplicate initialization and duplicated “tables created” logs.
- Key ideas:
  - __new__/__init__ ensure a single instance across services.
  - initialize_database() creates DB and tables if missing.
  - Context manager get_connection() yields safe connections and closes them.
  - Query helpers return dict-like rows for easy JSON.

4) Backend/api/api.py – Documents API service
- Purpose: A small Flask app exposing health/status and mounting the documents blueprint.
- Endpoints:
  - GET /api/health – quick health and DB connectivity check.
  - GET /api/status – basic “I am alive”.
  - Mounts /api/documents/* from `documents_api.py`.

5) Backend/api/documents_api.py – Documents management endpoints
- Purpose: Serves the Frontend’s dashboard and admin pages.
- Important endpoints:
  - GET /api/documents – list with filtering, searching, sorting, pagination.
  - GET /api/documents/types – list distinct classification types and counts.
  - GET /api/documents/routes – read router/routes.json to show routing options.
  - DELETE /api/documents/<id> – delete the DB row and any physical files.
  - POST /api/documents/<id>/reroute – move a file to a new folder, update DB paths.
- Implementation notes:
  - Uses db_manager.get_documents() then normalizes field names for the UI.
  - Calculates a human-friendly file size if the file exists on disk.
  - Reads `router/routes.json` to know valid destinations.

6) Backend/auth/auth.py – Authentication service
- Purpose: Register, login, verify tokens, refresh sessions, and provide simple admin user management.
- Data stored in `users` table. Passwords are hashed.
- Endpoints used by the Frontend are under /api/auth/*.

7) Backend/ingestor/* – The Reception Desk
- Files:
  - ingestor.py – boots the service.
  - ingestor_core.py – core logic: save uploads, register in DB, produce Kafka message `doc.ingested`.
  - flask_routes.py – all HTTP endpoints for upload, document status, and Gmail integration.
  - gmail_handler.py – handles OAuth, fetches email attachments safely, hands to core for processing.
- Flow when a file is uploaded:
  - The route receives a multipart form with a file.
  - ingestor_core saves it under `Backend/ingestor/uploads`.
  - db_manager.insert_document() creates the row.
  - A Kafka message with the document_id is produced to `doc.ingested`.

8) Backend/extractor/extractor.py – The Reader
- Purpose: Consume `doc.ingested`, read text depending on file type (PDF, DOCX, TXT, images via OCR), write logs.
- Flow:
  - On success: update status to `extracted` and produce to `doc.extracted` with extracted text.
  - On failure: log a processing_logs entry and mark status accordingly.

9) Backend/classifier/* – The AI Brain
- Files:
  - classifier.py – consumes `doc.extracted`, loads model/vectorizer, predicts category + confidence.
  - genai_utils.py – helper functions (feature prep, thresholds, fallbacks).
- Flow:
  - If confidence >= threshold in router/routes.json (e.g., 0.7), keep the predicted category.
  - Else, set classification_type = needs_action so a human can decide later.
  - Update DB and publish to `doc.classified`.

10) Backend/router/router.py – The Filer
- Purpose: Consume `doc.classified`, pick a destination folder from `router/routes.json`, move the file, finalize DB.
- routes.json controls:
  - routes: map of category -> subfolder.
  - default_folder: where unknown types go.
  - needs_action_folder: special review bin.
  - confidence_threshold: used by Classification to mark needs_action.

11) Utilities at Backend root
- create_admin.py – Interactive script to create the first admin user in `users`.
- check_docs.py – Helper to inspect and optionally clear documents and logs from the DB.
- check_services.py – Quick health checks across services (API/Auth/others).
- clear_logs.py – Empties `Backend/logs/*` for a fresh run.

12) Backend/docker-compose.yml – Messaging backbone
- Starts Zookeeper and Kafka locally.
- Kafka advertised on localhost:9092; topics are created automatically when first used.

---

## 🖥️ Part 7: Frontend Deep Dive – Your Control Panel

The Frontend is a Next.js (React + TypeScript) app in `Frontend/`. It talks to two backend base URLs:
- NEXT_PUBLIC_INGESTOR_URL: default http://localhost:5000 (uploads, Gmail, document-status)
- NEXT_PUBLIC_AUTH_URL: default http://localhost:5001 (register/login/verify/admin)

Important folders and files:
- app/
  - login/page.tsx – login screen. Calls Auth service to get a token and stores it in localStorage.
  - upload/page.tsx – upload UI. Sends files to Ingestor’s /api/receive.
  - dashboard/page.tsx – overall stats and charts. Reads from documents APIs.
  - documents/page.tsx – searchable list. Uses filtering and pagination.
  - review/page.tsx – a place to handle needs_action docs.
  - admin/page.tsx – user management (create, list, update, delete).
  - ai-tool/*, gmail-connected/* – utility screens for AI/Gmail flows.
- contexts/AuthContext.tsx – wraps the app, handles login/logout, and token persistence.
- lib/api.ts – all fetch calls live here. Changes to endpoints go here.
- components/* and components/ui/* – reusable UI building blocks (buttons, dialogs, tables, etc.).
- styles/globals.css, tailwind.config.js – visual style and theme.

How the Frontend calls the Backend:
- All calls go through `lib/api.ts`.
- For authenticated calls, `makeAuthenticatedRequest()` automatically adds the Bearer token and tries a refresh once on 401.
- Document uploads and Gmail actions hit the Ingestor service; admin and auth hit the Auth service; lists and dashboards hit the Documents API.

How a screen is built (example: login/page.tsx):
- Uses useAuth() from AuthContext to call `authApi.login({ user_id, password })`.
- On success, stores `auth_token` and redirects to the next page.

Where to change URLs:
- Update NEXT_PUBLIC_INGESTOR_URL and NEXT_PUBLIC_AUTH_URL in your environment to point to the correct backend hosts.

---

## 🔌 Part 8: How Everything Connects (Backend ⇄ Frontend ⇄ Database ⇄ Kafka)

- Frontend → Backend: via HTTP fetch from `lib/api.ts` to the Auth, Ingestor, and Documents API services.
- Backend services → Database: through `DatabaseManager` (always the same connection pattern).
- Backend services talk among themselves: asynchronously through Kafka topics (`doc.ingested`, `doc.extracted`, `doc.classified`).

Adding a new step in the pipeline (example):
- Create a new microservice (e.g., “validator”) that listens to a new topic (e.g., `doc.validated`).
- Change the producer in the upstream service to send to `doc.validated` instead of `doc.extracted`.
- Update DatabaseManager to record any extra fields you need.
- Update the Documents API if the Frontend must display the new info.

---

## 🛠️ Part 9: Make Changes with Confidence – Common Recipes

Change the folder a document goes to:
- Edit `Backend/router/routes.json`. Add or change entries under `routes`. Example: add "bill" → "bills".
- Optionally update the Frontend to show the new category in filters.

Change the confidence threshold:
- Edit `Backend/router/routes.json` → `confidence_threshold`.
- The Classifier will mark low-confidence items as needs_action using this value.

Add a new document type the AI can recognize:
- Update training offline and refresh `classifier/document_classifier.pkl` and `classifier/tfidf_vectorizer.pkl`.
- Ensure your new label is present in `routes.json` so Router knows where to file it.

Expose a new field in the UI:
- Add the column in `initialize_database()` if needed.
- Update DatabaseManager getters to include the field.
- Map it in `api/documents_api.py` response objects.
- Read it in the Frontend page (e.g., `documents/page.tsx`).

Add a new page or feature in the Frontend:
- Create a new route in `Frontend/app/*/page.tsx`.
- Add API calls in `Frontend/lib/api.ts`.
- Wire it to `AuthContext` if it needs auth.

Modify authentication rules:
- Edit `Backend/auth/auth.py` routes and validations.
- Adjust Frontend guards in `components/ProtectedRoute.tsx` or `contexts/AuthContext.tsx`.

---

## 🚀 Part 10: Run the System (Local, Step-by-Step)

Prerequisites:
- Python 3.10+ and pip
- Node.js 18+ and pnpm or npm
- Docker Desktop running (for Kafka/Zookeeper)

Start services in order:
1) Kafka: in `Backend/`, start Docker services. Wait until Kafka is healthy on port 9092.
2) Backend Python deps: in `Backend/`, install requirements and ensure Postgres is running and accessible.
3) Initialize DB: run the app once (the DatabaseManager creates tables). Optionally run `create_admin.py` to add your admin user.
4) Start the backend: run the Orchestrator (main.py) – it boots Auth (5001), Ingestor (5000), API (5002), and workers.
5) Frontend: in `Frontend/`, install deps and start the dev server. Open http://localhost:3000.

Sanity checks:
- Auth: open its status endpoint; login via the app.
- Ingestor: open its status endpoint; try a small upload.
- Documents API: open /api/health; the dashboard should load with zero docs on first run.

Logs to watch:
- `Backend/logs/*.log` – each service writes its own file. If something fails, check here.

---

## 🧯 Part 11: Troubleshooting (Quick Clues)

- Duplicate “tables created” logs: already fixed by the Singleton + _db_setup_logged flag.
- Can’t connect to DB: verify host/port/creds in DatabaseManager and that Postgres is running.
- Files don’t move: confirm `router/routes.json` exists and the destination folders are writable under `router/routed_documents`.
- Classifier says needs_action too often: lower the confidence threshold in `routes.json` or improve the model.
- Frontend shows 401 errors: token expired – the app will try refresh once. If it still fails, log in again.

---

## 📚 Part 12: Glossary (For Everyone)
- API: A waiter that takes orders (requests) and brings food (data).
- Kafka: A conveyor belt messages ride on.
- Database: Long-term memory.
- Microservice: A small worker that does one job well.
- OCR: A way for computers to read text from pictures.
- Token: A ticket that proves you’re logged in.

You now have the full map: what each part does, how they talk, how to change things, and how to run everything end-to-end. Make changes in one place at a time, test, watch logs, and iterate.

---

## Appendix A: Full API Reference (Current Endpoints)

Base URLs (default local):
- Ingestor: http://localhost:5000
- Auth: http://localhost:5001
- Documents API: http://localhost:5002

1) Auth Service (/api/auth)
- POST /api/auth/login – body: { user_id, password } → { token, user }
- POST /api/auth/verify – body: { token } → { valid: boolean, user? }
- POST /api/auth/refresh – uses Authorization: Bearer <token> → { token }
- POST /api/auth/register – body: { user_id, email, password, user_type?, department? }
- GET  /api/auth/status – service status
- Admin:
  - GET    /api/auth/admin/users
  - POST   /api/auth/admin/users – create user
  - PUT    /api/auth/admin/users/:userId – update user
  - DELETE /api/auth/admin/users/:userId – delete user
  - POST   /api/auth/reset-password – body: { user_id, new_password }

2) Ingestor Service
- GET  /           – HTML status page
- GET  /api/status – JSON status
- POST /api/receive – multipart form: document=<file>, metadata=<json>
- GET  /api/document/:id/status – document status + processing_logs
- GET  /api/documents/user/:user_id – list user’s documents
- GET  /api/documents/all – debug: recent documents (limited)
- GET  /api/documents/routes – router config (routes.json)
- DELETE /api/documents/:document_id – delete document + files
- Gmail integration:
  - POST /api/gmail/fetch – fetch new attachments
  - POST /api/gmail/fetch-all – fetch all unread attachments
  - GET  /api/gmail/status – gmail integration status
  - POST /api/gmail/reset – reset gmail state
  - POST /api/gmail/search – body: { prompt }
  - POST /api/gmail/process-selected – body: { file_ids: string[] }
  - GET  /api/gmail/auth/start – returns { auth_url }
  - POST /api/gmail/auth/disconnect – disconnect integration
  - GET  /api/gmail/auth/callback – OAuth callback (browser flow)

3) Documents API Service
- GET  /api/health – service + DB health
- GET  /api/status – service status
- GET  /api/documents/ – list (query params: user_id, status, type, limit, offset, search, sort_by, sort_order)
- GET  /api/documents/types – unique classification types + counts
- GET  /api/documents/routes – available routing options from routes.json
- GET  /api/documents/stats – basic stats (by_status, by_type)
- DELETE /api/documents/:document_id – delete document + files
- POST   /api/documents/:document_id/reroute – body: { route? , folder? }

Note: Some advanced reclassify/view endpoints are not yet implemented in PostgreSQL path and return 501.

---

## Appendix B: Environment & Configuration

Frontend environment variables (create `Frontend/.env.local`):
- NEXT_PUBLIC_INGESTOR_URL=http://localhost:5000
- NEXT_PUBLIC_AUTH_URL=http://localhost:5001

Backend configuration:
- Database connection is currently defined in `Backend/database/database.py` (connection_params). To change:
  - Edit host, port, database, user, password there; or
  - Refactor to read from OS env (recommended) and define, for example:
    - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
- Service ports (defaults):
  - Ingestor: 5000
  - Auth: 5001
  - Documents API: 5002
- Kafka/Zookeeper via `Backend/docker-compose.yml`:
  - Zookeeper: 2181
  - Kafka: 9092 (advertised localhost:9092)

CORS: The API services enable CORS for local development. Adjust origins if hosting remotely.

---

## Appendix C: Database Operations (psql/pgAdmin, Backup/Restore, Migrations)

Quick psql usage (replace credentials as needed):
- Connect: psql -h localhost -p 5432 -U postgres -d document_system
- List tables: \dt
- Inspect a document: SELECT * FROM documents WHERE document_id = '<id>';
- Recent logs: SELECT * FROM processing_logs ORDER BY timestamp DESC LIMIT 50;

Backup and restore (from a shell):
- Backup DB: pg_dump -h localhost -p 5432 -U postgres -d document_system -F c -f backup.dump
- Restore DB: pg_restore -h localhost -p 5432 -U postgres -d document_system --clean --if-exists backup.dump

Schema changes (simple):
- Add a column safely:
  - Update `initialize_database()` to include the column (CREATE TABLE IF NOT EXISTS keeps data).
  - For existing deployments, run: ALTER TABLE documents ADD COLUMN new_col TEXT; (idempotent checks recommended).
- Consider adopting Alembic for versioned migrations if schema evolves frequently.

pgAdmin/TablePlus:
- Create a connection with host/port/user/db above.
- Browse tables, edit rows, run queries in the query tool.

---

## Appendix D: Testing & Verification Checklist

Before first use:
- Kafka up and reachable at 9092
- Postgres reachable and `initialize_database()` ran (tables exist)
- Auth service /api/auth/status returns running
- Ingestor /api/status returns running
- Documents API /api/health returns healthy

Happy-path document flow:
- Login via Frontend (/login)
- Upload a small PDF in /upload → observe a new row in `documents` with status `uploaded`
- Extractor updates status to `extracted`; Classifier to `classified`; Router to `routed`
- File appears under `Backend/router/routed_documents/<folder>/`
- Dashboard shows updated counts

Gmail flow:
- Start OAuth via Frontend → open auth URL from /api/gmail/auth/start
- After connecting, run /api/gmail/fetch to pull attachments

Admin flow:
- Create user via Auth admin endpoints; verify in `users` table

Negative tests:
- Upload unsupported file → proper error and no DB corruption
- Force low confidence → appears in needs_action folder

---

## Appendix E: Performance & Scaling Notes

Database:
- Add indexes on frequent filters: documents(document_id), documents(uploaded_by), documents(processing_status), documents(classification_type), processing_logs(document_id)
- Use connection pooling (e.g., psycopg2.pool) if concurrency increases
- Avoid SELECT * in hot paths; fetch only needed columns

Kafka and services:
- Keep consumers idempotent (safe on retries)
- Use partitions and multiple consumers for parallel throughput
- Tune Kafka retention by size/time based on workload

Classifier:
- Load model once per process; reuse across messages
- Consider batching if throughput demands it

Filesystem and routing:
- Ensure routed_documents is on fast storage; avoid long path issues on Windows
- Validate and sanitize filenames

Observability:
- Log levels INFO in prod, DEBUG in dev
- Centralize logs and add request IDs/document IDs for tracing
- Add simple health/metrics endpoints if deploying to containers/cloud

Frontend:
- Use pagination and server-side filtering (already present)
- Build production assets (Next.js) and enable cache/CDN for static content

Security:
- Always hash passwords (already implemented)
- Use HTTPS in production and secure JWT handling
- Validate all inputs at API boundaries

These appendices complement the guide with concrete references, configs, operational steps, test plans, and scaling guidance.

---

## Appendix F: Base-Level Explanations (Kid‑Friendly Crash Course)

If this is your first tech project, start here. Think of this system as a school with helpers.

- The Receptionist (Ingestor) takes your paper when you hand it in.
- The Reader (Extractor) reads your paper out loud.
- The Brain (Classifier) decides what kind of paper it is.
- The Filer (Router) puts it in the correct shelf.
- The Librarian (Documents API) tells you where your paper is.
- The Bouncer (Auth) checks you have permission to enter.
- The Memory (Database) remembers everything.
- The Conveyor Belt (Kafka) moves job tickets between helpers.

What happens to one document (in 6 tiny steps):
1) You upload a file on the website.
2) Receptionist saves it and writes a note in Memory: “new paper arrived”.
