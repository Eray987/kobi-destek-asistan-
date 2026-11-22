# Sık kullanılan komutların kısayolları. Örnek: make test
.PHONY: kurulum db-baslat db-durdur db-kontrol veri test format kontrol

kurulum:    ## Sanal ortamı oluştur ve bağımlılıkları kur
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

db-baslat:  ## PostgreSQL + pgvector'ü Docker ile başlat
	docker compose up -d

db-durdur:  ## Veritabanını durdur
	docker compose down

db-kontrol: ## Veritabanı bağlantısını dene
	.venv/bin/python scripts/db_kontrol.py

veri:       ## Kaynak sayfaları indir ve Markdown'a çevir (data/sources.yaml)
	.venv/bin/python scripts/kaynaklari_indir.py

test:       ## Testleri çalıştır
	.venv/bin/pytest -v

format:     ## Kodu otomatik düzenle
	.venv/bin/ruff format .
	.venv/bin/ruff check --fix .

kontrol:    ## CI'daki kontrollerin aynısını yerelde çalıştır
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/pytest -v
