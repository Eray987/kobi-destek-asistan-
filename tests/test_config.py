from kobi_asistan.config import ayarlari_yukle


def test_varsayilan_ayarlar():
    ayarlar = ayarlari_yukle(env={})
    assert ayarlar.postgres_host == "localhost"
    assert ayarlar.postgres_port == 5432


def test_veritabani_url_ortam_degiskenlerinden_olusur():
    ayarlar = ayarlari_yukle(
        env={
            "POSTGRES_USER": "u",
            "POSTGRES_PASSWORD": "p",
            "POSTGRES_DB": "d",
            "POSTGRES_HOST": "h",
            "POSTGRES_PORT": "6543",
        }
    )
    assert ayarlar.veritabani_url == "postgresql://u:p@h:6543/d"
