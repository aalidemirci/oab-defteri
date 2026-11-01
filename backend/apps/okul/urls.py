"""`okul` URL'leri — kebab-case, çoğul kaynak adları (ailenin API sözleşmesi).

`setup/status/` hem arayüz kurulum kapısının hem masaüstü sağlık denetiminin
(`desktop/server.py::HEALTH_PATH`) tek kaynağıdır — yolu değişirse üçü birlikte
güncellenir. Kilitliyken açık kalan uçlar bir AÇIK listededir (yol + yöntem;
`lock_middleware.KILITLI_IZINLI`): durum, oturum özeti, hesap listesi, kilit açma,
kurtarma anahtarıyla açılış ve Çık. `security/` ön eki artık muaf değildir: buraya
eklenen yeni bir uç kilitliyken kendiliğinden kapalıdır (`test_kilit_koruma.py`).
"""

from __future__ import annotations

from django.urls import path

from apps.okul import views, views_app, views_calendar, views_oturum, views_pool, views_yedek

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
    # Öğrenim seviyeleri (okul içi sabit 1-12 + hazırlık bayrağı)
    path("grade-levels/", views.GradeLevelsView.as_view(), name="grade-levels"),
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
    # Öğrenciler / Personel / Şubeler
    path("students/", views.StudentListCreateView.as_view(), name="student-list"),
    path("students/<int:pk>/", views.StudentDetailView.as_view(), name="student-detail"),
    # Ayrılış yolu ve "olası aynı kişi" birleştirmesi (tasarım §5.1, §13 D30)
    path("students/<int:pk>/leave/", views.StudentLeaveView.as_view(), name="student-leave"),
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
    path("class-sections/", views.ClassSectionListCreateView.as_view(), name="class-section-list"),
    path(
        "class-sections/<int:pk>/",
        views.ClassSectionDetailView.as_view(),
        name="class-section-detail",
    ),
    # İçe aktarma (dosya veya pano metni)
    path(
        "imports/students/preview/",
        views.StudentImportPreviewView.as_view(),
        name="import-students-preview",
    ),
    path(
        "imports/students/commit/",
        views.StudentImportCommitView.as_view(),
        name="import-students-commit",
    ),
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
    # Şablon indirme
    path("templates/students/", views.StudentTemplateView.as_view(), name="template-students"),
    path("templates/personnel/", views.PersonnelTemplateView.as_view(), name="template-personnel"),
    # Güvenlik durumu ve ilk hesap (tasarım §4.3, §4.4.4; parolayı kaldırma ucu yok)
    path("security/status/", views.SecurityStatusView.as_view(), name="security-status"),
    path("security/enable/", views.SecurityEnableView.as_view(), name="security-enable"),
    # Oturum (tasarım §4.4.3, TK14; views_oturum): özet, kilit ekranının hesap listesi,
    # kilit açma, Kilitle, kurtarma anahtarıyla açılış, kendi parolasını değiştirme.
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
    # GitHub Release tabanlı uygulama güncellemesi (tasarım TK4)
    path("updates/latest/", views.UpdateStatusView.as_view(), name="update-latest"),
    path(
        "updates/latest/installer/",
        views.UpdateInstallerView.as_view(),
        name="update-installer",
    ),
]
