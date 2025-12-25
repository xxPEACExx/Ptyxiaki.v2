#
# import logging
# from format import format_mapping
# from loadsource import loadsource_mapping
# from state import lang_mapping
#
# logging.basicConfig(filename='errors.log', level=logging.ERROR,
#                     format='%(asctime)s - %(levelname)s - %(message)s')
#
#
# def get_or_create_kind_id(kind_name, cursor, db):
#     try:
#         cursor.execute("SELECT KID FROM kind WHERE name = %s", (kind_name,))
#         result = cursor.fetchone()
#         if result:
#             return result[0]
#
#         cursor.execute("INSERT INTO kind (name) VALUES (%s)", (kind_name,))
#         db.commit()
#         cursor.execute("SELECT LAST_INSERT_ID()")
#         new_id = cursor.fetchone()[0]
#         return new_id
#     except Exception as e:
#         logging.error("Error in get_or_create_kind_id with kind '%s': %s", kind_name, e)
#         return None
#
#
# def insert_claim(did, root, cursor, db):
#     try:
#         priority_claims = root.findall(".//priority-claims/priority-claim")
#         print(f"Βρέθηκαν {len(priority_claims)} claims για DID: {did}")
#     except Exception as e:
#         logging.error("Error finding priority claims for DID %s: %s", did, e)
#         return
#
#     for claim in priority_claims:
#         try:
#             document_id = claim.find("document-id")
#             if document_id is None:
#                 continue
#
#             # Format
#             format_attr = document_id.attrib.get("format")
#             format_id = format_mapping.get(format_attr)
#
#             # Load source
#             load_source_attr = claim.attrib.get("load-source")
#             load_source_id = loadsource_mapping.get(load_source_attr)
#
#             # Date
#             date_elem = document_id.find("date")
#             date_raw = date_elem.text if date_elem is not None else None
#             date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}" if date_raw and len(date_raw) == 8 else None
#
#             # Country
#             country_elem = document_id.find("country")
#             country_code = country_elem.text if country_elem is not None else None
#             country_id = lang_mapping.get(country_code)
#
#             # Kind
#             kind_elem = document_id.find("kind")
#             kind_name = kind_elem.text if kind_elem is not None else None
#             kind_id = get_or_create_kind_id(kind_name, cursor, db) if kind_name else None
#
#             print(f"  → format: {format_attr} → id: {format_id}, "
#                   f"load-source: {load_source_attr} → id: {load_source_id}, "
#                   f"date: {date}, country: {country_code} → id: {country_id}, "
#                   f"kind: {kind_name} → id: {kind_id}")
#
#             # Εισαγωγή claim
#             cursor.execute("""
#                 INSERT INTO claims (did, format, load_source, date, country, kind)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """, (did, format_id, load_source_id, date, country_id, kind_id))
#
#         except Exception as e:
#             logging.error("Error inserting claim for DID %s: %s", did, e)
#
#     try:
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         logging.error("Error committing claims for DID %s: %s", did, e)

import traceback
import logging
from state import lang_mapping
from loadsource import loadsource_mapping

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --------------------------------------------------
# CREATE TABLE claims
# --------------------------------------------------
def create_claims_table(cursor, db):
    try:
        # Απενεργοποίηση FK checks (dev/init μόνο)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        cursor.execute("DROP TABLE IF EXISTS claims")

        cursor.execute("""
            CREATE TABLE claims (
                CID INT NOT NULL AUTO_INCREMENT,
                DID MEDIUMINT UNSIGNED NOT NULL,

                count_chars INT,
                count_words INT,

                lang TINYINT,
                load_source TINYINT,

                PRIMARY KEY (CID),
                KEY idx_did (DID),
                KEY idx_lang (lang),
                KEY idx_load_source (load_source),

                CONSTRAINT fk_claims_document
                    FOREIGN KEY (DID)
                    REFERENCES document(DID)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()

        print("[OK] Ο πίνακας claims δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        print("[ERROR] create_claims_table failed:", e)


# --------------------------------------------------
# INSERT claims
# --------------------------------------------------
def insert_claims(did, root, cursor, db):
    if not did or root is None:
        return

    claims_elem = root.find(".//claims")
    if claims_elem is None:
        return

    # ---- attributes από <claims>
    lang_code = claims_elem.attrib.get("lang")
    load_source_attr = claims_elem.attrib.get("load-source")

    lang_id = lang_mapping.get(lang_code)
    load_source_id = loadsource_mapping.get(load_source_attr)

    # ---- συλλογή ΟΛΟΥ του <claim-text>
    texts = []

    for claim_text in claims_elem.findall(".//claim-text"):
        text = "".join(claim_text.itertext()).strip()
        if text:
            texts.append(text)

    if not texts:
        return

    full_text = " ".join(texts)

    count_chars = len(full_text)
    count_words = len(full_text.split())

    try:
        cursor.execute("""
            INSERT INTO claims
                (DID, count_chars, count_words, lang, load_source)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            did,
            count_chars,
            count_words,
            lang_id,
            load_source_id
        ))

        db.commit()

    except Exception:
        db.rollback()
        logging.error(
            "[CLAIMS_INSERT_ERROR] DID %s\n%s",
            did,
            traceback.format_exc()
        )

#
