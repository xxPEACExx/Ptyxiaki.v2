
import xml.etree.ElementTree as ET
import logging

from lang import lang_mapping
from country import country_mapping
from kind import kind_mapping
from status import status_mapping

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    filename="errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --------------------------------------------------
# CREATE TABLE document (ΧΩΡΙΣ FK – STAGING)
# --------------------------------------------------
# --------------------------------------------------
# CREATE TABLE document (ΜΕ country)
# --------------------------------------------------
def create_document_table(cursor, db):
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS document")

        cursor.execute("""
            CREATE TABLE document (
               DID INT UNSIGNED NOT NULL AUTO_INCREMENT,

                ucid VARCHAR(255),
                doc_number INT,

                kind INT UNSIGNED ,
                country TINYINT UNSIGNED ,
                status INT UNSIGNED,
                lang TINYINT UNSIGNED,

                date DATE,
                family_id INT,
                size_description INT,
                size_description_words INT,
                size_description_pars INT,

                how_many_claims SMALLINT,
                date_produced DATE,

                PRIMARY KEY (DID),

                KEY idx_kind (kind),
                KEY idx_country (country),
                KEY idx_status (status),
                KEY idx_lang (lang),

                CONSTRAINT fk_document_kind
                    FOREIGN KEY (kind)
                    REFERENCES kind(KID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,
                    
                CONSTRAINT fk_document_lang
                    FOREIGN KEY (lang)
                    REFERENCES lang(CID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_document_country
                    FOREIGN KEY (country)
                    REFERENCES country(CID)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT,

                CONSTRAINT fk_document_status
                    FOREIGN KEY (status)
                    REFERENCES status(SID)
                    ON UPDATE CASCADE
                    ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()
        print("[OK] Ο πίνακας document δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        print("[ERROR] create_document_table failed:", e)
        raise

# --------------------------------------------------
# Helpers (SAFE)
# --------------------------------------------------
def get_lang_id(lang):
    return lang_mapping.get(lang)

def get_country_id(country):
    return country_mapping.get(country)

def get_kind_id(kind):
    return kind_mapping.get(kind)

def get_status_id(status):
    if not status:
        return None
    return status_mapping.get(status.lower())



def compute_claims_count(root):
    claims = root.findall(".//{*}claim")  # namespace-safe

    claim_numbers = []
    for claim in claims:
        num = claim.get("num")
        if num and num.isdigit():
            claim_numbers.append(int(num))

    return max(claim_numbers) if claim_numbers else len(claims)


# --------------------------------------------------
# PROCESS DOCUMENT (DEBUG VERSION)
# --------------------------------------------------
def process_document(xml_file, cursor, db):

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except Exception:
        logging.error("XML PARSE FAILED: %s", xml_file, exc_info=True)
        return None

    try:
        # -----------------------------
        # ATTRIBUTES
        # -----------------------------
        ucid = root.get("ucid")
        doc_number = root.get("doc-number")
        date = root.get("date")
        lang_code = root.get("lang")
        country_code = root.get("country")
        date_produced = root.get("date-produced")
        kind_code = root.get("kind")
        family_id = root.get("family-id")
        status_code = root.get("status")

        # -----------------------------
        # MAPPINGS
        # -----------------------------
        lang_id = get_lang_id(lang_code)
        country_id = get_country_id(country_code)
        kind_id = get_kind_id(kind_code)
        status_id = get_status_id(status_code)

        if not ucid:
            raise ValueError("Missing UCID")

        if kind_id is None:
            logging.warning(f"Unknown kind '{kind_code}', setting NULL")
        if country_id is None:
            logging.warning(f"Unknown country '{country_code}', setting NULL")
        if lang_id is None:
            logging.warning(f"Unknown lang '{lang_code}', setting NULL")

        # -----------------------------
        # DESCRIPTION STATS
        # -----------------------------
        size_description = 0
        size_description_words = 0
        size_description_pars = 0

        for desc in root.findall(".//{*}description"):
            if desc.attrib.get("lang") == "EN":
                text = "".join(desc.itertext()).strip()
                size_description = len(text)
                size_description_words = len(text.split())
                size_description_pars = len(desc.findall(".//{*}p"))
                break

        # -----------------------------
        # CLAIMS COUNT (ΠΡΙΝ ΤΟ INSERT)
        # -----------------------------
        how_many_claims = compute_claims_count(root)

        # -----------------------------
        # INSERT DOCUMENT (ΜΕ CLAIMS)
        # -----------------------------
        cursor.execute("""
            INSERT INTO document (
                ucid, doc_number, date,
                lang, country, date_produced,
                kind, family_id, status,
                size_description, size_description_words, size_description_pars,
                how_many_claims
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ucid,
            int(doc_number) if doc_number else None,
            date,
            lang_id,
            country_id,
            date_produced,
            kind_id,
            int(family_id) if family_id else None,
            status_id,
            size_description,
            size_description_words,
            size_description_pars,
            how_many_claims
        ))

        did = cursor.lastrowid

        logging.info(
            "DOCUMENT INSERT OK – DID=%s how_many_claims=%s",
            did, how_many_claims
        )

        return did

    except Exception:
        logging.error("PROCESS DOCUMENT FAILED: %s", xml_file, exc_info=True)
        raise

