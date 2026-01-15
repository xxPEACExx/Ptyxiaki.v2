from waitress import serve
from app import app, init_app

if __name__ == "__main__":
    # Αρχικοποίηση εφαρμογής (DB, tables, folders)
    init_app()

    # Εκκίνηση production WSGI server
    serve(
        app,
        host="0.0.0.0",   # άλλαξε σε 127.0.0.1 αν το θες μόνο local
        port=5000,
        threads=8         # μπορείς να το ανεβάσεις αν έχεις δυνατό PC
    )
