


import logging
import traceback
from lang import lang_mapping
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
        print("[DEBUG] create_parties_table: START")

        print("[DEBUG] Disabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        print("[DEBUG] Dropping table parties if exists")
        cursor.execute("DROP TABLE IF EXISTS parties")

        print("[DEBUG] Creating table parties")
        cursor.execute("""
            CREATE TABLE parties (
                PID INT UNSIGNED NOT NULL AUTO_INCREMENT,
                DID INT UNSIGNED NOT NULL,

                last_name VARCHAR(255),
                state TINYINT UNSIGNED,
                role INT UNSIGNED,
                city VARCHAR(255),

                PRIMARY KEY (PID),

                KEY idx_parties_DID (DID),
                KEY idx_parties_state (state),
                KEY idx_parties_role (role),

                CONSTRAINT fk_parties_document
                    FOREIGN KEY (DID)
                    REFERENCES document (DID)
                    ON UPDATE CASCADE
                    ON DELETE CASCADE,

                CONSTRAINT fk_parties_lang
                    FOREIGN KEY (state)
                    REFERENCES lang (CID)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL,

                CONSTRAINT fk_parties_role
                    FOREIGN KEY (role)
                    REFERENCES role (RID)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        print("[DEBUG] Enabling FOREIGN_KEY_CHECKS")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας parties δημιουργήθηκε επιτυχώς")

    except Exception as e:
        print("[ERROR] create_parties_table FAILED")
        print("[MYSQL ERROR]", e)

        db.rollback()

        import logging
        import traceback
        logging.error(
            "[PARTIES_TABLE_CREATE_ERROR]\n%s",
            traceback.format_exc()
        )

        raise



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
