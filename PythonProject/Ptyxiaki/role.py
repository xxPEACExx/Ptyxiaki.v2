# role_mapping = {
#     'applicant': 1,
#     'inventor': 2,
#     'agent': 3
# }
#
# def initialize_role(cursor, db):
#     for name, rid in role_mapping.items():
#         cursor.execute("SELECT COUNT(*) FROM role WHERE RID = %s", (rid,))
#         if cursor.fetchone()[0] == 0:
#             cursor.execute("INSERT INTO role (RID, name) VALUES (%s, %s)", (rid, name))
#     db.commit()
import logging

# Ρύθμιση logging αν δεν υπάρχει ήδη
logging.basicConfig(filename='init.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

role_mapping = {
    'applicant': 1,
    'inventor': 2,
    'agent': 3
}

def initialize_role(cursor, db):
    for name, rid in role_mapping.items():
        cursor.execute("SELECT COUNT(*) FROM role WHERE RID = %s", (rid,))
        if cursor.fetchone()[0] == 0:
            logging.info(f"➕ Εισαγωγή στον πίνακα role: ({rid}, '{name}')")
            cursor.execute("INSERT INTO role (RID, name) VALUES (%s, %s)", (rid, name))
        else:
            logging.info(f"✔️ Ο ρόλος '{name}' (RID={rid}) υπάρχει ήδη.")
    db.commit()
