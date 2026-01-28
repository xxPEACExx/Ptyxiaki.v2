
import logging

# --------------------------------------------------
# CREATE TABLE saved_sql_queries
# --------------------------------------------------
def create_saved_sql_queries_table(cursor, db):
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS saved_sql_queries")

        cursor.execute("""
            CREATE TABLE saved_sql_queries (
                SID INT UNSIGNED NOT NULL AUTO_INCREMENT,

                name VARCHAR(255) NOT NULL,
                sql_text LONGTEXT NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (SID)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db.commit()

        print("[OK] Ο πίνακας saved_sql_queries δημιουργήθηκε")

    except Exception as e:
        db.rollback()
        logging.error("create_saved_sql_queries_table failed", exc_info=True)
        print("[ERROR] create_saved_sql_queries_table failed:", e)
        raise
