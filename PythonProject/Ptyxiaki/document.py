
import xml.etree.ElementTree as ET
from state import lang_mapping
from kind import kind_mapping
from status import status_mapping

import logging


# Logging config (αν δεν υπάρχει αλλού)
logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')
def create_document_table(cursor, db):
    try:
        # Προσωρινά απενεργοποιούμε τα FK checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        cursor.execute("DROP TABLE IF EXISTS document")

        cursor.execute("""
            CREATE TABLE document (
                DID MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT,

                ucid VARCHAR(255),
                doc_number INT,

                kind TINYINT,
                state VARCHAR(255),
                status TINYINT,
                lang TINYINT,

                date DATE,
                family_id INT,

                size_description MEDIUMINT,
                size_description_pars MEDIUMINT,
                size_description_words SMALLINT,

                how_many_claims SMALLINT,
                date_produced DATE,

                abstract_size_chars SMALLINT,
                abstract_word_count INT,

                PRIMARY KEY (DID),
                KEY idx_kind (kind),
                KEY idx_state (state),
                KEY idx_status (status),
                KEY idx_lang (lang)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Επαναφέρουμε τα FK checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        db.commit()
        print("[OK] Ο πίνακας document δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        print("[ERROR] create_document_table failed:", e)




def get_lang_integer(lang):
    return lang_mapping.get(lang, None)

def get_kind_id(kind):
    return kind_mapping.get(kind, None)

def get_status_id(status):
    return status_mapping.get(status.lower(), None) if status else None


def ensure_mappings(cursor, db, lang_id, kind_id, status_id):
    try:
        if lang_id:
            cursor.execute("SELECT COUNT(*) FROM state WHERE CID = %s", (lang_id,))
            if cursor.fetchone()[0] == 0:
                lang_name = {v: k for k, v in lang_mapping.items()}.get(lang_id)
                cursor.execute("INSERT INTO state (CID, country_name) VALUES (%s, %s)", (lang_id, lang_name))

        if kind_id:
            cursor.execute("SELECT COUNT(*) FROM kind WHERE KID = %s", (kind_id,))
            if cursor.fetchone()[0] == 0:
                kind_name = [k for k, v in kind_mapping.items() if v == kind_id][0]
                cursor.execute("INSERT INTO kind (KID, name) VALUES (%s, %s)", (kind_id, kind_name))

        if status_id:
            cursor.execute("SELECT COUNT(*) FROM status WHERE SID = %s", (status_id,))
            if cursor.fetchone()[0] == 0:
                status_name = [k for k, v in status_mapping.items() if v == status_id][0]
                cursor.execute("INSERT INTO status (SID, name) VALUES (%s, %s)", (status_id, status_name))

        db.commit()
    except Exception as e:
        logging.error("Error in ensure_mappings: %s", e)
        db.rollback()


def update_priority_claims_count(root, did, cursor, db):
    try:
        # Βρίσκουμε όλα τα claim elements (ανεξαρτήτως θέσης)
        claims = root.findall('.//claim')

        claim_numbers = []

        for claim in claims:
            num = claim.get('num')
            if num is not None:
                try:
                    claim_numbers.append(int(num))
                except ValueError:
                    # Αν το num δεν είναι ακέραιος, το αγνοούμε
                    continue

        # Αν βρέθηκαν έγκυρα num, παίρνουμε το μέγιστο
        if claim_numbers:
            claims_count = max(claim_numbers)
        else:
            # Fallback: πλήθος claims
            claims_count = len(claims)

        cursor.execute(
            '''
            UPDATE document
            SET how_many_claims = %s
            WHERE did = %s
            ''',
            (claims_count, did)
        )

        db.commit()

    except Exception as e:
        logging.error(
            "Error updating claims count for DID %s: %s",
            did,
            e,
            exc_info=True
        )
        db.rollback()



def process_document(xml_file, cursor, db):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        logging.error("Error parsing XML file %s: %s", xml_file, e)
        return None

    try:
        ucid = root.get('ucid')
        doc_number = root.get('doc-number')
        date = root.get('date')
        lang = root.get('lang')
        date_produced = root.get('date-produced')
        kind = root.get('kind')
        family_id = root.get('family-id')
        status = root.get('status')

        lang_id = get_lang_integer(lang)
        kind_id = get_kind_id(kind)
        status_id = get_status_id(status)

        if not lang_id or not kind_id:
            raise ValueError(f"Άγνωστη γλώσσα ή είδος για το αρχείο: {xml_file}")

        state_id = lang_id

        ensure_mappings(cursor, db, lang_id, kind_id, status_id)

        abstract = root.find('.//abstract')
        abstract_text = ''.join(abstract.itertext()) if abstract is not None else ""
        abstract_word_count = len(abstract_text.split())
        abstract_size_chars = len(abstract_text)

        size_description = 0
        size_description_words = 0
        size_description_pars = 0
        for desc in root.findall('.//description'):
            if desc.attrib.get('lang') == 'EN':
                text = ''.join(desc.itertext()).strip()
                size_description = len(text)
                size_description_words = len(text.split())
                size_description_pars = len(desc.findall('.//p'))
                break

        cursor.execute('''
            INSERT INTO document (
                ucid, doc_number, date, lang, abstract_word_count, abstract_size_chars,
                date_produced, kind, family_id, status,
                size_description, size_description_words, size_description_pars,
                state
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                doc_number = VALUES(doc_number),
                date = VALUES(date),
                lang = VALUES(lang),
                abstract_word_count = VALUES(abstract_word_count),
                abstract_size_chars = VALUES(abstract_size_chars),
                date_produced = VALUES(date_produced),
                kind = VALUES(kind),
                family_id = VALUES(family_id),
                status = VALUES(status),
                size_description = VALUES(size_description),
                size_description_words = VALUES(size_description_words),
                size_description_pars = VALUES(size_description_pars),
                state = VALUES(state)
        ''', (
            ucid, int(doc_number), date, lang_id, abstract_word_count, abstract_size_chars,
            date_produced, kind_id, family_id, status_id,
            size_description, size_description_words, size_description_pars,
            state_id
        ))

        did = cursor.lastrowid
        if did == 0:
            cursor.execute("SELECT did FROM document WHERE ucid = %s", (ucid,))
            did = cursor.fetchone()[0]

        update_priority_claims_count(root, did, cursor, db)
        return did

    except Exception as e:
        db.rollback()
        logging.error("Error processing document %s: %s", xml_file, e)
        return None
