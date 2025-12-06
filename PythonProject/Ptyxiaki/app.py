
from flask import Flask, render_template, jsonify, request
import os
import xml.etree.ElementTree as ET
import mysql.connector
import threading
import time
import logging

from Ptyxiaki.role import initialize_role
from Ptyxiaki.scheme import initialize_scheme
from Ptyxiaki.kind import initialize_kind
from Ptyxiaki.status import initialize_status
from title import insert_title
from parties import insert_parties
from claims import insert_claim
from classification import insert_classification
from document import process_document
from state import initialize_state
from format import initialize_format
from loadsource import initialize_loadsource

# Logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__,template_folder='html')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB

# -------- DATABASE CONNECTION -------- #
try:
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        password="admin",
        database="epdatabase"
    )
    cursor = db.cursor()
except mysql.connector.Error as err:
    logging.critical(f"❌ Σφάλμα σύνδεσης στη βάση: {err}")
    exit(1)

# -------- THREADING CONTROL -------- #
processing_thread = None
processing_lock = threading.Lock()
running = False
paused = False
stopped = False
progress_percentage = 0

# -------- SAFE INSERT HELPER -------- #
def safe_insert(query, params, cursor, db, context="Insert"):
    try:
        cursor.execute(query, params)
    except Exception as e:
        db.rollback()
        logging.error(f"❌ {context} failed: {e}")

# -------- PROCESSING FUNCTION -------- #
def process_files(files):
    global running, paused, stopped, progress_percentage

    total_files = len(files)
    for idx, file_path in enumerate(files, start=1):
        with processing_lock:
            if stopped:
                logging.info("🛑 Διακοπή διαδικασίας.")
                break

        while True:
            with processing_lock:
                if stopped:
                    logging.info("🛑 Διακοπή διαδικασίας.")
                    return
                if not paused:
                    break
            time.sleep(0.5)

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            did = process_document(file_path, cursor, db)
            if did is None:
                logging.warning(f"⚠️ Δεν δημιουργήθηκε DID για: {file_path}")
                continue

            insert_claim(did, root, cursor, db)
            insert_classification(did, root, cursor, db)
            insert_parties(did, root, cursor, db)
            insert_title(did, root, cursor, db)
            db.commit()

            progress_percentage = int((idx / total_files) * 100)
            logging.info(f"📁 Επεξεργασία: {file_path} ({progress_percentage}%)")

        except ET.ParseError as e:
            logging.error(f"❌ Μη έγκυρο XML αρχείο: {file_path} – {e}")
            continue
        except Exception as e:
            db.rollback()
            logging.error(f"💥 Σφάλμα στο αρχείο {file_path}: {e}")
            continue

    with processing_lock:
        running = False
        paused = False
        stopped = False
        progress_percentage = 100
        logging.info("✅ Επεξεργασία ολοκληρώθηκε.")

# -------- START PROCESSING THREAD -------- #
def start_processing_thread(files):
    global processing_thread, running, paused, stopped, progress_percentage
    with processing_lock:
        if running:
            return False
        running = True
        paused = False
        stopped = False
        progress_percentage = 0
    processing_thread = threading.Thread(target=process_files, args=(files,))
    processing_thread.start()
    return True

# -------- ROUTES -------- #



@app.route('/upload_folder', methods=['POST'])
def upload_folder():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'message': 'Δεν επιλέχθηκαν αρχεία.'}), 400

    folder_path = os.path.join('uploaded_files')
    os.makedirs(folder_path, exist_ok=True)

    saved_files = []
    try:
        for file in files:
            file_path = os.path.join(folder_path, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            saved_files.append(file_path)
    except Exception as e:
        return jsonify({'message': f'Σφάλμα κατά την αποθήκευση: {str(e)}'}), 500

    started = start_processing_thread(saved_files)
    if not started:
        return jsonify({'message': 'Η επεξεργασία ήδη τρέχει.'}), 400

    return jsonify({'message': f'Ξεκίνησε η επεξεργασία {len(saved_files)} αρχείων.'})


@app.route('/control', methods=['POST'])
def control():
    global running, paused, stopped
    data = request.json
    action = data.get('action')

    with processing_lock:
        if action == 'pause' and running and not paused:
            paused = True
            return jsonify({'message': 'Η επεξεργασία σταμάτησε προσωρινά.'})
        elif action == 'continue' and running and paused:
            paused = False
            return jsonify({'message': 'Η επεξεργασία συνεχίζεται.'})
        elif action == 'stop' and running:
            stopped = True
            paused = False
            return jsonify({'message': 'Η επεξεργασία τερματίστηκε.'})
        else:
            return jsonify({'message': 'Μη έγκυρη ενέργεια ή η επεξεργασία δεν τρέχει.'}), 400

@app.route('/get_progress', methods=['GET'])
def get_progress():
    global progress_percentage, running, paused
    status = 'running' if running else 'stopped'
    if paused:
        status = 'paused'
    return jsonify({'progress': progress_percentage, 'status': status})


@app.route('/query_documents', methods=['POST'])
def qquery_documents_post():
    cursor.execute("SELECT did, doc_number, date, filename FROM document")  # filename: όνομα αρχείου
    rows = cursor.fetchall()
    results = [
        {"did": row[0], "doc_number": row[1], "date": row[2], "filepath": row[3]}
        for row in rows
    ]
    return jsonify({"results": results})

@app.route('/get_documents', methods=['GET'])
def get_documents():
    try:
        cursor.execute("SELECT did, filename FROM document ORDER BY id DESC LIMIT 50")  # τελευταίες 50 εγγραφές
        rows = cursor.fetchall()
        results = [{"did": row[0], "filepath": row[1]} for row in rows]
        return jsonify({"results": results})
    except Exception as e:
        logging.error(f"Error in /get_documents: {e}")
        return jsonify({"results": []}), 500





@app.route('/query_documents', methods=['POST'])
def query_documents():
    try:
        data = request.json or {}
        query_type = data.get('queryType', 'all')

        if query_type == 'did_only':
            cursor.execute("SELECT did FROM document")
            rows = cursor.fetchall()
            results = [{"did": row[0]} for row in rows]
        else:
            cursor.execute("SELECT did, ucid, doc_number, date FROM document")
            rows = cursor.fetchall()
            results = [
                {"did": row[0], "ucid": row[1], "doc_number": row[2], "date": row[3]}
                for row in rows
            ]
        return jsonify({"results": results})
    except Exception as e:
        logging.error(f"Error in /query_documents: {e}")
        return jsonify({"results": []}), 500

@app.route('/start_batch_process', methods=['POST'])
def start_batch_process():
    folder_path = r"C:\WPI\Aposibiesmena\EP"  # Το path σου


    if not os.path.exists(folder_path):
        return jsonify({"message": "Ο φάκελος δεν βρέθηκε."}), 400

    xml_files = []
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.xml'):
                full_path = os.path.join(root_dir, file)
                xml_files.append(full_path)

    if not xml_files:
        return jsonify({"message": "Δεν βρέθηκαν αρχεία XML."}), 400

    started = start_processing_thread(xml_files)
    if not started:
        return jsonify({'message': 'Η επεξεργασία ήδη τρέχει.'}), 400

    return jsonify({'message': f'Ξεκίνησε η επεξεργασία {len(xml_files)} αρχείων.'})

@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/information')
def information():
    return render_template('information.html')

@app.route('/database')
def database():
    try:
        # Πόσες εγγραφές ανά σελίδα
        per_page = 10

        # Παίρνουμε την τρέχουσα σελίδα
        page = request.args.get('page', 1, type=int)
        offset = (page - 1) * per_page

        # Φέρε 15 εγγραφές
        cursor.execute(
            """
            SELECT did, ucid, doc_number, kind, state, date, family_id, status,
                   lang, size_description, size_description_pars, size_description_words,
                   how_many_claims, date_produced, abstract_size_chars, abstract_word_count
            FROM document
            LIMIT %s OFFSET %s
            """,
            (per_page, offset)
        )
        rows = cursor.fetchall()

        # Σύνολο εγγραφών
        cursor.execute("SELECT COUNT(*) FROM document")
        total_rows = cursor.fetchone()[0]
        total_pages = (total_rows + per_page - 1) // per_page

        return render_template(
            'database.html',
            rows=rows,
            page=page,
            total_pages=total_pages
        )

    except Exception as e:
        logging.error(f"/database error: {e}")
        return render_template('database.html', rows=[], page=1, total_pages=1)


@app.route('/list_uploaded_files', methods=['GET'])
def list_uploaded_files():
    base = "uploaded_files"
    result = []

    for root, dirs, files in os.walk(base):
        rel_path = os.path.relpath(root, base)

        result.append({
            "path": rel_path,
            "dirs": dirs,
            "files": files
        })

    return jsonify(result)

@app.route("/get_files", methods=["GET"])
def get_files():
    base_dir = "uploaded_files"
    requested_path = request.args.get("path", "").strip("/")

    # Full path στο σύστημα
    full_path = os.path.join(base_dir, requested_path)

    if not os.path.exists(full_path):
        return jsonify({"error": "Path does not exist"}), 400

    items = []

    for entry in os.scandir(full_path):
        item = {
            "name": entry.name,
            "type": "folder" if entry.is_dir() else "file",
            "path": os.path.join(requested_path, entry.name).replace("\\", "/"),
            "size": "",
            "date": ""
        }

        # Μέγεθος για αρχεία
        if entry.is_file():
            size_kb = os.path.getsize(entry.path) // 1024
            item["size"] = f"{size_kb} KB"

        # Ημερομηνία αλλαγής
        item["date"] = time.strftime(
            "%Y-%m-%d",
            time.localtime(entry.stat().st_mtime)
        )

        items.append(item)

    return jsonify(items)






# -------- INITIALIZATION -------- #
if __name__ == '__main__':
    try:
        initialize_state(cursor, db)
        initialize_format(cursor, db)
        initialize_loadsource(cursor, db)
        initialize_kind(cursor, db)
        initialize_scheme(cursor, db)
        initialize_role(cursor, db)
        initialize_status(cursor, db)

        app.run(debug=True)
    except Exception as e:
        logging.critical(f" Πρόβλημα κάτα την εκκίνηση: {e}")
        exit(1)
