# Test seti

`sorular_v0.jsonl`: 25 soruluk ilk pilot set (her satır bir soru). Sorular `idefix` mağazasının
yardım sayfalarına ve Mesafeli Sözleşmeler Yönetmeliği'ne göre yazıldı.

| Alan | Açıklama |
|---|---|
| `id` | Sorunun kalıcı kimliği |
| `store` | Sorunun ait olduğu mağaza (her soru tek mağazaya aittir) |
| `question` | Müşterinin sorusu |
| `category` | `tek_belge`, `cok_kanit`, `gunluk_dil`, `mevzuat`, `cevapsiz`, `prompt_injection`, `konu_disi` |
| `difficulty` | `kolay`, `orta`, `zor` |
| `answerable` | Cevap dokümanlarda var mı? |
| `expected_answer` | Beklenen cevap (kendi cümlelerimizle, kısa) |
| `supporting_doc_ids` | Cevabın geçtiği dokümanlar |
| `supporting_section_ids` | Cevabın geçtiği bölümler, `doc_id#bolum_id` (ör. `idefix-odeme#faq-49`) |
| `verified` | Bir insan bu satırı kaynağa bakarak kontrol etti mi? |

Kurallar (`pytest` her çalıştığında otomatik kontrol edilir):
- Cevaplanamaz sorularda kanıt alanları boş kalır.
- Cevaplanabilir sorularda en az bir kanıt bölümü olur.

**Önemli:** Sorular yapay zekâ yardımıyla hazırlandı, bu yüzden hepsi `verified: false`.
Her satırı `data/raw/` altındaki metinle karşılaştırıp doğruysa `true` yap. Deneylerde
yalnızca doğrulanmış satırlar kullanılmalı.

Bölüm kimlikleri ileride parçalama (chunking) yöntemi değişse de sabit kalır; parça
kimlikleri (`chunk_id`) bu bölümlere bağlanarak hesaplanacak.
