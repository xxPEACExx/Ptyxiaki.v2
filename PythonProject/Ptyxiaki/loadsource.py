# # loadsource.py
#
# loadsource_mapping = {
#     'docdb': 1,
#     'patent-office': 2,
#     'ipcr': 3,
# }
#
# def initialize_loadsource(cursor, db):
#     for name, lid in loadsource_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM loadsource WHERE LID = %s", (lid,))
#         if cursor.fetchone()[0] == 0:
#             print(f"[INFO] Εισαγωγή: ({lid}, '{name}') στον πίνακα loadsource")
#             cursor.execute("INSERT INTO loadsource (LID, name_loadsource) VALUES (%s, %s)", (lid, name))
#     db.commit()
import logging

# Ρύθμιση logging για καταγραφή σε αρχείο
logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

loadsource_mapping = {
    'docdb': 1,
    'patent-office': 2,
    'ipcr': 3,
}

def initialize_loadsource(cursor, db):
    try:
        for name, lid in loadsource_mapping.items():
            cursor.execute("SELECT COUNT(*) FROM loadsource WHERE LID = %s", (lid,))
            if cursor.fetchone()[0] == 0:
                print(f"[INFO] Εισαγωγή: ({lid}, '{name}') στον πίνακα loadsource")
                cursor.execute("INSERT INTO loadsource (LID, name_loadsource) VALUES (%s, %s)", (lid, name))
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_loadsource: %s", e)
