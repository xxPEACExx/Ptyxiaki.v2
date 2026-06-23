# Ptyxiaki.v2

## Overview

Ptyxiaki.v2 is a web-based application developed as part of a Bachelor's Thesis project. The system is designed to process, manage, and store large collections of XML documents through a user-friendly web interface.

The application allows users to upload ZIP archives containing XML files, automatically extract and process their contents, and store the extracted information in a MySQL database. It also provides monitoring tools, progress tracking, statistics, and document management features.

The project is built using Python and Flask and is designed to handle large datasets efficiently through background processing and chunked uploads.

---

## Features

- Upload ZIP archives containing XML documents
- Support for large file uploads using chunked transfer
- Automatic extraction of ZIP files
- XML parsing and processing
- Storage of extracted data in MySQL
- Document management and browsing
- Database viewing interface
- Processing progress monitoring
- Pause, resume, and stop processing operations
- Error logging and file validation
- Statistics and information dashboard
- Background task execution for improved performance

---

## Technologies Used

- Python 3
- Flask
- MySQL
- HTML5
- CSS3
- JavaScript
- Waitress WSGI Server

---

## Project Structure

```text
Ptyxiaki.v2/
│
├── README.md
│
└── PythonProject/
    ├── run_server.py
    │
    └── Ptyxiaki/
        ├── app.py
        ├── abstract.py
        ├── claims.py
        ├── classification.py
        ├── country.py
        ├── description.py
        ├── document.py
        ├── format.py
        ├── kind.py
        ├── lang.py
        ├── loadsource.py
        ├── parties.py
        ├── role.py
        ├── save_query.py
        ├── scheme.py
        ├── status.py
        ├── title.py
        ├── static/
        ├── templates/
        └── html/
```

---

## Requirements

Before running the application, make sure the following software is installed:

- Python 3.x
- MySQL Server
- pip

---

## Database Setup

Create a MySQL database:

```sql
CREATE DATABASE epdatabase;
```

Update the database credentials in the source code if necessary.

Example configuration:

```text
Host: localhost
Database: epdatabase
Username: admin
Password: admin
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/xxPEACExx/Ptyxiaki.v2.git
cd Ptyxiaki.v2/PythonProject
```

### 2. Install dependencies

```bash
pip install flask
pip install mysql-connector-python
pip install waitress
pip install reportlab
```

Or:

```bash
pip install flask mysql-connector-python waitress reportlab
```

---

## Running the Application

From the `PythonProject` directory execute:

```bash
python run_server.py
```

The server will start on:

```text
http://localhost:5000
```

---

## Workflow

1. Upload a ZIP archive containing XML files.
2. The system extracts the archive automatically.
3. XML files are parsed and validated.
4. Extracted information is stored in the MySQL database.
5. Processing progress is displayed in real time.
6. Users can browse and query stored documents through the web interface.

---

## Main Components

### Upload System

Handles standard and chunked uploads for large ZIP files.

### XML Processing Engine

Responsible for:

- Reading XML files
- Extracting metadata
- Validating content
- Preparing records for database insertion

### Database Layer

Stores:

- Document metadata
- Titles
- Abstracts
- Classifications
- Countries
- Languages
- Parties
- Roles
- Claims
- Status information

### Monitoring System

Provides:

- Progress tracking
- Error reporting
- Processing statistics
- Runtime information

---

## Logging

The application generates log files for diagnostics and troubleshooting.

Examples:

```text
errors.log
bad_files.log
```

These files contain information about processing failures, invalid XML files, and runtime exceptions.

---

## Future Improvements

Potential future enhancements include:

- User authentication and authorization
- REST API support
- Advanced search functionality
- Full-text indexing
- Docker deployment
- Automated testing
- Performance optimization for larger datasets
- Cloud database support

---

## Academic Purpose

This project was developed as part of a Bachelor's Thesis and focuses on large-scale XML document processing, database storage, and web-based information management.

---

## Author

Developed as a Bachelor's Thesis Project.

GitHub Repository:

https://github.com/xxPEACExx/Ptyxiaki.v2

---

## License

No license has been specified for this repository.
