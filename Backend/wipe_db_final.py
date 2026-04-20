from app.core.database import engine
from sqlalchemy import text

def wipe_db():
    try:
        with engine.connect() as con:
            con.execute(text("DROP SCHEMA public CASCADE;"))
            con.execute(text("CREATE SCHEMA public;"))
            con.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
            con.execute(text("GRANT ALL ON SCHEMA public TO public;"))
            con.commit()
            print("🔥 Base de datos lista para el Génesis definitivo")
    except Exception as e:
        print(f"❌ Error al limpiar la DB: {e}")

if __name__ == "__main__":
    wipe_db()
