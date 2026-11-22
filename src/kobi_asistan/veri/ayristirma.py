"""HTML sayfalarını yapılandırılmış dokümanlara çevirir.

Her ayrıştırıcı ham HTML alır, `Dokuman` listesi döndürür. Ağ erişimi yoktur;
bu yüzden küçük örnek HTML dosyalarıyla (tests/fixtures) test edilebilirler.

Her doküman `Bolum`lerden oluşur. Bölüm kimlikleri (ör. `faq-64`, `madde-12`)
test setindeki kanıtların bağlandığı kalıcı kimliklerdir.
"""

import json
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup


@dataclass
class Bolum:
    id: str
    baslik: str
    metin: str


@dataclass
class Dokuman:
    doc_id: str
    baslik: str
    bolumler: list[Bolum] = field(default_factory=list)


def _temiz(metin: str) -> str:
    """Fazla boşlukları ve satır sonlarını sadeleştirir."""
    metin = metin.replace(" ", " ")
    metin = re.sub(r"[ \t]+", " ", metin)
    metin = re.sub(r"\s*\n\s*", "\n", metin)
    return metin.strip()


def _html_metin(html: str) -> str:
    return _temiz(BeautifulSoup(html or "", "html.parser").get_text(" "))


def _slug(yol: str) -> str:
    """'/yardim/iade-ve-degisim-6' -> 'iade-ve-degisim'"""
    son = yol.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"-\d+$", "", son)


def idefix_sss(html: str, doc_id_onek: str = "idefix") -> list[Dokuman]:
    """idefix yardım sayfası: SSS'ler sayfadaki __NEXT_DATA__ JSON'unda gelir.

    Görünen HTML'de yalnızca sorular var, cevaplar JavaScript ile açılıyor; bu yüzden
    metni HTML yerine sayfanın gömülü verisinden okuyoruz.
    """
    soup = BeautifulSoup(html, "html.parser")
    etiket = soup.find("script", id="__NEXT_DATA__")
    if etiket is None:
        raise ValueError("__NEXT_DATA__ bulunamadı: sayfa yapısı değişmiş olabilir")
    veri = json.loads(etiket.string)
    kategoriler = veri["props"]["pageProps"]["faqs"]

    dokumanlar = []
    for kat in kategoriler:
        dok = Dokuman(doc_id=f"{doc_id_onek}-{_slug(kat['slug'])}", baslik=kat["name"])
        for sss in kat["faqs"]:
            dok.bolumler.append(
                Bolum(
                    id=f"faq-{sss['id']}",
                    baslik=_temiz(sss["title"]),
                    metin=_html_metin(sss.get("message", "")),
                )
            )
        dokumanlar.append(dok)
    return dokumanlar


def html_main(html: str, doc_id: str) -> list[Dokuman]:
    """Genel sayfa: <main> içindeki metni tek bölüm olarak alır."""
    soup = BeautifulSoup(html, "html.parser")
    for gereksiz in soup(["script", "style", "noscript", "nav", "header", "footer"]):
        gereksiz.decompose()
    govde = soup.find("main") or soup.body or soup
    baslik = _temiz(soup.title.get_text()) if soup.title else doc_id
    metin = _temiz(govde.get_text("\n"))
    return [Dokuman(doc_id=doc_id, baslik=baslik, bolumler=[Bolum("tum", baslik, metin)])]


_MADDE = re.compile(r"^(?:GEÇİCİ\s+)?MADDE\s+(\d+)\s*[–-]", re.IGNORECASE)


def mevzuat(html: str, doc_id: str) -> list[Dokuman]:
    """mevzuat.gov.tr metni: her MADDE ayrı bölüm olur (madde-1, madde-2, ...).

    Maddenin hemen üstündeki satır (ör. "Cayma hakkı") madde başlığı olarak alınır.
    """
    satirlar = [s for s in _temiz(BeautifulSoup(html, "html.parser").get_text("\n")).split("\n")]
    baslik = satirlar[0] if satirlar else doc_id
    dok = Dokuman(doc_id=doc_id, baslik=baslik)

    mevcut: Bolum | None = None
    onceki = ""
    for satir in satirlar:
        eslesme = _MADDE.match(satir)
        if eslesme:
            no = eslesme.group(1)
            on_ek = "gecici-" if satir.upper().startswith("GEÇİCİ") else ""
            mevcut = Bolum(id=f"{on_ek}madde-{no}", baslik=onceki, metin=satir)
            dok.bolumler.append(mevcut)
        elif mevcut is not None:
            mevcut.metin += "\n" + satir
        onceki = satir

    # Bir sonraki maddenin başlığı, önceki maddenin sonuna eklenmiş olur; onu temizle.
    for i in range(len(dok.bolumler) - 1):
        sonraki_baslik = dok.bolumler[i + 1].baslik
        if sonraki_baslik and dok.bolumler[i].metin.endswith("\n" + sonraki_baslik):
            dok.bolumler[i].metin = dok.bolumler[i].metin[: -len(sonraki_baslik) - 1]
    return [dok]


AYRISTIRICILAR = {"idefix_sss", "html_main", "mevzuat"}


def ayristir(ayristirici: str, html: str, doc_id: str) -> list[Dokuman]:
    if ayristirici == "idefix_sss":
        return idefix_sss(html, doc_id_onek=doc_id.split("-")[0])
    if ayristirici == "html_main":
        return html_main(html, doc_id)
    if ayristirici == "mevzuat":
        return mevzuat(html, doc_id)
    raise ValueError(f"Bilinmeyen ayrıştırıcı: {ayristirici}")


def markdown_yaz(dok: Dokuman, kaynak: dict) -> str:
    """Dokümanı, başında kaynak bilgisi olan bir Markdown metnine çevirir."""
    ust = [
        "---",
        f"doc_id: {dok.doc_id}",
        f"baslik: {json.dumps(dok.baslik, ensure_ascii=False)}",
        f"url: {kaynak['url']}",
        f"erisim: {kaynak['erisim']}",
        f"lisans: {kaynak['lisans']}",
        "---",
        "",
        f"# {dok.baslik}",
        "",
    ]
    govde = [f"## [{b.id}] {b.baslik}\n\n{b.metin}\n" for b in dok.bolumler]
    return "\n".join(ust) + "\n".join(govde)
