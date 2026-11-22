# KOBİ Destek Asistanı

KOBİ'ler için Türkçe, doküman tabanlı müşteri destek asistanı (Bitirme Projesi, 2026–2027).

Asistan müşteri sorularını yalnızca şirketin kendi dokümanlarına dayanarak cevaplar, cevabın kaynağını gösterir ve cevap dokümanlarda yoksa uydurmak yerine müşteriyi temsilciye aktarır. Projenin asıl katkısı, Türkçe bir değerlendirme seti üzerinde farklı RAG tasarım kararlarını (parçalama, hibrit arama, reranker, bilinçli reddetme) karşılaştıran deneylerdir.

## Yol haritası

- [x] 1. Repo ve mühendislik altyapısı
- [ ] 2. Kurgusal mağaza dokümanları + 25 soruluk elle doğrulanmış test seti
- [ ] 3. Baseline retrieval (yalnızca vektör araması), Recall@5 ve MRR
- [ ] 4. LLM ile kaynaklı cevap + temsilciye aktarma, FastAPI `/ask` ucu

## Klasör yapısı

```
src/kobi_asistan/     Uygulamanın Python kodu
tests/                Otomatik testler (pytest)
scripts/              Elle çalıştırılan yardımcı betikler
data/dokumanlar/      Şirket dokümanları (.md)
data/test_seti/       Soru-cevap değerlendirme seti
docker/postgres/      Veritabanı ilk açılırken çalışan SQL
.github/workflows/    GitHub Actions (CI) ayarları
```

## Kurulum (macOS)

Gerekenler: Python 3.11+, Git, [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone https://github.com/Eray987/kobi-destek-asistan-.git
cd kobi-destek-asistan-

cp .env.example .env     # ayar dosyasını oluştur
make kurulum             # .venv sanal ortamı + bağımlılıklar
make db-baslat           # Docker ile PostgreSQL + pgvector
make db-kontrol          # "Bağlantı başarılı" görmelisin
make test                # tüm testler geçmeli
```

`make` kullanmak istemezsen her hedefin karşılığı `Makefile` içinde açıkça yazıyor.

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

İhtiyaç olmadığı için şimdilik **eklenmeyenler**: Kubernetes, LangChain/LlamaIndex (ilk sürümü düz Python ile yazmak her deneyde neyin değiştiğini görmeyi kolaylaştırır), uygulamanın kendisini Docker'a koymak (API adımında eklenebilir).

## Günlük çalışma akışı

```bash
git checkout main && git pull           # en güncel hali al
git checkout -b ozellik-adi             # yeni dal aç
# ... kod yaz ...
make format && make kontrol             # düzenle ve test et
git add . && git commit -m "Ne yaptığını anlatan mesaj"
git push -u origin ozellik-adi          # GitHub'da PR aç
```
