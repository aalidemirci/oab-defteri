"""`okul` API uçları — İNCE view'lar (View → Service → Model; ORM selectors'ta).

Kişisel hesaplar ve oturum F1b-1'de geldi (`apps.okul.oturum`, uçları
`views_oturum`). Rol izni ara katmandadır: açık oturumda her uç ADIYLA rol tablosundadır
(`rol_izinleri.KURALLAR`, `RolMiddleware`; 403 `rol_yetkisiz`); DRF izni AllowAny kalır.
Tek izin sınıfı kişi yazan uçlardadır ve kurulum durumunun kapısıdır: ilk program
yöneticisi hesabı kurulmadan yazma yöntemleri 409 `parola_gerekli` döner
(`permissions.RequiresAdminPassword`, tasarım §5.3). Servislerin yetki kapısının reddi
(`RolYetkisiz`) `ValueError` değildir: `_service_errors` onu 400'e çevirmez, 403 olarak
geçer. Hata gövdesi `shared.exceptions.od_exception_handler` ile
`{code, message, fields}` sözleşmesine çevrilir; parser hataları
ValidationError olarak yükseltilir.

Aile iskeletinden alındı. Kapalı gün uçları ayrı dosyadadır (`views_calendar`);
sınıf-sorumlusu ve yıl-devri uçları yoktur. Zil/vardiya/şube kümesi/zümre/
fotoğraf/cinsiyet uçları aile iskeletine de alınmamıştı.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO
from typing import Any

from django.http import FileResponse
from django.views.decorators.debug import sensitive_variables
from rest_framework import generics, serializers, status
from rest_framework.exceptions import APIException
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.okul import selectors
from apps.okul.excel_ogrenci import ParserError
from apps.okul.models import (
    ClassSection,
    Personnel,
    SchoolYear,
    Student,
)
from apps.okul.oturum import OTURUM, yazar
from apps.okul.permissions import RequiresAdminPassword
from apps.okul.serializers import (
    ClassSectionSerializer,
    ImportRequestSerializer,
    PersonnelMergeSerializer,
    PersonnelSerializer,
    RecoveryKeyPdfRequestSerializer,
    RecoveryKeyRequestSerializer,
    RoadmapUpdateSerializer,
    SchoolConfigSerializer,
    SchoolTermConfigurationSerializer,
    SchoolTermSerializer,
    SchoolYearSerializer,
    StudentSerializer,
)
from apps.okul.services import app_password as app_password_service
from apps.okul.services import encrypted_backup as encrypted_backup_service
from apps.okul.services import hesap_kurallari, recovery_key_document
from apps.okul.services import imports as import_service
from apps.okul.services import live_restore as live_restore_service
from apps.okul.services import persons as persons_service
from apps.okul.services import school_year as school_year_service
from apps.okul.services import sections as section_service
from apps.okul.services import setup as setup_service
from apps.okul.services import templates as template_service
from apps.okul.services import terms as term_service
from apps.okul.services import updates as update_service
from apps.okul.views_oturum import guvenlik_hatalari

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Boolean query parametresi için kabul edilen "açık" değerler.
TRUE_VALUES = frozenset({"true", "1"})


@contextmanager
def _service_errors() -> Iterator[None]:
    """Servis `ValueError`'larını sözleşmeli 400'e çevirir (Türkçe mesaj korunur).

    Yetki kapısının reddi (`RolYetkisiz`) `ValueError` değildir: buradan geçer, 403 olur.
    """
    try:
        yield
    except ValueError as exc:
        raise serializers.ValidationError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Kurulum sihirbazı
# ---------------------------------------------------------------------------
class SetupIncompleteResponse(APIException):
    """`setup/complete/` eksik adım reddi — 400 `kurulum_eksik` (ileti hangi adımı söyler)."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "kurulum_eksik"
    default_detail = "Kurulum tamamlanamadı."


class SetupStatusView(APIView):
    """Kurulum durumu — masaüstü sağlık denetimi + arayüz kurulum kapısı + yol haritası.

    Hafif ve kişisel verisizdir (`services.setup.setup_status`).
    """

    def get(self, request: Request) -> Response:
        return Response(setup_service.setup_status())


class GradeLevelsView(APIView):
    """`GET /api/v1/grade-levels/` — UI seçicileri için geçerli öğrenim seviyeleri.

    Liste okul içi sabitten gelir (`SchoolConfig.grade_levels`): 1-12, hazırlık
    bayrağı açıksa başta 0 (Hazırlık). Kademe (`SchoolConfig.kademe`)
    seviyeleri KISITLAMAZ.
    """

    def get(self, request: Request) -> Response:
        config = setup_service.get_school_config()
        return Response(
            {
                "levels": selectors.grade_levels(),
                "prep_enabled": config.has_prep_class,
            }
        )


class SchoolConfigView(APIView):
    def get(self, request: Request) -> Response:
        return Response(SchoolConfigSerializer(setup_service.get_school_config()).data)

    def put(self, request: Request) -> Response:
        serializer = SchoolConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = setup_service.update_school_config(fields=dict(serializer.validated_data))
        return Response(SchoolConfigSerializer(config).data)


class SetupCompleteView(APIView):
    """`POST setup/complete/` — yalnız üç adım da tamamsa (parola, okul, ders yılı).

    1. adım kurtarma anahtarı doğrulanmadan tamam sayılmaz (tasarım §4.4.5).
    Kurulum sürerken boşta kilit işlemez (tasarım §13 D15); tamamlanınca boşta
    sayacı sıfırdan başlar (`OTURUM.sureyi_yeniden_baslat`).
    """

    def post(self, request: Request) -> Response:
        try:
            config = setup_service.mark_setup_completed()
        except setup_service.SetupIncomplete as exc:
            raise SetupIncompleteResponse(detail=str(exc)) from exc
        OTURUM.sureyi_yeniden_baslat()
        return Response({"setup_completed": config.setup_completed})


class SetupRoadmapView(APIView):
    """`POST setup/roadmap/` — Başlangıç Yol Haritası'nın kullanıcı işaretleri.

    Gövde `{item, done}` (elle işaretlenen madde) ya da `{hidden}` (kartı gizle;
    yalnız bütün maddeler tamamken). Yanıt güncel `{marks, hidden}`. Kişisel
    veri yazmaz.
    """

    def post(self, request: Request) -> Response:
        req = RoadmapUpdateSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        with _service_errors():
            if "hidden" in req.validated_data:
                state = setup_service.set_roadmap_hidden(hidden=req.validated_data["hidden"])
            else:
                state = setup_service.set_roadmap_mark(
                    req.validated_data["item"], done=req.validated_data["done"]
                )
        return Response(state)


# ---------------------------------------------------------------------------
# Ders yılları
# ---------------------------------------------------------------------------
class SchoolYearListCreateView(generics.ListCreateAPIView[SchoolYear]):
    serializer_class = SchoolYearSerializer

    def get_queryset(self) -> Any:
        return selectors.school_years()

    def perform_create(self, serializer: serializers.BaseSerializer[SchoolYear]) -> None:
        serializer.instance = school_year_service.create_school_year(
            **dict(serializer.validated_data)
        )


class SchoolTermView(APIView):
    def get(self, request: Request, pk: int) -> Response:
        year = get_object_or_404(selectors.school_years(), pk=pk)
        return Response(SchoolTermSerializer(year.terms.all(), many=True).data)

    def put(self, request: Request, pk: int) -> Response:
        year = get_object_or_404(selectors.school_years(), pk=pk)
        serializer = SchoolTermConfigurationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with _service_errors():
            terms = term_service.configure_terms(
                year,
                first_end=serializer.validated_data["first_term_end"],
                second_start=serializer.validated_data["second_term_start"],
            )
        return Response(SchoolTermSerializer(terms, many=True).data)


class SchoolYearActivateView(APIView):
    def post(self, request: Request, pk: int) -> Response:
        year = get_object_or_404(selectors.school_years(), pk=pk)
        school_year_service.activate_school_year(year)
        return Response(SchoolYearSerializer(year).data)


# ---------------------------------------------------------------------------
# Öğrenciler / Personel / Şubeler
# ---------------------------------------------------------------------------
class StudentListCreateView(generics.ListCreateAPIView[Student]):
    serializer_class = StudentSerializer
    permission_classes = [RequiresAdminPassword]

    def get_queryset(self) -> Any:
        params = self.request.query_params
        raw_level = params.get("class_level", "").strip()
        class_level: int | None = None
        if raw_level:
            # isdigit() Unicode basamaklarda ('²') True dönüp int()'te patlar;
            # sayısal olmayan değer de sessizce yutulmamalı — sözleşmeli 400.
            try:
                class_level = int(raw_level)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"class_level": "Sınıf filtresi sayısal olmalıdır."}
                ) from exc
        return selectors.student_list(
            class_level=class_level,
            class_section=params.get("class_section", ""),
            search=params.get("search", ""),
            # Süzgeç OPT-IN: sicil ekranı ayrılmış öğrenciyi de görmeli; yalnız
            # seçiciler (autocomplete) `only_active=true` gönderir.
            only_active=params.get("only_active", "").strip().lower() in TRUE_VALUES,
        )

    def perform_create(self, serializer: serializers.BaseSerializer[Student]) -> None:
        serializer.instance = persons_service.create_student(**dict(serializer.validated_data))


class StudentDetailView(generics.RetrieveUpdateDestroyAPIView[Student]):
    serializer_class = StudentSerializer
    permission_classes = [RequiresAdminPassword]

    def get_queryset(self) -> Any:
        return selectors.students_all()

    def perform_update(self, serializer: serializers.BaseSerializer[Student]) -> None:
        assert serializer.instance is not None
        serializer.instance = persons_service.update_student(
            serializer.instance, **dict(serializer.validated_data)
        )

    def perform_destroy(self, instance: Student) -> None:
        persons_service.delete_student(instance)


class PersonnelListCreateView(generics.ListCreateAPIView[Personnel]):
    serializer_class = PersonnelSerializer
    permission_classes = [RequiresAdminPassword]

    def get_queryset(self) -> Any:
        params = self.request.query_params
        return selectors.personnel_list(
            search=params.get("search", ""),
            only_active=params.get("only_active", "").strip().lower() in TRUE_VALUES,
        )

    def perform_create(self, serializer: serializers.BaseSerializer[Personnel]) -> None:
        serializer.instance = persons_service.create_personnel(**dict(serializer.validated_data))


class PersonnelDetailView(generics.RetrieveUpdateDestroyAPIView[Personnel]):
    serializer_class = PersonnelSerializer
    permission_classes = [RequiresAdminPassword]

    def get_queryset(self) -> Any:
        return selectors.personnel_all()

    def perform_update(self, serializer: serializers.BaseSerializer[Personnel]) -> None:
        assert serializer.instance is not None
        serializer.instance = persons_service.update_personnel(
            serializer.instance, **dict(serializer.validated_data)
        )

    def perform_destroy(self, instance: Personnel) -> None:
        persons_service.delete_personnel(instance)


# ---------------------------------------------------------------------------
# Ayrılış ve birleştirme (tasarım §5.1 `Personnel`, §13 D30)
# ---------------------------------------------------------------------------
class StudentLeaveView(APIView):
    """`POST students/<pk>/leave/` — "Ayrıldı olarak işaretle" (ayrılış yolu).

    Kayıt SİLİNMEZ: LEFT + `left_at`, havuzdaysa havuzdan çıkar.
    Yanıt ayrılmış öğrenci kaydıdır. Toplu karar `leave-pool/resolve/`'dadır.
    """

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        student = get_object_or_404(selectors.students_all(), pk=pk)
        return Response(StudentSerializer(persons_service.leave_student(student)).data)


class PersonnelLeaveView(APIView):
    """`POST personnel/<pk>/leave/` — "Ayrıldı olarak işaretle" (ayrılış yolu; kayıt kalır)."""

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        person = get_object_or_404(selectors.personnel_all(), pk=pk)
        return Response(PersonnelSerializer(persons_service.leave_personnel(person)).data)


class PersonnelMergeView(APIView):
    """`POST personnel/<pk>/merge/` gövde `{into_id}` — "olası aynı kişi" birleştirmesi.

    `<pk>` (kaynak: listede artık bulunmayan, ayrılış havuzundaki eski kayıt)
    `into_id` (hedef: yeni adla gelen kayıt) kaydına birleşir; bağlar birleştirme
    kancalarıyla taşınır, kaynak katı silinir. Aktarım sonucundan ya da ayrılış
    havuzundan çağrılır. İki kayıt da canlı olmalıdır (silinmiş kayıt 404).
    """

    permission_classes = [RequiresAdminPassword]

    def post(self, request: Request, pk: int) -> Response:
        req = PersonnelMergeSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        source = get_object_or_404(selectors.personnel_all(), pk=pk)
        target = get_object_or_404(selectors.personnel_all(), pk=req.validated_data["into_id"])
        merged = persons_service.merge_personnel(source, target)
        return Response(PersonnelSerializer(merged).data)


class ClassSectionListCreateView(generics.ListCreateAPIView[ClassSection]):
    serializer_class = ClassSectionSerializer

    def get_queryset(self) -> Any:
        raw_year = self.request.query_params.get("school_year", "").strip()
        school_year_id: int | None = None
        if raw_year:
            try:
                school_year_id = int(raw_year)
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"school_year": "Ders yılı kimliği sayısal olmalıdır."}
                ) from exc
        return selectors.class_sections_sorted(school_year_id=school_year_id)

    def perform_create(self, serializer: serializers.BaseSerializer[ClassSection]) -> None:
        serializer.instance = section_service.create_class_section(
            **dict(serializer.validated_data)
        )


class ClassSectionDetailView(generics.DestroyAPIView[ClassSection]):
    serializer_class = ClassSectionSerializer

    def get_queryset(self) -> Any:
        return ClassSection.objects.select_related("school_year")

    def perform_destroy(self, instance: ClassSection) -> None:
        section_service.delete_class_section(instance)


# ---------------------------------------------------------------------------
# İçe aktarma (dosya VEYA pano metni — aynı boru hattı)
# ---------------------------------------------------------------------------
class _BaseImportView(APIView):
    """Ortak istek çözümü; alt sınıf servis fonksiyonlarını belirler.

    Önizleme de kişi verisi işlediği için (ve arayüzde uygulamanın ilk adımı
    olduğu için) parola kurulmadan 409 döner.
    """

    permission_classes = [RequiresAdminPassword]

    file_handler: str = ""  # import_service fonksiyon adı (dosya yolu)
    text_handler: str = ""  # import_service fonksiyon adı (metin yolu)

    def options_for(self, validated: dict[str, Any]) -> dict[str, Any]:
        """Mutabakat seçenekleri (öğrenci: `full_list`; personelde seçenek yok — karar havuzda)."""
        return {}

    def post(self, request: Request) -> Response:
        serializer = ImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = dict(serializer.validated_data)
        uploaded = validated.get("file")
        secenekler = self.options_for(validated)
        try:
            if uploaded is not None:
                handler = getattr(import_service, self.file_handler)
                report = handler(
                    file_bytes=uploaded.read(), file_name=uploaded.name or "", **secenekler
                )
            else:
                handler = getattr(import_service, self.text_handler)
                report = handler(text=validated["text"], **secenekler)
        except ParserError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return Response(report.to_dict())


class _StudentImportView(_BaseImportView):
    def options_for(self, validated: dict[str, Any]) -> dict[str, Any]:
        return {"full_list": bool(validated.get("full_list", False))}


class StudentImportPreviewView(_StudentImportView):
    file_handler = "preview_students_file"
    text_handler = "preview_students_text"


class StudentImportCommitView(_StudentImportView):
    file_handler = "commit_students_file"
    text_handler = "commit_students_text"


class PersonnelImportPreviewView(_BaseImportView):
    file_handler = "preview_personnel_file"
    text_handler = "preview_personnel_text"


class PersonnelImportCommitView(_BaseImportView):
    file_handler = "commit_personnel_file"
    text_handler = "commit_personnel_text"


# ---------------------------------------------------------------------------
# Şablon indirme
# ---------------------------------------------------------------------------
class StudentTemplateView(APIView):
    def get(self, request: Request) -> FileResponse:
        return FileResponse(
            BytesIO(template_service.student_template_xlsx()),
            as_attachment=True,
            filename="sablon-ogrenci.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )


class PersonnelTemplateView(APIView):
    def get(self, request: Request) -> FileResponse:
        return FileResponse(
            BytesIO(template_service.personnel_template_xlsx()),
            as_attachment=True,
            filename="sablon-personel.xlsx",
            content_type=XLSX_CONTENT_TYPE,
        )


# ---------------------------------------------------------------------------
# İlk hesap ve kurtarma anahtarı (tasarım §4.3, §4.4.4, §9.7; F1b-1)
# ---------------------------------------------------------------------------
# Oturum uçları (durum özeti, hesap listesi, kilit açma, Kilitle, kurtarma
# anahtarıyla açılış, kendi parolasını değiştirme) `views_oturum.py`'dedir. Burada
# kalanlar kilitliyken KAPALIDIR (`lock_middleware.KILITLI_IZINLI`'de değildir):
# ilk hesap yalnız "kurulum" durumunda (kapı o durumda kesmez), kurtarma anahtarı
# uçları açık oturumda çalışır. Güvenlik dosyası kayıpken yalnız durum ucu ve
# sıfırlama açıktır. Parolalar YALNIZ istek gövdesinde taşınır; hiçbir yanıtta,
# günlükte veya hata mesajında yankılanmaz. Hesap silme ve hesapsız kipe dönme ucu
# YOKTUR (tasarım §5.3).
class SecurityEnableSerializer(serializers.Serializer[dict[str, Any]]):
    """İlk program yöneticisi hesabı: tanıtıcı (varsayılan `yonetici`), ad-soyad, parola."""

    tanitici = serializers.CharField(required=False, default="yonetici")
    ad_soyad = serializers.CharField(trim_whitespace=False)
    parola = serializers.CharField(trim_whitespace=False)


class AppPasswordRequestSerializer(serializers.Serializer[dict[str, Any]]):
    password = serializers.CharField(trim_whitespace=False)


class SecurityStatusView(APIView):
    """`GET /api/v1/security/status/` — hesap kurulu mu, kilitli mi, dosya kayıp mı."""

    def get(self, request: Request) -> Response:
        return Response(app_password_service.status())


class SecurityEnableView(APIView):
    """`POST /api/v1/security/enable/` `{tanitici?, ad_soyad, parola}` — ilk program yöneticisi hesabı.

    Yalnız ilk kurulumda. Oturum bu hesapla açılır (`app_password.enable`; kurulumda
    boşta kilit yoktur, tasarım §13 D15). Yanıttaki `recovery_key` TEK SEFERLİKTİR:
    sunucu onu bir daha üretemez (yalnız sarmalı saklanır); yanıt önbelleğe alınmaz.
    Sihirbaz anahtarı saklatıp doğrulatmadan (`security/recovery-key/confirm/`)
    ilerlemez. `login_name_warning` tanıtıcı ad-soyadı içeriyorsa uyarı metnidir
    (engel değil).
    """

    @sensitive_variables("req", "veri", "kurtarma")
    def post(self, request: Request) -> Response:
        req = SecurityEnableSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        veri = req.validated_data
        with guvenlik_hatalari():
            kurtarma = app_password_service.enable(
                tanitici=veri["tanitici"],
                display_name=veri["ad_soyad"],
                password=veri["parola"],
            )
        uyari = hesap_kurallari.login_name_warning(veri["tanitici"], veri["ad_soyad"])
        yanit = Response(
            {
                "recovery_key": kurtarma,
                "login_name_warning": uyari,
                **app_password_service.status(),
            },
            status=201,
        )
        yanit["Cache-Control"] = "no-store"
        return yanit


class SecurityRecoveryKeyPdfView(APIView):
    """`POST /api/v1/security/recovery-key/pdf/` `{recovery_key}` — kurtarma anahtarı belgesi.

    Anahtar `guvenlik.json`'daki kurtarma sarmalını açmıyorsa (ya da bellekteki
    anahtara ait değilse) 400 + kademeli gecikme; açıyorsa PDF. Kişi yazmaz.
    Kilitliyken kilit kapısı keser (`lock_middleware.KILITLI_IZINLI`'de değildir).
    Yanıt önbelleğe alınmaz: içinde sır vardır.
    """

    @sensitive_variables("req", "icerik")
    def post(self, request: Request) -> FileResponse:
        req = RecoveryKeyPdfRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        with _service_errors():
            icerik = recovery_key_document.render_recovery_key_pdf(
                req.validated_data["recovery_key"]
            )
        yanit = FileResponse(
            BytesIO(icerik),
            as_attachment=True,
            filename=recovery_key_document.recovery_key_pdf_filename(),
            content_type="application/pdf",
        )
        yanit["Cache-Control"] = "no-store"
        return yanit


class SecurityRecoveryKeyConfirmView(APIView):
    """`POST /api/v1/security/recovery-key/confirm/` `{recovery_key}` — saklandı damgası.

    Sihirbaz (ya da Ayarlar → Güvenlik) iki grubu istemcide denetledikten sonra
    TAM anahtarı gönderir; anahtar kurtarma sarmalını açıyor ve bellekteki
    anahtara aitse `guvenlik.json`'a doğrulama damgası yazılır (tasarım §4.4.4).
    Yanlışsa 400 + kademeli gecikme. Kişi yazmaz. Kilitliyken kilit kapısı keser
    (`lock_middleware.KILITLI_IZINLI`'de değildir). Yanıt güncel güvenlik durumudur
    (`recovery_key_confirmed: true`).
    """

    @sensitive_variables("req")
    def post(self, request: Request) -> Response:
        req = RecoveryKeyRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        with _service_errors():
            app_password_service.confirm_recovery_key(req.validated_data["recovery_key"])
        return Response(app_password_service.status())


class SecurityRecoveryKeyRenewView(APIView):
    """`POST /api/v1/security/recovery-key/renew/` `{password}` — kurtarma anahtarını yeniler.

    Yalnız açık oturumda (kilitliyken 423) ve yalnız program yöneticisi hesabıyla
    (rol kapısı ve servisin yetki kapısı; 403 `rol_yetkisiz`). Parola oturumdaki hesabınkine karşı
    doğrulanır (yanlışsa "Parola hatalı." + kademeli gecikme). Yanıttaki `recovery_key` TEK SEFERLİKTİR: sunucu onu saklamaz, bir
    daha üretemez; yanıt önbelleğe alınmaz. Yeni anahtar doğrulanana dek
    `recovery_key_confirmed` yanlıştır; `recovery_key_no` bir artar. Kişi yazmaz.

    Parolası sorulan hesap yazar bağlamının hesabıdır (`live_restore` ile aynı): rol kararı ve
    parolanın hesabı istek başındaki aynı görüntüden okunur (plan F1b-2 "Yetki kapısı").
    """

    @sensitive_variables("req", "anahtar")
    def post(self, request: Request) -> Response:
        req = AppPasswordRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        kim = yazar()
        with guvenlik_hatalari():
            anahtar = app_password_service.renew_recovery_key(
                hesap_id=(kim.hesap_id if kim is not None else None) or "",
                password=req.validated_data["password"],
            )
        yanit = Response({"recovery_key": anahtar, **app_password_service.status()})
        yanit["Cache-Control"] = "no-store"
        return yanit


class StateResetNotAllowedResponse(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "sifirlama_uygun_degil"
    default_detail = app_password_service.RESET_NOT_ALLOWED_MESSAGE


class SecurityStateResetView(APIView):
    """`POST /api/v1/security/state/reset/` — "Güvenlik dosyasını sıfırla ve kuruluma dön".

    Yalnız güvenlik dosyası kullanılamıyor + parmak izi boş + şifreli tablolar
    boşken (`app_password.state_reset_available`); aksi hâlde 409
    `sifirlama_uygun_degil`. Güvenlik dosyası kayıp kilidinde açık kalan
    uçlardandır (`lock_middleware.KAYIP_IZINLI`).
    """

    def post(self, request: Request) -> Response:
        try:
            arsiv = app_password_service.reset_unusable_state()
        except app_password_service.StateResetNotAllowed as exc:
            raise StateResetNotAllowedResponse(detail=str(exc)) from exc
        return Response({"archived_as": arsiv, **app_password_service.status()})


# ---------------------------------------------------------------------------
# Kullanıcı isteğiyle oluşturulan şifreli veritabanı yedeği
# ---------------------------------------------------------------------------
class EncryptedBackupDownloadView(APIView):
    def post(self, request: Request) -> FileResponse:
        with _service_errors():
            content, filename = encrypted_backup_service.create_encrypted_backup()
        return FileResponse(
            BytesIO(content),
            as_attachment=True,
            filename=filename,
            content_type="application/octet-stream",
        )


# ---------------------------------------------------------------------------
# Yedekten geri yükleme (Güvenlik sekmesi — çalışan program içinden)
# ---------------------------------------------------------------------------
class BackupRestoreRequestSerializer(serializers.Serializer[dict[str, Any]]):
    """Kaynak İKİSİNDEN BİRİ: `name` (yedek klasöründen) YA DA `file` (yükleme).

    Parola/kurtarma anahtarı yalnız gövdede taşınır; yanıt ve günlüklerde
    yankılanmaz (security uçlarıyla aynı kural).
    """

    name = serializers.CharField(required=False, allow_blank=True, default="")
    file = serializers.FileField(required=False, allow_null=True, default=None)
    # Parola yolunda hesabın tanıtıcısı; boşsa oturumdaki hesap (live_restore).
    hesap = serializers.CharField(required=False, allow_blank=True, default="")
    password = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=False
    )
    recovery_key = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        ad = str(attrs.get("name") or "").strip()
        dosya = attrs.get("file")
        if bool(ad) == bool(dosya):
            raise serializers.ValidationError(
                "Yedek klasöründen bir dosya seçin YA DA elinizdeki yedek dosyasını yükleyin."
            )
        attrs["name"] = ad
        return attrs


class BackupListView(APIView):
    """`GET /api/v1/backups/` — yedek klasöründeki geri yüklenebilir dosyalar.

    Güvenlik dosyası kayıpken de açıktır (kayıp kilidinden çıkış yolu).
    """

    def get(self, request: Request) -> Response:
        return Response(live_restore_service.list_backups())


class BackupRestoreView(APIView):
    """`POST /api/v1/backups/restore/` — yedeği veritabanının yerine koyar.

    Başarıda süreç "yeniden başlat" kapısına girer (`restart_gate`): sonraki
    tüm API istekleri 503 `restart_required` döner, kullanıcı programı kapatıp
    yeniden açar. Hata hâlinde hedefe dokunulmaz ve kapı kurulmaz. Güvenlik
    dosyası kayıpken de açıktır: geri yükleme `guvenlik.json`'u yedeğin kurtarma
    başlığından yeniden yazar. Açık oturumda yalnız program yöneticisi; parola yolunda
    servis de yazarın rolünü ve hesabını denetler, kurtarma anahtarı yolunda denetlemez
    (`live_restore` modül başlığı "YETKİ"). Parola yolunda çekirdeğin ORM'siz hesap denetimi
    reddederse (`GeriYuklemeYetkisiz`, bir `ValueError`) yanıt 400'dür.
    """

    def post(self, request: Request) -> Response:
        req = BackupRestoreRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        yuklenen = req.validated_data["file"]
        with _service_errors():
            payload = live_restore_service.restore_and_require_restart(
                name=req.validated_data["name"],
                content=yuklenen.read() if yuklenen is not None else None,
                hesap=req.validated_data["hesap"],
                password=req.validated_data["password"],
                recovery_key=req.validated_data["recovery_key"],
            )
        return Response(payload)


# ---------------------------------------------------------------------------
# GitHub Release tabanlı uygulama güncellemesi (aile iskeletinden AYNEN)
# ---------------------------------------------------------------------------
class UpdateStatusView(APIView):
    """GitHub'daki son kararlı sürümü çalışan sürümle karşılaştırır."""

    def get(self, request: Request) -> Response:
        force = str(request.query_params.get("force", "")).lower() in TRUE_VALUES
        try:
            return Response(update_service.update_status(force=force))
        except update_service.UpdateError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class UpdateInstallerView(APIView):
    """Doğrulanmış Windows kurucusunu uygulama indirmesi olarak döndürür."""

    def get(self, request: Request) -> FileResponse:
        try:
            installer = update_service.download_latest_installer(force=True)
        except update_service.UpdateError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        # Savunma derinliği: dönen dosya güncelleme önbelleği içinde mi?
        update_dir = update_service.update_directory().resolve()
        if update_dir not in installer.resolve().parents:
            raise serializers.ValidationError("Güncelleme dosyası güvenli önbellek dışında.")
        return FileResponse(
            installer.open("rb"),
            as_attachment=True,
            filename=installer.name,
            content_type="application/vnd.microsoft.portable-executable",
        )
