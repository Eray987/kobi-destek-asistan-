"""data/sources.yaml'daki sayfaları indirir ve Markdown dokümanlara çevirir.

    python scripts/kaynaklari_indir.py

- Şirket sayfaları  -> data/raw/<magaza>/<doc_id>.md   (Git'e girmez)
- Mevzuat           -> data/mevzuat/<doc_id>.md        (resmî metin, Git'e girebilir)

Sitelere nazik davranır: robots.txt'ye uyar ve istekler arasında bekler.
"""

import sys
import time
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlsplit

import requests
import yaml

from kobi_asistan.veri.ayristirma import ayristir, markdown_yaz

KOK = Path(__file__).resolve().parent.parent
USER_AGENT = "kobi-destek-asistani/0.1 (akademik bitirme projesi)"
BEKLEME_SN = 2


def robots_izin_veriyor(url: str) -> bool:
    parca = urlsplit(url)
    rp = urllib.robotparser.RobotFileParser(f"{parca.scheme}://{parca.netloc}/robots.txt")
    try:
        rp.read()
    except OSError:
        return True  # robots.txt okunamazsa varsayılan olarak izinli
    return rp.can_fetch(USER_AGENT, url)


def indir(url: str) -> str:
    yanit = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    yanit.raise_for_status()
    yanit.encoding = yanit.encoding or "utf-8"
    return yanit.text


def isle(kaynak: dict, hedef_klasor: Path) -> list[Path]:
    if not robots_izin_veriyor(kaynak["url"]):
        print(f"  ATLANDI (robots.txt izin vermiyor): {kaynak['url']}")
        return []
    html = indir(kaynak["url"])
    hedef_klasor.mkdir(parents=True, exist_ok=True)
    yazilanlar = []
    for dok in ayristir(kaynak["ayristirici"], html, kaynak["doc_id"]):
        yol = hedef_klasor / f"{dok.doc_id}.md"
        yol.write_text(markdown_yaz(dok, kaynak), encoding="utf-8")
        print(f"  {yol.relative_to(KOK)}  ({len(dok.bolumler)} bölüm)")
        yazilanlar.append(yol)
    return yazilanlar


def main() -> int:
    kaynaklar = yaml.safe_load((KOK / "data" / "sources.yaml").read_text(encoding="utf-8"))
    hatalar = 0

    gorevler = []
    for magaza in kaynaklar.get("magazalar", []):
        for k in magaza["kaynaklar"]:
            gorevler.append((k, KOK / "data" / "raw" / magaza["id"]))
    for k in kaynaklar.get("mevzuat", []):
        gorevler.append((k, KOK / "data" / "mevzuat"))

    for i, (kaynak, klasor) in enumerate(gorevler):
        print(f"[{i + 1}/{len(gorevler)}] {kaynak['doc_id']}")
        try:
            isle(kaynak, klasor)
        except Exception as hata:  # bir kaynak bozuksa diğerlerine devam et
            hatalar += 1
            print(f"  HATA: {hata}")
        time.sleep(BEKLEME_SN)

    print("Bitti." if not hatalar else f"{hatalar} kaynakta hata oluştu.")
    return 1 if hatalar else 0


if __name__ == "__main__":
    sys.exit(main())
