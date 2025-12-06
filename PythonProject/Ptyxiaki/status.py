#
# status_mapping = {
#     'corrected': 1,
#     'deleted': 2
# }
#
# def initialize_status(cursor, db):
#     for name, sid in status_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM status WHERE SID = %s", (sid,))
#         if cursor.fetchone()[0] == 0:
#             cursor.execute("INSERT INTO status (SID, name) VALUES (%s, %s)", (sid, name))
#     db.commit()
import traceback

status_mapping = {
    'corrected': 1,
    'deleted': 2
}

def log_error(message):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def initialize_status(cursor, db):
    for name, sid in status_mapping.items():
        try:
            cursor.execute("SELECT COUNT(*) FROM status WHERE SID = %s", (sid,))
            if cursor.fetchone()[0] == 0:
                try:
                    cursor.execute("INSERT INTO status (SID, name) VALUES (%s, %s)", (sid, name))
                except Exception as insert_err:
                    log_error(f"[INSERT_ERROR] SID: {sid}, name: {name}, error: {insert_err}")
                    continue
        except Exception as select_err:
            log_error(f"[SELECT_ERROR] SID: {sid}, name: {name}, error: {select_err}")
            continue
    try:
        db.commit()
    except Exception as commit_err:
        db.rollback()
        log_error(f"[COMMIT_ERROR] initialize_status commit failed: {commit_err}")

