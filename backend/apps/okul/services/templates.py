"""İndirilebilir içe aktarma şablonları (aile iskeletinden; OAB'de tasarım §8.4).

Başlıklar parser sinonimleriyle bire bir tanınır — ayrı bir "şablon kod yolu"
YOKTUR; kullanıcı şablonu doldurup aynı import ucuna yükler. Öğrenci şablonu F1b 5. adımda
öğrenci tarafıyla söküldü (tasarım §5.1 ALMA); yerine veli listesi şablonu geldi (T5: e-Okul veli
adı veren rapor sunmaz, liste okulun doldurduğu bu şablondan gelir; plan "F1b-5 uygulama
kararları").
"""

from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

#: Personel şablonunda unvan ve branş sütunu YOKTUR (tasarım §8.4). "Görev Türü" yalnız
#: "Öğretmen", "Yönetici" ya da "Diğer personel" değerini bekler (sözlük "Personelin türü");
#: ayrıştırıcı onu türe çevirir (`excel_personel.template_member_kind`), metnini saklamaz.
PERSONNEL_TEMPLATE_HEADERS: tuple[str, ...] = ("Adı", "Soyadı", "Görev Türü")
#: "Görev Türü" sütununun doğrulama listesi (Excel'de açılır liste; arayüz etiketleri).
GOREV_TURU_DEGERLERI: tuple[str, ...] = ("Öğretmen", "Yönetici", "Diğer personel")
#: Veli listesi şablonunda YALNIZ iki sütun vardır (tasarım §8.4; T5): velinin adı-soyadı ve
#: öğrencinin sınıfı. Ayrıştırıcı başlıkları birebir tanır (`excel_veli.COLUMN_SYNONYMS`).
PARENT_TEMPLATE_HEADERS: tuple[str, ...] = ("Velinin Adı Soyadı", "Öğrencinin Sınıfı")
#: "Öğrencinin Sınıfı" sütununun girdi iletisi (Excel; sözlük §4.3 "Veli Listesi"). Örnek
#: yazımlar ayrıştırıcının tanıdıklarıdır (`excel_veli.sinif_metni`); okul öncesi dahil.
PARENT_CLASS_PROMPT = (
    "9-A, 10/B, Hazırlık-A, Anasınıfı-A ya da 5 Yaş-A biçiminde. Bir satır bir öğrencidir."
)
#: Doğrulama listesinin kapsadığı son satır (örnek satırla birlikte).
_DOGRULAMA_SON_SATIR = 1000


def _workbook_bytes(
    headers: tuple[str, ...],
    example: tuple[str, ...],
    validations: tuple[DataValidation, ...] = (),
) -> bytes:
    wb = Workbook()
    ws: Worksheet = wb.active
    ws.append(list(headers))
    ws.append(list(example))
    for column_cells in ws.columns:
        letter = column_cells[0].column_letter
        ws.column_dimensions[letter].width = 18
    for dogrulama in validations:
        ws.add_data_validation(dogrulama)
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _gorev_turu_listesi(sutun: str) -> DataValidation:
    """ "Görev Türü" sütununun açılır listesi: yalnız üç değer; açıklaması seçimde görünür.

    Açıklama başlık satırının ÜSTÜNE yazılmaz: başlık bulma ilk satırları tarar, açıklama
    satırı bir başlık sözcüğüne eşlenebilirdi (`excel_ortak.basligi_bul`).
    """
    dogrulama = DataValidation(
        type="list",
        formula1='"' + ",".join(GOREV_TURU_DEGERLERI) + '"',
        allow_blank=True,
        showErrorMessage=True,
        errorTitle="Görev türü",
        error="Listeden seçin: Öğretmen, Yönetici ya da Diğer personel.",
        showInputMessage=True,
        promptTitle="Görev türü",
        prompt="Öğretmen, Yönetici ya da Diğer personel. Unvan ve branş yazılmaz.",
    )
    dogrulama.add(f"{sutun}2:{sutun}{_DOGRULAMA_SON_SATIR}")
    return dogrulama


def personnel_template_xlsx() -> bytes:
    """Örnek satırlı personel şablonu; "Görev Türü" sütununda doğrulama listesi."""
    return _workbook_bytes(
        PERSONNEL_TEMPLATE_HEADERS,
        ("ÖRNEK", "ÖĞRETMEN", "Öğretmen"),
        (_gorev_turu_listesi("C"),),
    )


def parent_template_xlsx() -> bytes:
    """Veli listesi şablonu: iki sütun, uydurma örnek satır (bir satır bir öğrenci).

    Örnek satır uydurmadır ve aktarılmadan önce silinmelidir; silinmezse "Örnek Veli" adlı bir
    satır olarak aktarılır (önizlemede sayısı görünür). Açıklama başlığın üstüne yazılmaz
    (`_gorev_turu_listesi` gerekçesi); sınıf sütununun yazımı girdi iletisinde söylenir.
    """
    sinif = DataValidation(
        type="textLength",
        operator="lessThanOrEqual",
        formula1="16",
        allow_blank=True,
        showInputMessage=True,
        promptTitle="Öğrencinin sınıfı",
        prompt=PARENT_CLASS_PROMPT,
    )
    sinif.add(f"B2:B{_DOGRULAMA_SON_SATIR}")
    return _workbook_bytes(PARENT_TEMPLATE_HEADERS, ("ÖRNEK VELİ", "9-A"), (sinif,))
