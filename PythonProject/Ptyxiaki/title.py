#
#
# def get_lang_id(lang_code, cursor, db):
#     cursor.execute("SELECT CID FROM state WHERE country_name = %s", (lang_code,))
#     result = cursor.fetchone()
#     if result:
#         return result[0]
#     else:
#         # Αν δεν υπάρχει, εισάγεται καινούρια εγγραφή στη state
#         cursor.execute("INSERT INTO state (country_name) VALUES (%s)", (lang_code,))
#         db.commit()
#         return cursor.lastrowid
#
#
# def insert_title(did, root, cursor, db):
#     if not did or root is None:
#         return
#
#     invention_titles = root.findall(".//invention-title")
#     title_text = None
#     lang_code = None
#
#     for title in invention_titles:
#         if title.attrib.get('lang') == 'EN':
#             title_text = ''.join(title.itertext()).strip()
#             lang_code = title.attrib.get('lang')
#             break
#
#     if not title_text:
#         return  # Δεν υπάρχει τίτλος στα Αγγλικά
#
#     # Υπολογισμός μεγέθους
#     size_title_chars = len(title_text)
#     size_title_words = len(title_text.split())
#
#     # Αντιστοίχιση γλώσσας με CID στον πίνακα state
#     lang_id = get_lang_id(lang_code, cursor, db)
#
#     # Εισαγωγή στον πίνακα title
#     cursor.execute("""
#         INSERT INTO title (did, title_text, lang, size_title_chars, size_title_words)
#         VALUES (%s, %s, %s, %s, %s)
#         ON DUPLICATE KEY UPDATE
#             title_text = VALUES(title_text),
#             lang = VALUES(lang),
#             size_title_chars = VALUES(size_title_chars),
#             size_title_words = VALUES(size_title_words)
#     """, (did, title_text, lang_id, size_title_chars, size_title_words))
#
#     db.commit()
import traceback

def log_error(message):
    with open("errors.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

def get_lang_id(lang_code, cursor, db):
    try:
        cursor.execute("SELECT CID FROM state WHERE country_name = %s", (lang_code,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            try:
                cursor.execute("INSERT INTO state (country_name) VALUES (%s)", (lang_code,))
                db.commit()
                return cursor.lastrowid
            except Exception as insert_err:
                log_error(f"[INSERT_ERROR] state insert lang_code: {lang_code}, error: {insert_err}")
                db.rollback()
                return None
    except Exception as select_err:
        log_error(f"[SELECT_ERROR] state select lang_code: {lang_code}, error: {select_err}")
        return None

def insert_title(did, root, cursor, db):
    if not did or root is None:
        return

    invention_titles = root.findall(".//invention-title")
    title_text = None
    lang_code = None

    for title in invention_titles:
        if title.attrib.get('lang') == 'EN':
            title_text = ''.join(title.itertext()).strip()
            lang_code = title.attrib.get('lang')
            break

    if not title_text:
        return  # Δεν υπάρχει τίτλος στα Αγγλικά

    # Υπολογισμός μεγέθους
    size_title_chars = len(title_text)
    size_title_words = len(title_text.split())

    lang_id = get_lang_id(lang_code, cursor, db)
    if lang_id is None:
        log_error(f"[ERROR] Δεν βρέθηκε ή δεν εισήχθη το lang_id για γλώσσα: {lang_code}")
        return

    try:
        cursor.execute("""
            INSERT INTO title (did, title_text, lang, size_title_chars, size_title_words)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                title_text = VALUES(title_text),
                lang = VALUES(lang),
                size_title_chars = VALUES(size_title_chars),
                size_title_words = VALUES(size_title_words)
        """, (did, title_text, lang_id, size_title_chars, size_title_words))
        db.commit()
    except Exception as e:
        db.rollback()
        log_error(f"[INSERT_ERROR] title insert did: {did}, error: {e}")

