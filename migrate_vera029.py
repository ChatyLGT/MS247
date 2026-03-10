        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS poking_counter INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS citas_fallidas INTEGER DEFAULT 0;")
        cur.execute("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS citas_totales INTEGER DEFAULT 0;")
        conn.commit()
        print("MIGRACION VERA-029.5: Exitosa.")
    except Exception as e:
        print(f"MIGRACION: Error: {e}")
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    migrate()
