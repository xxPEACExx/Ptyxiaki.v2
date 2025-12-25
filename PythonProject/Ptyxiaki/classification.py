
from scheme import scheme_mapping
from loadsource import loadsource_mapping

import logging

logging.basicConfig(
    filename='errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def create_classification_table(cursor, db):
    try:
        cursor.execute("DROP TABLE IF EXISTS classification")

        cursor.execute("""
            CREATE TABLE classification (
                CID INT NOT NULL AUTO_INCREMENT,
                DID MEDIUMINT UNSIGNED,
                title VARCHAR(255),
                title_size_words TINYINT,
                title_size_chars SMALLINT,
                type VARCHAR(10),

                PRIMARY KEY (CID),

                CONSTRAINT fk_classification_document
                    FOREIGN KEY (DID)
                    REFERENCES document(DID)
                    ON DELETE CASCADE
                    ON UPDATE CASCADE

            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.commit()
        print("[OK] Ο πίνακας classification δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("Σφάλμα στο create_classification_table: %s", e)

def insert_classification(did, root, cursor, db):
    # Βρίσκουμε και IPCR και CPC classifications
    classification_tags = (
        root.findall(".//classification-ipcr") +
        root.findall(".//classification-cpc")
    )

    print(f"Βρέθηκαν {len(classification_tags)} ταξινομήσεις για DID: {did}")

    for cls in classification_tags:
        # title
        title = cls.text.strip() if cls.text else None

        # type: ipcr ή cpc (από το tag)
        tag_name = cls.tag.split('}')[-1]  # αφαιρεί namespace αν υπάρχει
        if tag_name == "classification-ipcr":
            classification_type = "ipcr"
        elif tag_name == "classification-cpc":
            classification_type = "cpc"
        else:
            classification_type = None

        # μετρήσεις
        title_size_chars = len(title) if title else None
        title_size_words = len(title.split()) if title else None

        print(
            f"  → title: {title}, "
            f"chars: {title_size_chars}, "
            f"words: {title_size_words}, "
            f"type: {classification_type}"
        )

        try:
            cursor.execute("""
                INSERT INTO classification
                (DID, title, title_size_words, title_size_chars, type)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                did,
                title,
                title_size_words,
                title_size_chars,
                classification_type
            ))
        except Exception as e:
            db.rollback()
            print(f"[CLASSIFICATION INSERT ERROR] DID {did}: {e}")
            continue

    db.commit()
