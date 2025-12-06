
import logging
from format import format_mapping
from loadsource import loadsource_mapping
from state import lang_mapping

logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_or_create_kind_id(kind_name, cursor, db):
    try:
        cursor.execute("SELECT KID FROM kind WHERE name = %s", (kind_name,))
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute("INSERT INTO kind (name) VALUES (%s)", (kind_name,))
        db.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        new_id = cursor.fetchone()[0]
        return new_id
    except Exception as e:
        logging.error("Error in get_or_create_kind_id with kind '%s': %s", kind_name, e)
        return None


def insert_claim(did, root, cursor, db):
    try:
        priority_claims = root.findall(".//priority-claims/priority-claim")
        print(f"Βρέθηκαν {len(priority_claims)} claims για DID: {did}")
    except Exception as e:
        logging.error("Error finding priority claims for DID %s: %s", did, e)
        return

    for claim in priority_claims:
        try:
            document_id = claim.find("document-id")
            if document_id is None:
                continue

            # Format
            format_attr = document_id.attrib.get("format")
            format_id = format_mapping.get(format_attr)

            # Load source
            load_source_attr = claim.attrib.get("load-source")
            load_source_id = loadsource_mapping.get(load_source_attr)

            # Date
            date_elem = document_id.find("date")
            date_raw = date_elem.text if date_elem is not None else None
            date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}" if date_raw and len(date_raw) == 8 else None

            # Country
            country_elem = document_id.find("country")
            country_code = country_elem.text if country_elem is not None else None
            country_id = lang_mapping.get(country_code)

            # Kind
            kind_elem = document_id.find("kind")
            kind_name = kind_elem.text if kind_elem is not None else None
            kind_id = get_or_create_kind_id(kind_name, cursor, db) if kind_name else None

            print(f"  → format: {format_attr} → id: {format_id}, "
                  f"load-source: {load_source_attr} → id: {load_source_id}, "
                  f"date: {date}, country: {country_code} → id: {country_id}, "
                  f"kind: {kind_name} → id: {kind_id}")

            # Εισαγωγή claim
            cursor.execute("""
                INSERT INTO claims (did, format, load_source, date, country, kind)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (did, format_id, load_source_id, date, country_id, kind_id))

        except Exception as e:
            logging.error("Error inserting claim for DID %s: %s", did, e)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error("Error committing claims for DID %s: %s", did, e)

