
from flask import Flask, render_template, jsonify, request
from zipfile import ZipFile
import tempfile
import shutil
import os
import xml.etree.ElementTree as ET
import mysql.connector
import threading
import time
import logging
from datetime import datetime

from Ptyxiaki.abstract import create_abstract_table, insert_abstract
from Ptyxiaki.country import create_country_table, initialize_country
from Ptyxiaki.description import create_description_table, insert_description
# from Ptyxiaki.abstract import create_abstract_table, insert_abstract
# from Ptyxiaki.country import create_country_table, initialize_country
from Ptyxiaki.role import initialize_role, create_role_table
from Ptyxiaki.save_query import create_saved_sql_queries_table
from Ptyxiaki.scheme import initialize_scheme, create_scheme_table
from Ptyxiaki.kind import initialize_kind, create_kind_table
from Ptyxiaki.status import initialize_status, create_status_table
from title import insert_title, create_title_table
from parties import insert_parties, create_parties_table
from claims import insert_claims, create_claims_table
from classification import insert_classification, create_classification_table
from document import process_document, create_document_table
from lang import initialize_lang, create_lang_table
from format import initialize_format, create_format_table
from loadsource import initialize_loadsource, create_loadsource_table


# Εδώ κάνουμε την global σύνδεση για την βάση δεδομένων.

def get_db_cursor():
    conn = mysql.connector.connect(
        host="localhost",
        user="admin",
        password="admin",
        database="epdatabase"
    )
    return conn, conn.cursor(buffered=True)



logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder='html') # na trexei prwto gia na arxikopoihsoume thn vash dedomemenw me fk
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 5GB  # megisto 10GB gia na mhn epivarinoume to request

#syndesi me thn vasi
try:
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
        password="admin",
        database="epdatabase"
    )

    cursor = db.cursor()  # o controller tis vasis

# exception an den vrethei h vasi
except mysql.connector.Error as err:
    logging.critical(f" Σφάλμα σύνδεσης στη βάση δεδομένων: {err}")
    raise SystemExit(1)

#telos me syndesi vasis kai exception


processing_thread = None
processing_lock = threading.Lock()
running = False
paused = False
stopped = False
progress_percentage = 0
zip_progress = 0
zip_total = 0
upload_progress = 0
upload_total = 0
processing_state = "idle"
current_phase = "idle"
batch_count = 0
processing_finished = False




BAD_FILES_LOG = "bad_files.log" # Metavliti gia to arxeio errors

#einai mia methothodo gia insert, an kati paei lathos kanei rollback
def safe_insert(query, params, cursor, db, context="Insert"):

    try:
        cursor.execute(query, params)
    except Exception as e:
        db.rollback()
        logging.error(f" {context} failed: {e}")


#tin xristimopoioume gia thn statistiki analysh sto information. Mas dinei tis evdomades px 15-22 3h evdomada ktl
def get_week_number(date_obj: datetime) -> int:

    return date_obj.isocalendar().week


#ipologismos statistikos evdomadon apo tin vasi
def calculate_week_stats_from_db(cursor):

    week_counts = [0] * 12  # 12 θέσεις, μία για κάθε εβδομάδα

    try:
        cursor.execute("SELECT date FROM document")
        rows = cursor.fetchall()
    except Exception as e:
        logging.error(f" Σφάλμα ανάγνωσης ημερομηνιών από document: {e}")
        return week_counts

    for (date_value,) in rows:
        if not date_value:
            continue

        # sinithos erxetai kati san datetime apo thn vasi
        if isinstance(date_value, datetime):
            date_obj = date_value
        else:
            # an einai str dokimazoume 2 format
            date_obj = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    date_obj = datetime.strptime(str(date_value), fmt)
                    break
                except ValueError:
                    continue
            if date_obj is None:
                continue

        week_num = get_week_number(date_obj)
        if 1 <= week_num <= 12:
            week_counts[week_num - 1] += 1

    return week_counts

# xrisimopoioiume gia tous mines, pirame tin function pou eixame gia tis evdomades kai thn
def calculate_month_stats_from_db(cursor, year=None):

    if year is None:
        year = datetime.now().year

    month_counts = [0] * 12  # 12 μήνες

    try:
        cursor.execute("SELECT date FROM document")
        rows = cursor.fetchall()
    except Exception as e:
        logging.error(f" Σφάλμα ανάγνωσης ημερομηνιών από document (month stats): {e}")
        return month_counts, year

    for (date_value,) in rows:
        if not date_value:
            continue


        if isinstance(date_value, datetime):
            date_obj = date_value
        else:

            date_obj = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    date_obj = datetime.strptime(str(date_value), fmt)
                    break
                except ValueError:
                    continue
            if date_obj is None:
                continue


        if date_obj.year != year:
            continue

        month_idx = date_obj.month - 1  # 1–12 -> 0–11
        month_counts[month_idx] += 1

    return month_counts, year

# trexei ola ta xml, kai ta epexergazetai ena ena
def process_files(files):
    global running, paused, stopped, progress_percentage,current_phase

    thread_db = None
    thread_cursor = None

    try:
        # κάθε thread θέλει δική του σύνδεση
        thread_db = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="admin",
            database="epdatabase"
        )
        thread_cursor = thread_db.cursor()

        total_files = len(files)

        for idx, file_path in enumerate(files, start=1):

            # STOP
            with processing_lock:
                if stopped:
                    logging.info("🛑 Διακοπή διαδικασίας από χρήστη.")
                    break

            # PAUSE
            while True:
                with processing_lock:
                    if stopped:
                        return
                    if not paused:
                        break
                time.sleep(0.3)

            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                did = process_document(file_path, thread_cursor, thread_db)

                if did is None:
                    logging.warning(f"DID δεν δημιουργήθηκε: {file_path}")
                    with open(BAD_FILES_LOG, "a", encoding="utf-8") as f:
                        f.write(f"{file_path} | DID not created\n")
                    continue

                insert_claims(did, root, thread_cursor, thread_db)
                insert_classification(did, root, thread_cursor, thread_db)
                insert_parties(did, root, thread_cursor, thread_db)
                insert_title(did, root, thread_cursor, thread_db)
                insert_abstract(did, root, thread_cursor, thread_db)
                insert_description(did, root, cursor, db)

                thread_db.commit()

                with processing_lock:
                    progress_percentage = int((idx / total_files) * 100)

                logging.info(f"📁 OK {file_path} ({progress_percentage}%)")

            except ET.ParseError as e:
                logging.error(f"Κακό XML: {file_path} – {e}")
                continue

            except Exception as e:
                logging.error(f"Σφάλμα σε {file_path}: {e}")
                try:
                    thread_db.rollback()
                except:
                    pass
                continue

    finally:
        try:
            if thread_cursor:
                thread_cursor.close()
            if thread_db:
                thread_db.close()
        except:
            pass

        with processing_lock:
            running = False
            paused = False
            if stopped:
                current_phase = "stopped"
            else:
                progress_percentage = 100
                current_phase = "done"

        logging.info("🧹 Τέλος processing thread.")




def start_processing_thread(files):
    global processing_thread, running, paused, stopped, progress_percentage
    global processing_finished

    with processing_lock:
        if running:
            return False

        running = True
        paused = False
        stopped = False
        progress_percentage = 0
        current_phase = "processing"
        processing_finished = False

    processing_thread = threading.Thread(
        target=process_files,
        args=(files,),
        daemon=True
    )
    processing_thread.start()
    return True


# edw xenkinae ta endpointsprocess_files
@app.route("/upload_zip", methods=["POST"])
def upload_zip():
    global running, paused, stopped
    global progress_percentage, zip_progress, zip_total, current_phase
    global processing_finished

    with processing_lock:
        running = False
        paused = False
        stopped = False
        progress_percentage = 0
        zip_progress = 0
        zip_total = 0
        current_phase = "upload"
        processing_finished = False

    uploaded = request.files.getlist("files")
    if not uploaded:
        return jsonify({"message": "Δεν επιλέχθηκε ZIP αρχείο."}), 400

    zip_file = uploaded[0]
    if not zip_file.filename.lower().endswith(".zip"):
        return jsonify({"message": "Το αρχείο δεν είναι ZIP."}), 400

    base_dir = "uploaded_files"
    os.makedirs(base_dir, exist_ok=True)

    zip_path = os.path.join(base_dir, zip_file.filename)
    zip_file.save(zip_path)

    extract_dir = os.path.join(
        base_dir,
        os.path.splitext(zip_file.filename)[0]
    )
    os.makedirs(extract_dir, exist_ok=True)

    # unzip + processing σε background
    threading.Thread(
        target=unzip_and_start_processing,
        args=(zip_path, extract_dir),
        daemon=True
    ).start()

    return jsonify({
        "message": "Upload ολοκληρώθηκε. Ξεκίνησε unzip.",
        "folder_name": os.path.splitext(zip_file.filename)[0]
    })


def unzip_and_start_processing(zip_path, extract_dir):
    global zip_progress, zip_total, current_phase
    global processing_finished

    with processing_lock:
        current_phase = "unzip"
        zip_progress = 0
        zip_total = 0

    try:
        with ZipFile(zip_path, "r") as z:
            members = [m for m in z.namelist() if not m.endswith("/")]
            zip_total = len(members)

            extracted = 0
            for member in members:
                z.extract(member, extract_dir)
                extracted += 1
                zip_progress = int((extracted / max(zip_total, 1)) * 100)

        zip_progress = 100

        xml_files = []
        for root, _, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith(".xml"):
                    xml_files.append(os.path.join(root, f))

        if xml_files:
            with processing_lock:
                current_phase = "processing"
            start_processing_thread(xml_files)
        else:
            with processing_lock:
                current_phase = "done"
                processing_finished = True


    except Exception:
        logging.exception("Unzip failed")
        with processing_lock:
            current_phase = "stopped"
            zip_progress = -1


@app.route("/upload_progress", methods=["GET"])
def upload_progress_status():
    global upload_progress, upload_total
    return jsonify({"progress": upload_progress, "total": upload_total})


@app.route("/upload_zip_chunk", methods=["POST"])
def upload_zip_chunk():
    global upload_progress, upload_total
    global zip_progress, zip_total
    global progress_percentage
    global running, paused, stopped
    global current_phase
    global processing_finished

    # =========================
    # Reset state (start upload)
    # =========================
    with processing_lock:
        running = False
        paused = False
        stopped = False

        upload_progress = 0
        upload_total = 0

        zip_progress = 0
        zip_total = 0

        progress_percentage = 0
        current_phase = "upload"
        processing_finished = False

    # =========================
    # Validate input
    # =========================
    chunk = request.files.get("chunk")
    if chunk is None:
        return jsonify({"message": "Missing chunk"}), 400

    upload_id = request.form.get("upload_id")
    filename = request.form.get("filename")

    try:
        index = int(request.form.get("index"))
        total = int(request.form.get("total"))
    except:
        return jsonify({"message": "Bad index/total"}), 400

    if not upload_id or not filename or total <= 0 or index < 0:
        return jsonify({"message": "Invalid upload data"}), 400

    # =========================
    # Save chunk
    # =========================
    base_dir = "uploaded_files"
    os.makedirs(base_dir, exist_ok=True)

    chunks_dir = os.path.join(base_dir, "_chunks", upload_id)
    os.makedirs(chunks_dir, exist_ok=True)

    part_path = os.path.join(chunks_dir, f"part_{index:06d}")
    chunk.save(part_path)

    upload_total = total
    upload_progress = int(((index + 1) / total) * 100)

    # =========================
    # Not last chunk → done
    # =========================
    if index < total - 1:
        return jsonify({
            "message": "Chunk received",
            "progress": upload_progress
        })


    final_zip_path = os.path.join(base_dir, filename)
    if os.path.exists(final_zip_path):
        os.remove(final_zip_path)

    try:
        with open(final_zip_path, "wb") as out:
            for i in range(total):
                part_file = os.path.join(chunks_dir, f"part_{i:06d}")
                if not os.path.exists(part_file):
                    return jsonify({"message": f"Missing chunk {i}"}), 500
                with open(part_file, "rb") as inp:
                    shutil.copyfileobj(inp, out)

        shutil.rmtree(chunks_dir, ignore_errors=True)

    except Exception as e:
        logging.exception("Chunk merge failed")
        return jsonify({"message": f"Merge failed: {e}"}), 500


    extract_dir = os.path.join(base_dir, os.path.splitext(filename)[0])
    os.makedirs(extract_dir, exist_ok=True)

    with processing_lock:
        current_phase = "unzip"
        zip_progress = 1
        zip_total = 0

    try:
        with ZipFile(final_zip_path, "r") as z:
            members = [m for m in z.namelist() if not m.endswith("/")]
            zip_total = len(members)

            extracted = 0
            for member in members:
                z.extract(member, extract_dir)
                extracted += 1
                zip_progress = int((extracted / max(zip_total, 1)) * 100)

        zip_progress = 100

    except Exception as e:
        logging.exception("Unzip failed")
        with processing_lock:
            current_phase = "stopped"
        return jsonify({"message": f"Unzip failed: {e}"}), 500


    xml_files = []
    for root_dir, _, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith(".xml"):
                xml_files.append(os.path.join(root_dir, f))

    if not xml_files:
        with processing_lock:
            current_phase = "done"
        return jsonify({"message": "No XML files found"}), 400


    with processing_lock:
        current_phase = "processing"

    started = start_processing_thread(xml_files)
    if not started:
        return jsonify({"message": "Processing already running"}), 400

    upload_progress = 100

    return jsonify({
        "message": f"Upload ολοκληρώθηκε. Ξεκίνησε processing {len(xml_files)} XML.",
        "folder_name": os.path.splitext(filename)[0]
    })



@app.route("/upload_folder", methods=["POST"])
def upload_folder():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"message": "Δεν επιλέχθηκαν αρχεία."}), 400

    folder_path = os.path.join("uploaded_files")
    os.makedirs(folder_path, exist_ok=True)

    saved_files = []
    try:
        for file in files:
            file_path = os.path.join(folder_path, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            saved_files.append(file_path)
    except Exception as e:
        logging.error(f" Σφάλμα κατά την αποθήκευση αρχείων upload_folder: {e}")
        return jsonify({"message": f"Σφάλμα κατά την αποθήκευση: {str(e)}"}), 500

    started = start_processing_thread(saved_files)
    if not started:
        return jsonify({"message": "Η επεξεργασία ήδη τρέχει."}), 400

    return jsonify({"message": f"Ξεκίνησε η επεξεργασία {len(saved_files)} αρχείων."})

@app.route("/control", methods=["POST"])
def control():
    global running, paused, stopped, current_phase

    data = request.json or {}
    action = data.get("action")

    with processing_lock:
        if action == "pause" and running and not paused:
            paused = True
            return jsonify({"message": "Paused"})

        if action == "continue" and running and paused:
            paused = False
            return jsonify({"message": "Continued"})

        if action == "stop" and running:
            stopped = True
            paused = False
            current_phase = "stopped"
            return jsonify({"message": "Stopped"})

    return jsonify({"message": "Invalid action"}), 400



@app.route("/get_progress", methods=["GET"])
def get_progress():
    with processing_lock:
        if paused:
            status = "paused"
        elif running:
            status = "running"
        elif stopped:
            status = "stopped"
        else:
            status = "idle"

        return jsonify({
            "progress": progress_percentage,
            "zip_progress": zip_progress,
            "zip_total": zip_total,
            "status": status,
            "phase": current_phase,
            "batch_count": batch_count,
            "finished": processing_finished

        })


@app.route("/qquery_documents", methods=["POST"])
def qquery_documents_post():

    cursor.execute("SELECT did, doc_number, date, filename FROM document")
    rows = cursor.fetchall()
    results = [
        {"did": row[0], "doc_number": row[1], "date": row[2], "filepath": row[3]}
        for row in rows
    ]
    return jsonify({"results": results})

@app.route("/get_documents", methods=["GET"])
def get_documents():
    conn, cur = get_db_cursor()
    try:
        cur.execute(
            "SELECT did, filename FROM document ORDER BY id DESC LIMIT 50"
        )
        rows = cur.fetchall()
        results = [{"did": r[0], "filepath": r[1]} for r in rows]
        return jsonify({"results": results})
    except Exception as e:
        logging.error(f"/get_documents error: {e}")
        return jsonify({"results": []}), 500
    finally:
        cur.close()
        conn.close()




@app.route("/query_documents", methods=["POST"])
def query_documents():

    try:
        data = request.json or {}
        query_type = data.get("queryType", "all")

        if query_type == "did_only":
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


@app.route("/start_batch_process", methods=["POST"])
def start_batch_process():

    folder_path = r"C:\WPI\Aposibiesmena\EP"  # Το path σου

    if not os.path.exists(folder_path):
        return jsonify({"message": "Ο φάκελος δεν βρέθηκε."}), 400

    xml_files = []
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(".xml"):
                full_path = os.path.join(root_dir, file)
                xml_files.append(full_path)

    if not xml_files:
        return jsonify({"message": "Δεν βρέθηκαν αρχεία XML."}), 400


    started = start_processing_thread(xml_files)
    if not started:
        return jsonify({"message": "Η επεξεργασία ήδη τρέχει."}), 400

    return jsonify({"message": f"Ξεκίνησε η επεξεργασία {len(xml_files)} αρχείων."})


@app.route("/index")
def home():
    return render_template("index.html")


@app.route("/information")
def information():
    return render_template("information.html")


@app.route("/database")
def database():
    # -----------------------------
    # 1. READ PARAMS
    # -----------------------------
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Whitelist per_page
    if per_page not in (25, 50, 100):
        per_page = 50

    if page < 1:
        page = 1

    offset = (page - 1) * per_page

    conn, cur = get_db_cursor()

    try:

        cur.execute("SELECT COUNT(*) FROM document")
        total_rows = cur.fetchone()[0]
        total_pages = max(1, (total_rows + per_page - 1) // per_page)

        # Clamp page
        if page > total_pages:
            page = total_pages
            offset = (page - 1) * per_page


        cur.execute("""
            SELECT
                d.did,
                d.ucid,
                d.doc_number,
                d.kind,
                d.country,
                d.date,
                d.family_id,
                d.status,
                d.lang,
                d.size_description,
                d.size_description_pars,
                d.size_description_words,
                d.how_many_claims,
                d.date_produced
            FROM document d
            ORDER BY d.did DESC
            LIMIT %s OFFSET %s
        """, (per_page, offset))

        rows = cur.fetchall()

        # -----------------------------
        # 4. RENDER
        # -----------------------------
        return render_template(
            "database.html",
            rows=rows,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            total_rows=total_rows
        )

    except Exception as e:
        logging.error(f"/database error: {e}", exc_info=True)
        return render_template(
            "database.html",
            rows=[],
            page=1,
            per_page=50,
            total_pages=1,
            total_rows=0
        )

    finally:
        cur.close()
        conn.close()




@app.route("/list_uploaded_files", methods=["GET"])
def list_uploaded_files():

    base = "uploaded_files"
    result = []

    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if not d.startswith("_")]
        rel_path = os.path.relpath(root, base)

        result.append(
            {
                "path": rel_path,
                "dirs": dirs,
                "files": files,
            }
        )

    return jsonify(result)


@app.route("/get_files", methods=["GET"])
def get_files():

    base_dir = "uploaded_files"
    requested_path = request.args.get("path", "").strip("/")

    full_path = os.path.join(base_dir, requested_path)

    if not os.path.exists(full_path):
        return jsonify({"error": "Path does not exist"}), 400

    items = []

    for entry in os.scandir(full_path):

        if entry.name.startswith("_"):
            continue

        if entry.is_file() and entry.name.lower().endswith(".zip"):
            continue

        item = {
            "name": entry.name,
            "type": "folder" if entry.is_dir() else "file",
            "path": os.path.join(requested_path, entry.name).replace("\\", "/"),
            "size": "",
            "date": "",
        }

        if entry.is_file():
            size_kb = os.path.getsize(entry.path) // 1024
            item["size"] = f"{size_kb} KB"

        item["date"] = time.strftime("%Y-%m-%d", time.localtime(entry.stat().st_mtime))
        items.append(item)

    return jsonify(items)


@app.route("/stats/uploads_per_week", methods=["GET"])
def uploads_per_week():

    conn, cur = get_db_cursor()
    try:
        counts = calculate_week_stats_from_db(cur)
    finally:
        cur.close()
        conn.close()

    labels = [f"Εβδ. {i}" for i in range(1, 13)]
    return jsonify({"labels": labels, "counts": counts})


def calculate_month_stats_from_db(cursor, year=None):

    if year is None:
        year = datetime.now().year

    month_counts = [0] * 12  # 12 μήνες

    try:
        cursor.execute("SELECT date FROM document")
        rows = cursor.fetchall()
    except Exception as e:
        logging.error(f" Σφάλμα ανάγνωσης ημερομηνιών από document (month stats): {e}")
        return month_counts, year

    for (date_value,) in rows:
        if not date_value:
            continue

        if isinstance(date_value, datetime):
            date_obj = date_value
        else:
            # Αν είναι string, δοκιμάζουμε με 2 formats
            date_obj = None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
                try:
                    date_obj = datetime.strptime(str(date_value), fmt)
                    break
                except ValueError:
                    continue
            if date_obj is None:
                continue

        if date_obj.year != year:
            continue

        month_idx = date_obj.month - 1  # 1–12 -> 0–11
        month_counts[month_idx] += 1

    return month_counts, year

# ----------------------------------------------------

@app.route("/zip_progress", methods=["GET"])
def zip_progress_status():
    return jsonify({
        "progress": zip_progress,
        "total": zip_total
    })





# Κεντρική συνάρτηση που τρέχει ένα SELECT query πάνω στη βάση
def run_sql_query(sql_text, cursor):


    sql_clean = (sql_text or "").strip()
    if not sql_clean:
        return None, None, "Empty query.", 0.0

    # Βασικός έλεγχος ασφαλείας – επιτρέπουμε μόνο SELECT
    lowered = sql_clean.lower()
    if not lowered.startswith("select"):
        return None, None, "Only SELECT statements are allowed.", 0.0

    start = time.time()
    try:
        cursor.execute(sql_clean)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        elapsed = time.time() - start
        return cols, rows, None, elapsed
    except Exception as e:
        elapsed = time.time() - start
        return None, None, str(e), elapsed


# Global state για να θυμόμαστε το τελευταίο query & αποτελέσματα
last_query_state = {
    "sql": "",
    "columns": [],
    "rows": [],
    "error": None,
    "elapsed": 0.0,
    "row_count": 0,
}

@app.route("/workspace", methods=["GET", "POST"])
def workspace():
    global last_query_state

    active_tab = "query"

    if request.method == "POST":
        sql_input = request.form.get("sql_input", "").strip()
        active_tab = request.form.get("active_tab", "query")

        conn, cur = get_db_cursor()
        try:
            cols, rows, err, elapsed = run_sql_query(sql_input, cur)
        finally:
            cur.close()
            conn.close()

        last_query_state.update({
            "sql": sql_input,
            "columns": cols or [],
            "rows": rows or [],
            "error": err,
            "elapsed": elapsed,
            "row_count": len(rows or []),
        })

    return render_template(
        "workspace.html",
        active_tab=active_tab,
        sql_input=last_query_state["sql"],
        columns=last_query_state["columns"],
        rows=last_query_state["rows"],
        error=last_query_state["error"],
        elapsed=last_query_state["elapsed"],
        row_count=last_query_state["row_count"],
    )



@app.post("/workspace_ajax")
def workspace_ajax():
    sql_input = request.form.get("sql_input", "").strip()

    conn, cur = get_db_cursor()
    try:
        cols, rows, err, elapsed = run_sql_query(sql_input, cur)
    finally:
        cur.close()
        conn.close()

    return {
        "sql": sql_input,
        "columns": cols or [],
        "rows": rows or [],
        "error": err,
        "elapsed": elapsed,
        "row_count": len(rows or [])
    }

@app.post("/api/search")
def api_search():
    conn, cur = get_db_cursor()
    try:
        payload = request.get_json(silent=True) or {}
        criteria = payload.get("criteria", payload)


        def as_int(x):
            try:
                return int(x)
            except:
                return None

        page = as_int(payload.get("page")) or 1
        if page < 1:
            page = 1

        page_size = as_int(payload.get("page_size")) or 500

        # allow-list sizes (recommended)
        allowed_sizes = {10, 100, 1000, 10000}
        if page_size not in allowed_sizes:
            # fallback safely
            page_size = 500

        # hard cap
        page_size = max(1, min(page_size, 10000))

        offset = (page - 1) * page_size


        where = []
        params = []

        # YEAR RANGE
        yf = as_int(criteria.get("year_from"))
        yt = as_int(criteria.get("year_to"))

        if yf is not None:
            where.append("d.date >= %s")
            params.append(f"{yf}-01-01")

        if yt is not None:
            where.append("d.date <= %s")
            params.append(f"{yt}-12-31")

        # STATE FILTER (στον κώδικά σου λέγεται state αλλά πάει στο d.lang)
        raw_states = criteria.get("state")
        if raw_states:
            if not isinstance(raw_states, list):
                raw_states = [raw_states]

            state_ids = []
            for item in raw_states:
                iv = as_int(item)
                if iv is not None:
                    state_ids.append(iv)

            if state_ids:
                placeholders = ",".join(["%s"] * len(state_ids))
                where.append(f"d.lang IN ({placeholders})")
                params.extend(state_ids)
            else:
                return jsonify({
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_rows": 0,
                    "total_pages": 1,
                    "error": None,
                    "elapsed": 0.0
                })

        # KIND FILTER
        raw_kinds = criteria.get("kind")
        if raw_kinds:
            if not isinstance(raw_kinds, list):
                raw_kinds = [raw_kinds]

            kind_ids = []
            for k in raw_kinds:
                iv = as_int(k)
                if iv is not None:
                    kind_ids.append(iv)

            if kind_ids:
                placeholders = ",".join(["%s"] * len(kind_ids))
                where.append(f"d.kind IN ({placeholders})")
                params.extend(kind_ids)

        # MIN CLAIMS
        mc = as_int(criteria.get("min_claims"))
        if mc is not None:
            where.append("d.how_many_claims >= %s")
            params.append(mc)

        # MIN ABSTRACT WORDS
        maw = as_int(criteria.get("min_abstract_words"))
        if maw is not None:
            where.append("""
                EXISTS (
                    SELECT 1
                    FROM abstract a
                    WHERE a.DID = d.DID
                      AND a.abstract_words_count >= %s
                )
            """)

            params.append(maw)

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        # -----------------------------
        # 3) COUNT query (for pages)
        # -----------------------------
        count_sql = f"""
            SELECT COUNT(*)
            FROM document d
            {where_sql}

            """
        cur.execute(count_sql, params)
        total_rows = int(cur.fetchone()[0] or 0)
        total_pages = max(1, (total_rows + page_size - 1) // page_size)

        # clamp page if beyond total_pages
        if page > total_pages:
            page = total_pages
            offset = (page - 1) * page_size

        # -----------------------------
        # 4) Data query
        # -----------------------------
        data_sql = f"""
            SELECT
    d.DID,
    d.ucid,
    d.doc_number,
    d.date,
    d.family_id,
    d.status,
    k.name AS kind_name,
    c.name AS country_name,
    l.name AS lang_name,
    d.how_many_claims,
    d.date_produced
FROM document d
LEFT JOIN kind     k ON k.KID = d.kind
LEFT JOIN country  c ON c.CID = d.country
LEFT JOIN lang     l ON l.CID = d.lang
{where_sql}
ORDER BY d.DID ASC
LIMIT %s OFFSET %s

        """
        cur.execute(data_sql, params + [page_size, offset])
        rows = cur.fetchall()
        columns = [col[0] for col in cur.description]

        return jsonify({
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "page": page,
            "page_size": page_size,
            "total_rows": total_rows,
            "total_pages": total_pages,
            "error": None,
            "elapsed": 0.0
        })

    except Exception as e:
        logging.error("/api/search ERROR", exc_info=True)
        return jsonify({
            "columns": [],
            "rows": [],
            "row_count": 0,
            "page": 1,
            "page_size": 500,
            "total_rows": 0,
            "total_pages": 1,
            "error": str(e),
            "elapsed": 0.0
        }), 500

    finally:
        cur.close()
        conn.close()



@app.get("/api/stats")
def api_stats():
    stat_type = request.args.get("type", "year")

    try:
        if stat_type == "year":
            cursor.execute("""
                SELECT YEAR(d.date) AS label, COUNT(*) AS value
                FROM document d
                WHERE d.date IS NOT NULL
                GROUP BY YEAR(d.date)
                ORDER BY YEAR(d.date)
            """)

        elif stat_type == "lang":
            cursor.execute("""
                SELECT s.code AS label, COUNT(*) AS value
                FROM document d
                JOIN lang s ON s.id = d.lang
                GROUP BY s.code
                ORDER BY value DESC
            """)

        elif stat_type == "kind":
            cursor.execute("""
                SELECT k.code AS label, COUNT(*) AS value
                FROM document d
                JOIN kind k ON k.id = d.kind
                GROUP BY k.code
                ORDER BY value DESC
            """)

        else:
            return jsonify({"error": "Unknown stat type"}), 400

        rows = cursor.fetchall()

        return jsonify({
            "labels": [str(r[0]) for r in rows],
            "values": [r[1] for r in rows]
        })

    except Exception as e:
        logging.error(f"/api/stats error: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/kinds")
def api_kinds():
    conn, cur = get_db_cursor()
    cur.execute("SELECT KID, name FROM kind ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.get("/api/states")
def api_states():
    conn, cur = get_db_cursor()
    cur.execute("SELECT CID, name FROM lang ORDER BY name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.get("/api/stats/heatmap")
def api_stats_heatmap():
    cursor.execute("""
        SELECT
            s.name AS country,
            k.name AS kind,
            COUNT(*) AS total
        FROM document d
        JOIN lang s ON s.CID = d.lang
        JOIN kind  k ON k.KID = d.kind
        GROUP BY s.name, k.name
        ORDER BY s.name, k.name
    """)

    rows = cursor.fetchall()

    return jsonify([
        {
            "country": r[0],
            "kind": r[1],
            "total": r[2]
        }
        for r in rows
    ])


@app.get("/api/stats/kind-by-country")
def stats_kind_by_country():
    try:
        sql = """
            SELECT
    s.name AS country,
    k.name AS kind,
    COUNT(*) AS total
FROM document d
JOIN lang s ON s.CID = d.lang
JOIN kind  k ON k.KID = d.kind
GROUP BY s.name, k.name
ORDER BY s.name, k.name;

        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        result = []
        for lang, kind, total in rows:
            result.append({
                "country": lang,   # κρατάμε country για consistency στο JS
                "kind": kind,
                "total": total
            })

        return jsonify(result)

    except Exception as e:
        logging.error(f"/api/stats/kind-by-country error: {e}")
        return jsonify([]), 500





def clean_uploaded_files():
    base_dir = "uploaded_files"

    if os.path.exists(base_dir):
        try:
            shutil.rmtree(base_dir)
            logging.info("🧹 Καθαρίστηκε ο φάκελος uploaded_files")
        except Exception as e:
            logging.error(f" Αποτυχία καθαρισμού uploaded_files: {e}")

    os.makedirs(base_dir, exist_ok=True)


    #ΣΩΣΤΟ ΣΤΑΤΙΣΤΙΚΟ 1

@app.get("/api/stats/claims-vs-abstract")
def api_claims_vs_abstract():
    conn, cur = get_db_cursor()

    try:
        cur.execute("""
            SELECT
                d.size_description_words AS abstract_words,
                d.how_many_claims
            FROM document d
            WHERE
                d.size_description_words IS NOT NULL
                AND d.how_many_claims IS NOT NULL
                AND d.size_description_words > 0
                AND d.how_many_claims > 0
            LIMIT 5000
        """)

        rows = cur.fetchall()

        return jsonify({
            "points": [
                {"x": int(r[0]), "y": int(r[1])}
                for r in rows
            ]
        })

    except Exception as e:
        logging.error(f"/api/stats/claims-vs-abstract error: {e}", exc_info=True)
        return jsonify({"points": [], "error": str(e)}), 500

    finally:
        cur.close()
        conn.close()



#ΣΩΣΤΟ ΣΤΑΤΙΣΤΙΚΟ 2
@app.get("/api/stats/claims-intensity")
def stats_claims_intensity():
    conn, cur = get_db_cursor()
    try:
        ep_id = get_country_id(cur, "EP")

        country_filter = ""
        params = []
        if ep_id is not None:
            country_filter = "AND d.country = %s"
            params.append(ep_id)

        cur.execute(f"""
            SELECT
                k.name AS kind,
                AVG(d.how_many_claims) AS avg_claims,
                COUNT(*) AS patent_count
            FROM document d
            JOIN kind k ON k.KID = d.kind
            WHERE d.how_many_claims IS NOT NULL
              {country_filter}
            GROUP BY k.name
            ORDER BY avg_claims DESC
        """, params)

        rows = cur.fetchall()
        labels = [r[0] for r in rows]
        values = [float(r[1]) if r[1] is not None else 0.0 for r in rows]
        counts = [int(r[2]) for r in rows]

        return jsonify({"labels": labels, "values": values, "counts": counts})

    except Exception as e:
        logging.error(f"/api/stats/claims-intensity error: {e}", exc_info=True)
        return jsonify({"labels": [], "values": [], "counts": [], "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()



#ΣΩΣΤΟ ΣΤΑΤΙΣΤΙΚΟ 3

@app.get("/api/stats/complexity-score")
def api_complexity_score():
    conn, cur = get_db_cursor()

    try:
        cur.execute("""
            SELECT
                d.DID,
                d.how_many_claims,
                MAX(a.abstract_words_count) AS abstract_word_count,
                (
                    LOG(1 + d.how_many_claims) *
                    LOG(1 + MAX(a.abstract_words_count))
                ) AS complexity_score
            FROM document d
            JOIN abstract a ON a.DID = d.DID
            WHERE
                d.how_many_claims > 0
                AND a.abstract_words_count > 0
            GROUP BY d.DID, d.how_many_claims
            ORDER BY complexity_score DESC
            LIMIT 1000
        """)

        rows = cur.fetchall()

        return jsonify({
            "rows": [
                {
                    "did": r[0],
                    "claims": int(r[1]),
                    "abstract_words": int(r[2]),
                    "complexity": float(r[3])
                }
                for r in rows
            ]
        })

    finally:
        cur.close()
        conn.close()


#ΣΩΣΤΟ ΣΤΑΤΙΣΤΙΚΟ 6
@app.get("/api/stats/maturity-over-time")
def api_maturity_over_time():
    conn, cur = get_db_cursor()

    try:
        cur.execute("""
            SELECT
                YEAR(d.date) AS year,
                COUNT(*) AS documents,
                AVG(
                    (d.how_many_claims * 0.6) +
                    (IFNULL(a.abstract_words_count, 0) * 0.4 / 100)
                ) AS maturity
            FROM document d
            LEFT JOIN abstract a ON a.DID = d.DID
            WHERE d.date IS NOT NULL
              AND d.country = (
                  SELECT CID FROM country WHERE name = 'EP'
              )
            GROUP BY YEAR(d.date)
            ORDER BY year
        """)

        rows = cur.fetchall()

        years = []
        values = []

        for year, docs, maturity in rows:
            if year is not None and maturity is not None:
                years.append(year)
                values.append(round(float(maturity), 3))

        return jsonify({
            "years": years,
            "values": values
        })

    except Exception as e:
        logging.error(f"maturity-over-time error: {e}", exc_info=True)
        return jsonify({"years": [], "values": []}), 500

    finally:
        cur.close()
        conn.close()

#ΣΩΣΤΟ ΣΤΑΤΙΣΤΙΚΟ 4
@app.get("/api/stats/patents-per-month")
def api_patents_per_month():
    conn, cur = get_db_cursor()

    try:
        ep_id = get_country_id(cur, "EP")

        cur.execute("""
            SELECT
                MONTH(d.date) AS m,
                COUNT(*) AS total
            FROM document d
            WHERE
                d.date IS NOT NULL
                AND d.country = %s
            GROUP BY m
        """, (ep_id,))

        rows = cur.fetchall()

        # 1..12
        month_counts = {int(m): int(c) for m, c in rows if m is not None}

        labels = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]

        values = [month_counts.get(i, 0) for i in range(1, 13)]

        total_patents = sum(values)
        avg = round(total_patents / 12, 2)

        return jsonify({
            "labels": labels,
            "values": values,
            "average": avg
        })

    except Exception as e:
        logging.error(e, exc_info=True)
        return jsonify({"labels": [], "values": [], "average": 0}), 500
    finally:
        cur.close()
        conn.close()


def get_country_id(cur, name: str):
    cur.execute("SELECT CID FROM country WHERE name = %s LIMIT 1", (name,))
    row = cur.fetchone()
    return row[0] if row else None



@app.get("/api/stats/monthly-growth-rate")
def api_monthly_growth_rate():
    conn, cur = get_db_cursor()
    try:
        ep_id = get_country_id(cur, "EP")

        country_filter = ""
        params = []
        if ep_id is not None:
            country_filter = "AND d.country = %s"
            params.append(ep_id)

        cur.execute(f"""
            SELECT
                DATE_FORMAT(d.date, '%%Y-%%m') AS year_month,
                COUNT(*) AS total
            FROM document d
            WHERE d.date IS NOT NULL
              {country_filter}
            GROUP BY year_month
            ORDER BY year_month
        """, params)

        rows = [(r[0], int(r[1])) for r in cur.fetchall() if r[0] is not None]

        if len(rows) < 2:
            return jsonify({"labels": [], "values": []})

        labels = []
        values = []

        prev_month, prev_total = rows[0]
        for month, total in rows[1:]:
            if prev_total <= 0:
                growth = 0.0
            else:
                growth = ((total - prev_total) / prev_total) * 100.0

            labels.append(month)
            values.append(growth)

            prev_total = total

        return jsonify({"labels": labels, "values": values})

    except Exception as e:
        logging.error(f"/api/stats/monthly-growth-rate error: {e}", exc_info=True)
        return jsonify({"labels": [], "values": [], "error": str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.get("/api/database/summary")
def database_summary():
    conn, cur = get_db_cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM document")
        documents = cur.fetchone()[0]

        # Φάκελοι από filesystem
        base = "uploaded_files"
        folders = sum(
            1 for root, dirs, _ in os.walk(base)
            if root != base
        )

        return jsonify({
            "documents": documents,
            "folders": folders,
            "timestamp": int(time.time())
        })
    finally:
        cur.close()
        conn.close()




@app.post("/api/documents/delete")
def api_documents_delete():
    payload = request.get_json(silent=True) or {}
    mode = (payload.get("mode") or "").strip().lower()

    if mode not in ("selected", "all"):
        return jsonify({"status": "error", "message": "Invalid mode"}), 400

    conn, cur = get_db_cursor()
    try:
        conn.start_transaction()


        if mode == "all":
            # Ένα καθαρό delete. CASCADE θα καθαρίσει τα παιδιά.
            cur.execute("DELETE FROM document")
            deleted_count = cur.rowcount
            conn.commit()
            return jsonify({"status": "ok", "deleted_count": deleted_count})


        dids = payload.get("dids", [])
        if not isinstance(dids, list) or not dids:
            return jsonify({"status": "error", "message": "No DIDs provided"}), 400

        # sanitize ints
        clean_dids = []
        for d in dids:
            try:
                clean_dids.append(int(d))
            except:
                return jsonify({"status": "error", "message": "Invalid DID in list"}), 400

        BATCH_SIZE = 500
        total_deleted = 0

        for i in range(0, len(clean_dids), BATCH_SIZE):
            batch = clean_dids[i:i + BATCH_SIZE]
            placeholders = ",".join(["%s"] * len(batch))
            cur.execute(f"DELETE FROM document WHERE DID IN ({placeholders})", batch)
            total_deleted += cur.rowcount

        conn.commit()
        return jsonify({"status": "ok", "deleted_count": total_deleted})

    except Exception as e:
        try:
            conn.rollback()
        except:
            pass

        # Πολύ σημαντικό: γράφουμε το πραγματικό error στο log για να το βλέπεις
        logging.error(f"/api/documents/delete failed: {e}", exc_info=True)

        return jsonify({
            "status": "error",
            "message": "Delete failed. Transaction rolled back."
        }), 500

    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass


@app.get("/api/documents/new")
def get_new_documents():
    after_did = request.args.get("after", type=int, default=0)

    conn, cur = get_db_cursor()
    try:
        cur.execute("""
            SELECT
                d.did,
                d.ucid,
                d.doc_number,
                d.kind,
                d.country,
                d.date,
                d.family_id,
                d.status,
                d.lang,
                d.size_description,
                d.size_description_pars,
                d.size_description_words,
                d.how_many_claims,
                d.date_produced
            FROM document d
            WHERE d.did > %s
            ORDER BY d.did DESC
        """, (after_did,))

        return jsonify(cur.fetchall())
    finally:
        cur.close()
        conn.close()




@app.route("/api/sql/save", methods=["POST"])
def save_sql_query():
    try:
        data = request.get_json(force=True)

        name = (data.get("name") or "").strip()
        sql_text = (data.get("sql_text") or "").strip()

        if not name or not sql_text:
            return jsonify({
                "error": "Name and SQL text are required."
            }), 400

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO saved_sql_queries (name, sql_text)
            VALUES (%s, %s)
        """, (name, sql_text))

        db.commit()

        return jsonify({
            "status": "ok",
            "id": cursor.lastrowid
        })

    except Exception as e:
        db.rollback()
        logging.error("save_sql_query failed", exc_info=True)

        return jsonify({
            "error": "Failed to save SQL query."
        }), 500


@app.get("/api/sql/list")
def list_sql_queries():
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            SID       AS id,
            name      AS name,
            sql_text  AS sql_text
        FROM saved_sql_queries
        ORDER BY SID DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    return jsonify(rows)

@app.delete("/api/sql/delete/<int:sid>")
def delete_sql_query(sid):
    try:
        cur = db.cursor()
        cur.execute(
            "DELETE FROM saved_sql_queries WHERE SID = %s",
            (sid,)
        )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception:
        db.rollback()
        logging.exception("delete_sql_query failed")
        return jsonify({"error": "Delete failed"}), 500


@app.put("/api/sql/rename/<int:sid>")
def rename_sql_query(sid):
    try:
        data = request.get_json(force=True)
        name = (data.get("name") or "").strip()

        if not name:
            return jsonify({"error": "Empty name"}), 400

        cur = db.cursor()
        cur.execute(
            "UPDATE saved_sql_queries SET name = %s WHERE SID = %s",
            (name, sid)
        )
        db.commit()
        return jsonify({"status": "ok"})
    except Exception:
        db.rollback()
        logging.exception("rename_sql_query failed")
        return jsonify({"error": "Rename failed"}), 500



if __name__ == "__main__":
    try:

        clean_uploaded_files()


        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        cursor.execute("DROP TABLE IF EXISTS description")
        cursor.execute("DROP TABLE IF EXISTS abstract")
        cursor.execute("DROP TABLE IF EXISTS title")
        cursor.execute("DROP TABLE IF EXISTS classification")
        cursor.execute("DROP TABLE IF EXISTS parties")
        cursor.execute("DROP TABLE IF EXISTS claims")
        cursor.execute("DROP TABLE IF EXISTS document")

        cursor.execute("DROP TABLE IF EXISTS kind")
        cursor.execute("DROP TABLE IF EXISTS lang")
        cursor.execute("DROP TABLE IF EXISTS country")
        cursor.execute("DROP TABLE IF EXISTS loadsource")
        cursor.execute("DROP TABLE IF EXISTS role")
        cursor.execute("DROP TABLE IF EXISTS status")
        cursor.execute("DROP TABLE IF EXISTS format")

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        # =====================
        # 2. CREATE LOOKUPS
        # =====================
        create_format_table(cursor, db)
        initialize_format(cursor, db)

        create_country_table(cursor, db)
        initialize_country(cursor, db)

        create_loadsource_table(cursor, db)
        initialize_loadsource(cursor, db)

        create_lang_table(cursor, db)
        initialize_lang(cursor, db)

        create_kind_table(cursor, db)
        initialize_kind(cursor, db)

        create_role_table(cursor, db)
        initialize_role(cursor, db)

        create_status_table(cursor, db)
        initialize_status(cursor, db)

        create_document_table(cursor, db)

        create_claims_table(cursor, db)
        create_parties_table(cursor, db)
        create_classification_table(cursor, db)
        create_title_table(cursor, db)
        create_abstract_table(cursor, db)
        create_description_table(cursor, db)

        create_saved_sql_queries_table(cursor, db)

        app.run(debug=False, threaded=True)

    except Exception as e:
        logging.critical(f" Πρόβλημα κάτα την εκκίνηση: {e}")
        raise SystemExit(1)

