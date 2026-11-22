"""Veritabanının çalıştığını ve pgvector'ün kurulu olduğunu kontrol eder.

Kullanım:  python scripts/db_kontrol.py
"""

from kobi_asistan.db import baglan, pgvector_surumu


def main() -> None:
    with baglan() as conn:
        surum = pgvector_surumu(conn)
        # İki vektör arasındaki kosinüs uzaklığı: 0 = aynı yön
        uzaklik = conn.execute("SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector").fetchone()[0]
    print(f"Bağlantı başarılı. pgvector sürümü: {surum}")
    print(f"Örnek kosinüs uzaklığı (aynı vektör): {uzaklik}")


if __name__ == "__main__":
    main()
