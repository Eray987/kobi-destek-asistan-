# Kurulum ve araçlar (Türkçe rehber)

Bu dosya projeyi kendi bilgisayarında çalıştırmak ve kullanılan araçların ne işe yaradığını
anlamak için Türkçe bir rehberdir. Ana doküman İngilizce [README](../README.md)'dir.

## Kurulum (macOS)

Gerekenler: Python 3.11+, Git, [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/Eray987/kobi-destek-asistan-.git
cd kobi-destek-asistan-

cp .env.example .env     # ayar dosyasını oluştur
make install             # .venv sanal ortamı + bağımlılıklar
make db-up               # Docker ile PostgreSQL + pgvector
make db-check            # "Connected" görmelisin
make test                # tüm testler geçmeli
```

## Hangi araç ne işe yarıyor?

| Araç | Ne işe yarar? | Neden bu projede? |
|---|---|---|
| **Git + GitHub** | Kodun her değişikliğini kaydeder, geri dönmeyi ve paylaşmayı sağlar. | Hoca ve jüri ilerlemeyi commit geçmişinden görebilir. |
| **Branch + Pull Request** | Her iş ayrı bir dalda yapılır, `main`'e PR ile eklenir. | `main` her zaman çalışan sürüm kalır; değişiklikler gözden geçirilir. |
| **venv** (`.venv/`) | Projeye özel, izole Python ortamı. | Başka projelerin kütüphaneleriyle çakışmaz. |
| **pyproject.toml** | Projenin adı, bağımlılıkları ve araç ayarları tek dosyada. | Modern Python projelerinin standart dosyası. |
| **.env + .env.example** | Şifre ve API anahtarları koddan ayrı tutulur. | `.env` Git'e girmez; anahtar sızdırma riski olmaz. |
| **Docker + docker compose** | Programı (burada veritabanını) her bilgisayarda aynı şekilde çalışan bir kapta açar. | PostgreSQL ve pgvector'ü Mac'e kurmadan tek komutla çalıştırırız. |
| **PostgreSQL + pgvector** | İlişkisel veritabanı + vektör saklama ve benzerlik araması eklentisi. | Doküman, sürüm ve embedding'ler aynı yerde tutulur. |
| **pytest** | Otomatik testler. | Bir değişiklik eski bir şeyi bozduğunda hemen görürüz. Deneylerin tekrarlanabilir olması için de şart. |
| **ruff** | Kod düzenini ve sık hataları kontrol eder, otomatik biçimlendirir. | Kod tutarlı ve okunabilir kalır. |
| **GitHub Actions (CI)** | Her push ve PR'da testleri GitHub'ın sunucusunda çalıştırır. | "Benim bilgisayarımda çalışıyordu" sorununu önler. |
| **Makefile** | Uzun komutlara kısa isimler verir. | `make test` gibi komutlarla herkes projeyi aynı şekilde çalıştırır. |

Şimdilik **eklenmeyenler**: Kubernetes, LangChain/LlamaIndex (ilk sürümü düz Python ile yazmak
her deneyde neyin değiştiğini görmeyi kolaylaştırır), uygulamanın kendisini Docker'a koymak.

## Günlük çalışma akışı

```bash
git checkout main && git pull           # en güncel hali al
git checkout -b ozellik-adi             # yeni dal aç
# ... kod yaz ...
make format && make check               # düzenle ve test et
git add . && git commit -m "Short English description of the change"
git push -u origin ozellik-adi          # GitHub'da PR aç
```

Commit mesajları, PR'lar, kod ve yorumlar İngilizce yazılır. Test soruları ve mağaza verisi
Türkçedir, çünkü projenin konusu Türkçe RAG.
