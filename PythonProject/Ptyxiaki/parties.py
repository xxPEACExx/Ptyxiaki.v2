


import logging
import traceback
from state import lang_mapping
from role import role_mapping

# -------------------------------------------------
# Logging
# -------------------------------------------------
logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_error(message):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

# -------------------------------------------------
# CREATE TABLE parties
# -------------------------------------------------
def create_parties_table(cursor, db):
    try:
        # ⚠️ ΠΡΩΤΑ drop για να μη μένουν παλιά FK
        cursor.execute("DROP TABLE IF EXISTS parties")

        cursor.execute("""
        CREATE TABLE parties (
            PID INT NOT NULL AUTO_INCREMENT,
            DID INT UNSIGNED NOT NULL,
            last_name VARCHAR(255),
            state TINYINT UNSIGNED,
            role INT,
            city VARCHAR(255),

            PRIMARY KEY (PID),

            INDEX idx_parties_did (DID),
            INDEX idx_parties_state (state),
            INDEX idx_parties_role (role),

            CONSTRAINT fk_parties_document
                FOREIGN KEY (DID)
                REFERENCES document(DID)
                ON DELETE CASCADE
                ON UPDATE CASCADE,

            CONSTRAINT fk_parties_state
                FOREIGN KEY (state)
                REFERENCES state(CID)
                ON DELETE SET NULL
                ON UPDATE CASCADE,

            CONSTRAINT fk_parties_role
                FOREIGN KEY (role)
                REFERENCES role(RID)
                ON DELETE SET NULL
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        db.commit()
        print("✔ parties table dropped & created successfully")

    except Exception as e:
        db.rollback()
        print("❌ parties table creation failed:", e)


# -------------------------------------------------
# INSERT δεδομένων parties (XML → DB)
# -------------------------------------------------
def insert_parties(did, root, cursor, db):
    if not did or root is None:
        return

    def strip_ns(tag):
        return tag.split('}')[-1] if '}' in tag else tag

    # Εύρεση <parties>
    parties_section = None
    for elem in root.iter():
        if strip_ns(elem.tag) == "parties":
            parties_section = elem
            break

    if parties_section is None:
        return

    count = 0

    for role_tag in ["applicants", "inventors", "agents"]:
        role_section = parties_section.find(role_tag)
        if role_section is None:
            continue

        role_name = role_tag[:-1]  # applicants → applicant
        role_id = role_mapping.get(role_name)

        for person in role_section:
            try:
                addressbook = person.find("addressbook")
                if addressbook is None:
                    continue

                last_name_elem = addressbook.find("last-name")
                if last_name_elem is None or not last_name_elem.text:
                    continue
                last_name = last_name_elem.text.strip()

                # city
                city = None
                address_elem = addressbook.find("address")
                if address_elem is not None:
                    city_elem = address_elem.find("city")
                    if city_elem is not None and city_elem.text:
                        city = city_elem.text.strip()

                # state (country → ID)
                state_id = None
                if address_elem is not None:
                    country_elem = address_elem.find("country")
                    if country_elem is not None and country_elem.text:
                        state_id = lang_mapping.get(country_elem.text.strip())

                # INSERT
                try:
                    cursor.execute("""
                        INSERT INTO parties (DID, last_name, city, state, role)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (did, last_name, city, state_id, role_id))
                    count += 1

                except Exception as insert_error:
                    log_error(f"[INSERT_ERROR] DID {did}, name {last_name}: {insert_error}")

            except Exception:
                log_error(f"[PARTY_PARSE_ERROR] DID {did}:\n{traceback.format_exc()}")

    try:
        db.commit()
    except Exception as commit_err:
        db.rollback()
        log_error(f"[COMMIT_ERROR] DID {did}: {commit_err}")

    print(f"✅ Εισήχθησαν {count} εγγραφές στον πίνακα parties για DID: {did}")
