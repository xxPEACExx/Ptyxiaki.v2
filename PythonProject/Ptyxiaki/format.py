# # format.py
#
# format_mapping = {'epo': 1, 'original': 2, 'intermediate': 3}
#
# def initialize_format(cursor, db):
#     for name, fid in format_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM format WHERE FID = %s", (fid,))
#         if cursor.fetchone()[0] == 0:
#             print(f"[INFO] Εισαγωγή: ({fid}, '{name}') στον πίνακα format")
#             cursor.execute("INSERT INTO format (FID, name) VALUES (%s, %s)", (fid, name))
#     db.commit()
# format.py

import logging

# Ρύθμιση logging (αν δεν έχεις ήδη κάπου αλλού)
logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

format_mapping = {'epo': 1, 'original': 2, 'intermediate': 3}

def initialize_format(cursor, db):
    try:
        for name, fid in format_mapping.items():
            cursor.execute("SELECT COUNT(*) FROM format WHERE FID = %s", (fid,))
            if cursor.fetchone()[0] == 0:
                print(f"[INFO] Εισαγωγή: ({fid}, '{name}') στον πίνακα format")
                cursor.execute("INSERT INTO format (FID, name) VALUES (%s, %s)", (fid, name))
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στην initialize_format: %s", e)
