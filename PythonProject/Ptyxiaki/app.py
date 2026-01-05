
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
# from Ptyxiaki.abstract import create_abstract_table, insert_abstract
# from Ptyxiaki.country import create_country_table, initialize_country
from Ptyxiaki.role import initialize_role, create_role_table
from Ptyxiaki.scheme import initialize_scheme, create_scheme_table
from Ptyxiaki.kind import initialize_kind, create_kind_table
from Ptyxiaki.status import initialize_status, create_status_table
from title import insert_title, create_title_table
from parties import insert_parties, create_parties_table
from claims import insert_claims, create_claims_table
from classification import insert_classification, create_classification_table
from document import process_document, create_document_table
from state import initialize_state, create_state_table
from format import initialize_format, create_format_table
from loadsource import initialize_loadsource, create_loadsource_table


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
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # megisto 1GB gia na mhn epivarinoume to request

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


    global running, paused, stopped, progress_percentage

    #kathe tread thelei thn diki toy syndesi, gia auto pername timout apo tin vasi
    try:
        thread_db = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="admin",
            database="epdatabase"
        )

        thread_cursor = thread_db.cursor()

    except Exception as e:
        logging.critical(f" Αποτυχία δημιουργίας συνδεσης στο thread: {e}")
        running = False
        return

    total_files = len(files)

    for idx, file_path in enumerate(files, start=1): #ενα ενα xml thn fora

        #diadikasima top
        with processing_lock:
            if stopped:
                logging.info(" Διακοπή διαδικασίας από χρήστη.")
                break

        # to pause
        while True:
            with processing_lock:
                if stopped:
                    logging.info("Διακοπή διαδικασίας από pause loop.")
                    return
                if not paused:
                    break
            time.sleep(0.3)

        #olo einai se try exception gia na mhn stamataei, auto luni to problhma poy thn eisagwgh kai kai sfalma
        try:

            tree = ET.parse(file_path)
            root = tree.getroot()


            did = process_document(file_path, thread_cursor, thread_db)

            #to stelnoume sto bad eeror an eixei sfalma to arxeio
            if did is None:
                logging.warning(f" DID δεν δημιουργήθηκε: {file_path}")
                with open(BAD_FILES_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{file_path} | DID not created\n")
                continue

            insert_claims(did, root, thread_cursor, thread_db)
            insert_classification(did, root, thread_cursor, thread_db)
            insert_parties(did, root, thread_cursor, thread_db)
            insert_title(did, root, thread_cursor, thread_db)
            insert_abstract(did, root, thread_cursor, thread_db)



            thread_db.commit()


            progress_percentage = int((idx / total_files) * 100)
            logging.info(f"📁 OK {file_path} ({progress_percentage}%)")

        except ET.ParseError as e:
            logging.error(f" Κακό XML: {file_path} – {e}")
            with open(BAD_FILES_LOG, "a", encoding="utf-8") as f:
                f.write(f"{file_path} | XML ParseError: {e}\n")
            continue

        except Exception as e:
            logging.error(f" Σφάλμα σε {file_path}: {e}")
            try:
                thread_db.rollback()
            except:
                logging.error(" Rollback failed (connection lost).")

            with open(BAD_FILES_LOG, "a", encoding="utf-8") as f:
                f.write(f"{file_path} | Processing Error: {e}\n")
            continue


    try:
        thread_cursor.close()
        thread_db.close()
    except:
        pass

    with processing_lock:
        running = False
        paused = False
        stopped = False
        progress_percentage = 100

    logging.info("✅ Επεξεργασία ολοκληρώθηκε κανονικά.")


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

# edw xenkinae ta endpoints

@app.route("/upload_zip", methods=["POST"])
def upload_zip():

    uploaded = request.files.getlist("files")
    if not uploaded:
        return jsonify({"message": "Δεν επιλέχθηκε ZIP αρχείο."}), 400

    zip_file = uploaded[0]


    if not zip_file.filename.lower().endswith(".zip"):
        return jsonify({"message": "Το αρχείο δεν είναι ZIP."}), 400

    base_upload_dir = "uploaded_files"
    os.makedirs(base_upload_dir, exist_ok=True)

    zip_path = os.path.join(base_upload_dir, zip_file.filename)
    zip_file.save(zip_path)

    extract_dir = os.path.join(
        base_upload_dir,
        os.path.splitext(zip_file.filename)[0]
    )
    os.makedirs(extract_dir, exist_ok=True)

    try:

        global zip_progress, zip_total
        zip_progress = 0

        with ZipFile(zip_path, 'r') as z:
            members = z.namelist()
            members = [m for m in members if not m.endswith("/")]

            zip_total = len(members)
            extracted = 0

            for member in members:
                z.extract(member, extract_dir)
                extracted += 1
                zip_progress = int((extracted / zip_total) * 100)

        xml_files = []
        for root_dir, _, files in os.walk(extract_dir):
            for f in files:
                if f.lower().endswith(".xml"):
                    full = os.path.join(root_dir, f)
                    xml_files.append(full)

        if not xml_files:
            return jsonify({"message": "Το ZIP δεν περιέχει XML αρχεία."}), 400

        zip_progress = 100


        started = start_processing_thread(xml_files)
        if not started:
            return jsonify({"message": "Η επεξεργασία ήδη τρέχει."}), 400

        return jsonify({"message": f"Ξεκίνησε η επεξεργασία {len(xml_files)} XML από ZIP."})

    except Exception as e:
        logging.exception(" Σφάλμα κατά το upload_zip")
        return jsonify({"message": f"Σφάλμα ZIP: {str(e)}"}), 500



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
    global running, paused, stopped
    data = request.json or {}
    action = data.get("action")

    with processing_lock:
        if action == "pause" and running and not paused:
            paused = True
            return jsonify({"message": "Η επεξεργασία σταμάτησε προσωρινά."})
        elif action == "continue" and running and paused:
            paused = False
            return jsonify({"message": "Η επεξεργασία συνεχίζεται."})
        elif action == "stop" and running:
            stopped = True
            paused = False
            return jsonify({"message": "Η επεξεργασία τερματίστηκε."})
        else:
            return jsonify({"message": "Μη έγκυρη ενέργεια ή η επεξεργασία δεν τρέχει."}), 400


@app.route("/get_progress", methods=["GET"])
def get_progress():
    global progress_percentage, running, paused
    status = "running" if running else "stopped"
    if paused:
        status = "paused"
    return jsonify({"progress": progress_percentage, "status": status})


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

    try:
        cursor.execute("SELECT did, filename FROM document ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        results = [{"did": row[0], "filepath": row[1]} for row in rows]
        return jsonify({"results": results})
    except Exception as e:
        logging.error(f"Error in /get_documents: {e}")
        return jsonify({"results": []}), 500


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
    try:
        per_page = 10
        page = request.args.get("page", 1, type=int)
        offset = (page - 1) * per_page

        cursor.execute("""
            SELECT
                d.did,
                d.ucid,
                d.doc_number,
                d.kind,
                d.state,
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
            LIMIT %s OFFSET %s
        """, (per_page, offset))

        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM document")
        total_rows = cursor.fetchone()[0]
        total_pages = (total_rows + per_page - 1) // per_page

        return render_template(
            "database.html",
            rows=rows,
            page=page,
            total_pages=total_pages,
        )

    except Exception as e:
        logging.error(f"/database error: {e}")
        return render_template("database.html", rows=[], page=1, total_pages=1)



@app.route("/list_uploaded_files", methods=["GET"])
def list_uploaded_files():

    base = "uploaded_files"
    result = []

    for root, dirs, files in os.walk(base):
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

    counts = calculate_week_stats_from_db(cursor)
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
    global zip_progress, zip_total
    return jsonify({
        "progress": zip_progress,
        "total": zip_total
    })





# Κεντρική συνάρτηση που τρέχει ένα SELECT query πάνω στη βάση
def run_sql_query(sql_text, cursor):
    """
    Εκτελεί ένα SQL SELECT query και επιστρέφει:
    - columns: λίστα με ονόματα στηλών
    - rows: λίστα από tuples (τα αποτελέσματα)
    - error: None ή string με μήνυμα λάθους
    - elapsed: χρόνος εκτέλεσης σε δευτερόλεπτα (float)
    """

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
        active_tab = request.form.get("active_tab", "query")  # <---- ΣΗΜΑΝΤΙΚΟ

        cols, rows, err, elapsed = run_sql_query(sql_input, cursor)

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

    cols, rows, err, elapsed = run_sql_query(sql_input, cursor)

    resp = {
        "sql": sql_input,
        "columns": cols or [],
        "rows": rows or [],
        "error": err,
        "elapsed": elapsed,
        "row_count": len(rows or [])
    }

    return resp
@app.post("/api/search")
def api_search():
    conn, cur = get_db_cursor()

    try:
        payload = request.get_json(silent=True) or {}
        criteria = payload.get("criteria", payload)

        limit = int(payload.get("limit", 100))
        offset = int(payload.get("offset", 0))

        limit = max(1, min(limit, 500))
        offset = max(0, offset)

        where = []
        params = []

        def as_int(x):
            try:
                return int(x)
            except:
                return None

        # --- Year ---
        yf = as_int(criteria.get("year_from"))
        yt = as_int(criteria.get("year_to"))

        if yf is not None:
            where.append("d.date >= %s")
            params.append(f"{yf}-01-01")
        if yt is not None:
            where.append("d.date <= %s")
            params.append(f"{yt}-12-31")

        # --- State ---
        states = criteria.get("state") or []
        if states:
            where.append(f"d.state IN ({','.join(['%s'] * len(states))})")
            params.extend(states)

        # --- Kind ---
        kinds = criteria.get("kind") or []
        if kinds:
            where.append(f"d.kind IN ({','.join(['%s'] * len(kinds))})")
            params.extend(kinds)

        # --- Metrics ---
        mc = as_int(criteria.get("min_claims"))
        if mc is not None:
            where.append("d.how_many_claims >= %s")
            params.append(mc)

        maw = as_int(criteria.get("min_abstract_words"))
        if maw is not None:
            where.append("d.abstract_word_count >= %s")
            params.append(maw)

        where_sql = " WHERE " + " AND ".join(where) if where else ""

        select_cols = [
            "d.*",
            "k.name AS kind_name",
            "s.country_name AS state_name"
        ]

        sql = f"""
            SELECT {", ".join(select_cols)}
            FROM document d
            LEFT JOIN kind  k ON k.KID = d.kind
            LEFT JOIN state s ON s.CID = d.state
            {where_sql}
            ORDER BY d.date DESC
            LIMIT %s OFFSET %s
        """

        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]

        return jsonify({
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "error": None,
            "elapsed": 0.0
        })

    except Exception as e:
        logging.error(f"/api/search error: {e}")
        return jsonify({
            "columns": [],
            "rows": [],
            "row_count": 0,
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

        elif stat_type == "state":
            cursor.execute("""
                SELECT s.code AS label, COUNT(*) AS value
                FROM document d
                JOIN state s ON s.id = d.state
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
    cur.execute("SELECT CID, country_name FROM state ORDER BY country_name")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.get("/api/stats/heatmap")
def api_stats_heatmap():
    cursor.execute("""
        SELECT
            s.country_name AS country,
            k.name AS kind,
            COUNT(*) AS total
        FROM document d
        JOIN state s ON s.CID = d.state
        JOIN kind  k ON k.KID = d.kind
        GROUP BY s.country_name, k.name
        ORDER BY s.country_name, k.name
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
    s.country_name AS country,
    k.name AS kind,
    COUNT(*) AS total
FROM document d
JOIN state s ON s.CID = d.state
JOIN kind  k ON k.KID = d.kind
GROUP BY s.country_name, k.name
ORDER BY s.country_name, k.name;

        """

        cursor.execute(sql)
        rows = cursor.fetchall()

        result = []
        for state, kind, total in rows:
            result.append({
                "country": state,   # κρατάμε country για consistency στο JS
                "kind": kind,
                "total": total
            })

        return jsonify(result)

    except Exception as e:
        logging.error(f"/api/stats/kind-by-country error: {e}")
        return jsonify([]), 500



@app.get("/api/stats/claims-vs-abstract")
def api_claims_vs_abstract():
    conn, cur = get_db_cursor()

    try:
        cur.execute("""
            SELECT
                abstract_word_count,
                how_many_claims
            FROM document
            WHERE
                abstract_word_count IS NOT NULL
                AND how_many_claims IS NOT NULL
                AND abstract_word_count > 0
                AND how_many_claims > 0
            LIMIT 5000
        """)

        rows = cur.fetchall()

        data = [
            {
                "x": r[0],  # abstract words
                "y": r[1]   # claims
            }
            for r in rows
        ]

        return jsonify({
            "points": data,
            "count": len(data)
        })

    except Exception as e:
        logging.error(f"/api/stats/claims-vs-abstract error: {e}")
        return jsonify({
            "points": [],
            "count": 0,
            "error": str(e)
        }), 500

    finally:
        cur.close()
        conn.close()




if __name__ == "__main__":
    try:


        create_format_table(cursor, db)
        initialize_format(cursor, db)

        # create_country_table(cursor, db)
        # initialize_country(cursor, db)

        create_loadsource_table(cursor, db)
        initialize_loadsource(cursor, db)

        create_state_table(cursor, db)
        initialize_state(cursor, db)

        create_kind_table(cursor, db)
        initialize_kind(cursor, db)

        create_scheme_table(cursor, db)
        initialize_scheme(cursor, db)

        create_role_table(cursor, db)
        initialize_role(cursor, db)

        create_status_table(cursor, db)
        initialize_status(cursor, db)

        create_claims_table(cursor, db)

        create_parties_table(cursor, db)

        create_classification_table(cursor, db)

        create_title_table(cursor, db)

        create_abstract_table(cursor, db)

        create_document_table(cursor, db)






        app.run(debug=True)
    except Exception as e:
        logging.critical(f" Πρόβλημα κάτα την εκκίνηση: {e}")
        raise SystemExit(1)

