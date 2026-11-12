"""`okul` URL'leri — kebab-case, çoğul kaynak adları (ailenin API sözleşmesi).

`setup/status/` hem arayüz kurulum kapısının hem masaüstü sağlık denetiminin
(`desktop/server.py::HEALTH_PATH`) tek kaynağıdır — yolu değişirse üçü birlikte
güncellenir. Kilitliyken açık kalan uçlar bir AÇIK listededir (yol + yöntem;
`lock_middleware.KILITLI_IZINLI`): durum, oturum özeti, hesap listesi, kilit açma,
kurtarma anahtarıyla açılış ve Çık. `security/` ön eki artık muaf değildir: buraya
eklenen yeni bir uç kilitliyken kendiliğinden kapalıdır (`test_kilit_koruma.py`). Açık
oturumda her uç ADIYLA rol tablosundadır (`rol_izinleri.KURALLAR`; tasarım §4.4.2): yeni bir
uç oraya bilinçli eklenmedikçe her role kapalıdır (`test_rol_koruma.py`). Adlar tekildir.
"""

from __future__ import annotations

from django.urls import path

from apps.okul import (
    views,
    views_app,
    views_calendar,
    views_erisim_gunlugu,
    views_hesaplar,
    views_oturum,
    views_pool,
    views_yedek,
)

urlpatterns = [
    # Arayüzden düzenli çıkış (tasarım §4.2 "Kapanış", §4.5): her oturum durumunda
    # parolasız; kilit ve yeniden başlat kapıları bu yolu geçirir (views_app).
    path("app/quit/", views_app.AppQuitView.as_view(), name="app-quit"),
    # Son oturum kartı (T15, §13 D4).
    path(
        "dashboard/last-session/",
        views_app.SonOturumView.as_view(),
        name="dashboard-last-session",
    ),
    # Kurulum sihirbazı
    path("setup/status/", views.SetupStatusView.as_view(), name="setup-status"),
    path("setup/school-config/", views.SchoolConfigView.as_view(), name="setup-school-config"),
    path("setup/complete/", views.SetupCompleteView.as_view(), name="setup-complete"),
    # Genel Bakış "Başlangıç Yol Haritası" kartının kullanıcı işaretleri (kişisel veri yok)
    path("setup/roadmap/", views.SetupRoadmapView.as_view(), name="setup-roadmap"),
    # Ders yılları + dönemler
    path("school-years/", views.SchoolYearListCreateView.as_view(), name="school-year-list"),
    path(
        "school-years/<int:pk>/terms/",
        views.SchoolTermView.as_view(),
        name="school-year-terms",
    ),
    path(
        "school-years/<int:pk>/activate/",
        views.SchoolYearActivateView.as_view(),
        name="school-year-activate",
    ),
    # Kapalı günler: resmî/dini tatil, öğrenciye kapalı gün, idari izin (tasarım §5.1)
    path("holidays/", views_calendar.HolidayListCreateView.as_view(), name="holiday-list"),
    path("holidays/seed/", views_calendar.HolidaySeedView.as_view(), name="holiday-seed"),
    path(
        "holidays/<int:pk>/",
        views_calendar.HolidayDetailView.as_view(),
        name="holiday-detail",
    ),
    # Personel; ayrılış yolu ve "olası aynı kişi" birleştirmesi (tasarım §5.1, §13 D30)
    path("personnel/", views.PersonnelListCreateView.as_view(), name="personnel-list"),
    path("personnel/<int:pk>/", views.PersonnelDetailView.as_view(), name="personnel-detail"),
    path(
        "personnel/<int:pk>/leave/",
        views.PersonnelLeaveView.as_view(),
        name="personnel-leave",
    ),
    path(
        "personnel/<int:pk>/merge/",
        views.PersonnelMergeView.as_view(),
        name="personnel-merge",
    ),
    # Ayrılış havuzu: aktarım kimseyi ayırmaz; karar burada verilir.
    path("leave-pool/", views_pool.LeavePoolView.as_view(), name="leave-pool"),
    path(
        "leave-pool/resolve/",
        views_pool.LeavePoolResolveView.as_view(),
        name="leave-pool-resolve",
    ),
    # İçe aktarma (dosya veya pano metni)
    path(
        "imports/personnel/preview/",
        views.PersonnelImportPreviewView.as_view(),
        name="import-personnel-preview",
    ),
    path(
        "imports/personnel/commit/",
        views.PersonnelImportCommitView.as_view(),
        name="import-personnel-commit",
    ),
    # Veli listesi (T5; yalnız dosya): özet ve silme, önizleme ve aktarım, şablon
    path("parent-roster/", views.ParentRosterView.as_view(), name="parent-roster"),
    path(
        "imports/parents/preview/",
        views.ParentImportPreviewView.as_view(),
        name="import-parents-preview",
    ),
    path(
        "imports/parents/commit/",
        views.ParentImportCommitView.as_view(),
        name="import-parents-commit",
    ),
    # Şablon indirme
    path("templates/personnel/", views.PersonnelTemplateView.as_view(), name="template-personnel"),
    path("templates/parents/", views.ParentTemplateView.as_view(), name="template-parents"),
    # Güvenlik durumu ve ilk hesap (tasarım §4.3, §4.4.4; parolayı kaldırma ucu yok)
    path("security/status/", views.SecurityStatusView.as_view(), name="security-status"),
    path("security/enable/", views.SecurityEnableView.as_view(), name="security-enable"),
    # Oturum (tasarım §4.4.3, TK14; views_oturum): özet, kilit ekranının hesap listesi,
    # kilit açma, Kilitle, kurtarma anahtarıyla açılış, kendi parolasını değiştirme,
    # boşta kilit süresi.
    path("security/session/", views_oturum.OturumOzetiView.as_view(), name="security-session"),
    path(
        "security/accounts/",
        views_oturum.KilitEkraniHesaplariView.as_view(),
        name="security-accounts",
    ),
    path("security/unlock/", views_oturum.SecurityUnlockView.as_view(), name="security-unlock"),
    path("security/lock/", views_oturum.SecurityLockView.as_view(), name="security-lock"),
    path("security/recover/", views_oturum.SecurityRecoverView.as_view(), name="security-recover"),
    path(
        "security/change-password/",
        views_oturum.SecurityChangePasswordView.as_view(),
        name="security-change-password",
    ),
    # Boşta kilit süresi (Ayarlar → Güvenlik; TK14, §13 D11): yalnız açık oturumda —
    # kilitliyken KAPALIDIR (lock_middleware.KILITLI_IZINLI'de değildir).
    path(
        "security/idle-lock/",
        views_oturum.BostaKilitSuresiView.as_view(),
        name="security-idle-lock",
    ),
    # Bütünlük kartları (tasarım §4.6.3, §4.6.1 kural 1 ve 4, §4.4.4): kısmi yetki ayrı uçla
    # (§4.4.2; plan F1b-2) — kendi kartları her rol, denetim kartları program yöneticisi ve
    # Denetleme Kurulu, iki depo kartı ve sahipsiz sarmalların onayla silinmesi yalnız program
    # yöneticisi (`rol_izinleri`). Kilitliyken KAPALIDIR (açık listede değildir).
    path(
        "security/integrity/",
        views_oturum.ButunlukDurumuView.as_view(),
        name="security-integrity",
    ),
    path(
        "security/integrity/audit/",
        views_oturum.DenetimKartlariView.as_view(),
        name="security-integrity-audit",
    ),
    path(
        "security/integrity/two-store/",
        views_oturum.IkiDepoKartiView.as_view(),
        name="security-integrity-two-store",
    ),
    path(
        "security/integrity/orphan-wraps/",
        views_oturum.SahipsizSarmalView.as_view(),
        name="security-integrity-orphan-wraps",
    ),
    # Geri yükleme kartının "Gördüm"ü (plan F1b-2; tasarım §4.4.4): yalnız Denetleme Kurulu,
    # `ISARET` satırı. Kilitliyken KAPALIDIR.
    path(
        "security/integrity/restore-seen/",
        views_oturum.GeriYuklemeGordumView.as_view(),
        name="security-integrity-restore-seen",
    ),
    # Erişim günlüğünün okuma ekranı (plan F1b-2; tasarım §4.6.4): program yöneticisi ve
    # Denetleme Kurulu; okuma iz bırakmaz. Kilitliyken KAPALIDIR.
    path("access-log/", views_erisim_gunlugu.ErisimGunluguView.as_view(), name="access-log"),
    # Parola yenilenme bildirimi (tasarım §4.4.3, tehdit 12): oturumdaki hesabın bildirimi ve
    # "Gördüm" (izli). Kilitliyken KAPALIDIR.
    path(
        "security/integrity/reset-notice/",
        views_oturum.ParolaBildirimiView.as_view(),
        name="security-integrity-reset-notice",
    ),
    # Kullanıcılar (plan F1b-2 "Kullanıcılar uçları"; tasarım §4.4.2 Kullanıcılar satırı): yalnız
    # program yöneticisi (`rol_izinleri`), yalnız açık oturumda (kilitliyken KAPALIDIR).
    path("accounts/", views_hesaplar.KullanicilarView.as_view(), name="account-list"),
    path(
        "accounts/options/",
        views_hesaplar.KullaniciSecenekleriView.as_view(),
        name="account-options",
    ),
    path(
        "accounts/<uuid:hesap_id>/",
        views_hesaplar.KullaniciAyrintisiView.as_view(),
        name="account-detail",
    ),
    path(
        "accounts/<uuid:hesap_id>/close/",
        views_hesaplar.KullaniciKapatView.as_view(),
        name="account-close",
    ),
    path(
        "accounts/<uuid:hesap_id>/unsuspend/",
        views_hesaplar.KullaniciAskidanCikarView.as_view(),
        name="account-unsuspend",
    ),
    path(
        "accounts/<uuid:hesap_id>/reset-password/",
        views_hesaplar.KullaniciParolaSifirlaView.as_view(),
        name="account-reset-password",
    ),
    # Hesap teslim pusulası (E63; plan F1b-2, F1c 9. adım): yalnız PDF, dosya saklanmaz; üretimi
    # `GeneratedDocument` kaydı, dosyanın izi `BASIM` satırıdır.
    path(
        "accounts/<uuid:hesap_id>/handover-slip/",
        views_hesaplar.KullaniciTeslimPusulasiView.as_view(),
        name="account-handover-slip",
    ),
    # Kurtarma anahtarı belgesi (tasarım §9.7): anahtar kurtarma sarmalını açıyorsa PDF.
    # KİLİTLİYKEN KAPALIDIR (lock_middleware.KILITLI_IZINLI'de değildir).
    path(
        "security/recovery-key/pdf/",
        views.SecurityRecoveryKeyPdfView.as_view(),
        name="security-recovery-key-pdf",
    ),
    # Kurtarma anahtarının saklandığını doğrulama ve anahtarı yenileme (tasarım
    # §4.4.4 `kurtarma.dogrulandi`, §13 D14). İkisi de kilit açma yolu değildir:
    # kilitliyken KAPALI.
    path(
        "security/recovery-key/confirm/",
        views.SecurityRecoveryKeyConfirmView.as_view(),
        name="security-recovery-key-confirm",
    ),
    path(
        "security/recovery-key/renew/",
        views.SecurityRecoveryKeyRenewView.as_view(),
        name="security-recovery-key-renew",
    ),
    # "Güvenlik dosyasını sıfırla ve kuruluma dön" — yalnız korunan veri yokken (409 aksi).
    path(
        "security/state/reset/",
        views.SecurityStateResetView.as_view(),
        name="security-state-reset",
    ),
    path(
        "backups/encrypted/",
        views.EncryptedBackupDownloadView.as_view(),
        name="encrypted-backup-download",
    ),
    # Dış yedek hatırlatması (tasarım §16 R6): son indirme + süre; kilitliyken kapalı.
    path(
        "backups/external/",
        views_yedek.DisYedekView.as_view(),
        name="backup-external-reminder",
    ),
    # Yedekten geri yükleme (Güvenlik sekmesi — çalışan program içinden)
    path("backups/", views.BackupListView.as_view(), name="backup-list"),
    path("backups/restore/", views.BackupRestoreView.as_view(), name="backup-restore"),
    # Aç penceresinde seçilen dosyanın başlığı (kullanıcı kararı 06.11.2026): yol gövdede gider.
    path("backups/inspect/", views.BackupInspectView.as_view(), name="backup-inspect"),
    # Yedek Raporu (plan F1b-3): yalnız PDF, saklanmaz; izi `BASIM` satırıdır.
    path("backups/report/", views_yedek.YedekRaporuView.as_view(), name="backup-report"),
    # GitHub Release tabanlı uygulama güncellemesi (tasarım TK4)
    path("updates/latest/", views.UpdateStatusView.as_view(), name="update-latest"),
    path(
        "updates/latest/installer/",
        views.UpdateInstallerView.as_view(),
        name="update-installer",
    ),
]
