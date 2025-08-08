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
