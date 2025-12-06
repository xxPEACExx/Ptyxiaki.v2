# # κανει εισαγωγη το did στον πινακα του classification
#
# def insert_classification(did, cursor, db):
#     if did:
#         cursor.execute("INSERT IGNORE INTO classification (did) VALUES (%s)", (did,))
#         db.commit()

import xml.etree.ElementTree as ET
from scheme import scheme_mapping
from loadsource import loadsource_mapping
import re

def insert_classification(did, root, cursor, db):
    # Συνδυαστικά xpath για classification tags
    classification_tags = root.findall(".//classification-ipcr") + root.findall(".//classification-cpc")

    print(f"Βρέθηκαν {len(classification_tags)} ταξινομήσεις για DID: {did}")

    for cls in classification_tags:
        title = cls.text.strip() if cls.text else None

        load_source_attr = cls.attrib.get("load-source")
        load_source_id = loadsource_mapping.get(load_source_attr)

        scheme_attr = cls.attrib.get("scheme")
        scheme_id = scheme_mapping.get(scheme_attr)

        title_size_chars = len(title) if title else None
        title_size_words = len(title.split()) if title else None

        print(f"  → title: {title}, chars: {title_size_chars}, words: {title_size_words}, "
              f"load_source: {load_source_attr} → {load_source_id}, scheme: {scheme_attr} → {scheme_id}")

        # Εισαγωγή εγγραφής
        cursor.execute("""
            INSERT INTO classification 
            (did, title, title_size_chars, title_size_words, load_source, scheme)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (did, title, title_size_chars, title_size_words, load_source_id, scheme_id))

    db.commit()

