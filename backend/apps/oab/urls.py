"""`oab` URL'leri — `/api/v1/oab/` altında, kebab-case, çoğul kaynak adları (ailenin API sözleşmesi).

Yeni uç `okul`'daki gibi ADIYLA rol tablosuna (`rol_izinleri.KURALLAR`) ve yazma ucuysa izsiz yazım
kapısının `IZLI_UCLAR` ya da `MUAF_UCLAR` kümesine girer; girmezse testler düşer.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from apps.oab import views
from apps.oab import views_genel_kurul as gk

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        "okul-karti-bilgileri/",
        views.OkulKartiBilgileriView.as_view(),
        name="oab-okul-karti-bilgileri",
    ),
    path("terms/", views.TermListCreateView.as_view(), name="oab-term-list"),
    path("terms/<int:pk>/", views.TermDetailView.as_view(), name="oab-term-detail"),
    path("terms/<int:pk>/cancel/", views.TermCancelView.as_view(), name="oab-term-cancel"),
    # Yönetim kurulunun aylık toplantı günü kuralı (dönem ayarı; E01'in D bölümü, F1c 11. adım).
    path(
        "terms/<int:pk>/meeting-day/",
        views.TermMeetingDayView.as_view(),
        name="oab-term-meeting-day",
    ),
    # Kural sürümü güncellemesi: bağ, hedefler, fark ve revizyon geçişi (tasarım §6.2-5; F2 2. adım).
    path(
        "terms/<int:pk>/rule-revision/",
        views.TermRuleRevisionView.as_view(),
        name="oab-term-rule-revision",
    ),
    # Bağlanabilecek (kabul edilmiş ya da deftere işlenmiş) yönetim kurulu kararları (F1c 11. adım).
    path(
        "terms/<int:pk>/linkable-decisions/",
        views.TermLinkableDecisionsView.as_view(),
        name="oab-term-linkable-decisions",
    ),
    # Geçiş kurulumu (F1c 8. adımın servisleri; uçları ve ekranı 11. adımın birinci parçasında).
    path("transition/", views.TransitionView.as_view(), name="oab-transition"),
    path(
        "transition/inherited/",
        views.TransitionInheritedView.as_view(),
        name="oab-transition-inherited",
    ),
    path(
        "transition/election-counts/",
        views.TransitionElectionCountsView.as_view(),
        name="oab-transition-election-counts",
    ),
    path(
        "transition/decision-book/",
        views.TransitionDecisionBookView.as_view(),
        name="oab-transition-decision-book",
    ),
    path(
        "transition/decision-book/<int:pk>/cancel/",
        views.TransitionDecisionBookCancelView.as_view(),
        name="oab-transition-decision-book-cancel",
    ),
    # Genel Bakış'ın pano kalemleri (F1c 12. adım; hesaplanır, saklanmaz, yazmaz).
    path("dashboard/", views.DashboardView.as_view(), name="oab-dashboard"),
    # Gerekçe kutusunun yarım metni (F1c 11. adım; ortak "uyarı + gerekçe" bileşeni).
    path("drafts/", views.DraftTextView.as_view(), name="oab-draft-text"),
    path(
        "transition/complete/",
        views.TransitionCompleteView.as_view(),
        name="oab-transition-complete",
    ),
    path("persons/", views.PersonListCreateView.as_view(), name="oab-person-list"),
    path(
        "persons/from-personnel/",
        views.PersonFromPersonnelView.as_view(),
        name="oab-person-from-personnel",
    ),
    path(
        "persons/from-parent/",
        views.PersonFromParentView.as_view(),
        name="oab-person-from-parent",
    ),
    path("persons/<int:pk>/", views.PersonDetailView.as_view(), name="oab-person-detail"),
    path(
        "terms/<int:pk>/roster/<str:organ>/",
        views.OrganRosterView.as_view(),
        name="oab-organ-roster",
    ),
    path("memberships/", views.MembershipListCreateView.as_view(), name="oab-membership-list"),
    path(
        "memberships/<int:pk>/",
        views.MembershipDetailView.as_view(),
        name="oab-membership-detail",
    ),
    path(
        "memberships/<int:pk>/eligibility-basis/",
        views.MembershipEligibilityBasisView.as_view(),
        name="oab-membership-eligibility-basis",
    ),
    # Görev bölümü, yedek çağrısı, düşme, iptal, temsilciler, alım komisyonu (F1c 6. adım).
    path(
        "terms/<int:pk>/duty-assignment/yk/",
        views.YkDutyAssignmentView.as_view(),
        name="oab-yk-duty-assignment",
    ),
    path(
        "terms/<int:pk>/duty-assignment/dk/",
        views.DkDutyAssignmentView.as_view(),
        name="oab-dk-duty-assignment",
    ),
    path(
        "memberships/<int:pk>/substitute-call/yk/",
        views.MembershipSubstituteCallYkView.as_view(),
        name="oab-membership-substitute-call-yk",
    ),
    path(
        "memberships/<int:pk>/substitute-call/dk/",
        views.MembershipSubstituteCallDkView.as_view(),
        name="oab-membership-substitute-call-dk",
    ),
    path(
        "memberships/<int:pk>/drop/",
        views.MembershipDropView.as_view(),
        name="oab-membership-drop",
    ),
    path(
        "memberships/<int:pk>/cancel/",
        views.MembershipCancelView.as_view(),
        name="oab-membership-cancel",
    ),
    path(
        "representatives/",
        views.RepresentativeListCreateView.as_view(),
        name="oab-representative-list",
    ),
    path(
        "purchase-committee/",
        views.PurchaseCommitteeCreateView.as_view(),
        name="oab-purchase-committee-list",
    ),
    # Görev bölümü ve temsilci evrakı: liste, üretim ve basım (F1c 10. adım).
    path(
        "terms/<int:pk>/documents/",
        views.TermDocumentListView.as_view(),
        name="oab-term-documents",
    ),
    path(
        "terms/<int:pk>/documents/e01/",
        views.E01DocumentView.as_view(),
        name="oab-document-e01",
    ),
    path(
        "terms/<int:pk>/documents/e02/",
        views.E02DocumentView.as_view(),
        name="oab-document-e02",
    ),
    path(
        "terms/<int:pk>/documents/e03/",
        views.E03DocumentView.as_view(),
        name="oab-document-e03",
    ),
    # Yıllık iş takvimi (Genel Bakış; E14'ün verisi ve basımı; F2 11. adım).
    path(
        "terms/<int:pk>/annual-calendar/",
        gk.TermAnnualCalendarView.as_view(),
        name="oab-term-annual-calendar",
    ),
    path(
        "terms/<int:pk>/documents/e14/",
        gk.E14DocumentView.as_view(),
        name="oab-document-e14",
    ),
    # E12'nin gelen-giden evrak kaydı (öneri ve onay; plan F2 §7 U20). İndirme deseninden önce durur.
    path(
        "documents/<int:pk>/outgoing-record/",
        gk.DocumentOutgoingRecordView.as_view(),
        name="oab-document-outgoing-record",
    ),
    path(
        "documents/<int:pk>/<str:bicim>/",
        views.DocumentDownloadView.as_view(),
        name="oab-document-download",
    ),
    # ------------------------------------------------------------------ genel kurul (plan F2 §6.1)
    path("assemblies/", gk.AssemblyListView.as_view(), name="oab-assembly-list"),
    path("assemblies/<int:pk>/", gk.AssemblyDetailView.as_view(), name="oab-assembly-detail"),
    path("assemblies/<int:pk>/call/", gk.AssemblyCallView.as_view(), name="oab-assembly-call"),
    path(
        "assemblies/<int:pk>/principal-call/",
        gk.AssemblyPrincipalCallView.as_view(),
        name="oab-assembly-principal-call",
    ),
    path(
        "assemblies/<int:pk>/audit-board-call/",
        gk.AssemblyAuditBoardCallView.as_view(),
        name="oab-assembly-audit-board-call",
    ),
    path(
        "assemblies/<int:pk>/call-document/",
        gk.AssemblyCallDocumentView.as_view(),
        name="oab-assembly-call-document",
    ),
    path(
        "assemblies/<int:pk>/announcement/",
        gk.AssemblyAnnouncementView.as_view(),
        name="oab-assembly-announcement",
    ),
    path(
        "assemblies/<int:pk>/second-announcement/",
        gk.AssemblySecondAnnouncementView.as_view(),
        name="oab-assembly-second-announcement",
    ),
    path(
        "announcements/<int:pk>/evidence/",
        gk.AnnouncementEvidenceView.as_view(),
        name="oab-announcement-evidence",
    ),
    path(
        "announcements/<int:pk>/attachments/",
        gk.AnnouncementAttachmentsView.as_view(),
        name="oab-announcement-attachments",
    ),
    path(
        "assemblies/<int:pk>/first-meeting/",
        gk.AssemblyFirstMeetingView.as_view(),
        name="oab-assembly-first-meeting",
    ),
    path(
        "assemblies/<int:pk>/second-meeting/",
        gk.AssemblySecondMeetingView.as_view(),
        name="oab-assembly-second-meeting",
    ),
    path(
        "assemblies/<int:pk>/cancel/", gk.AssemblyCancelView.as_view(), name="oab-assembly-cancel"
    ),
    path(
        "assemblies/<int:pk>/attendance-corrections/",
        gk.AssemblyAttendanceCorrectionsView.as_view(),
        name="oab-assembly-attendance-corrections",
    ),
    path(
        "assemblies/<int:pk>/attendance-marks/",
        gk.AssemblyAttendanceMarksView.as_view(),
        name="oab-assembly-attendance-marks",
    ),
    path(
        "assemblies/<int:pk>/agenda/", gk.AssemblyAgendaView.as_view(), name="oab-assembly-agenda"
    ),
    path(
        "assemblies/<int:pk>/agenda-order/",
        gk.AssemblyAgendaOrderView.as_view(),
        name="oab-assembly-agenda-order",
    ),
    path(
        "agenda-items/<int:pk>/removal/",
        gk.AgendaItemRemovalView.as_view(),
        name="oab-agenda-item-removal",
    ),
    path(
        "agenda-items/<int:pk>/result/",
        gk.AgendaItemResultView.as_view(),
        name="oab-agenda-item-result",
    ),
    path(
        "agenda-items/<int:pk>/election/",
        gk.AgendaItemElectionView.as_view(),
        name="oab-agenda-item-election",
    ),
    path(
        "agenda-items/<int:pk>/election-form/",
        gk.AgendaItemElectionFormView.as_view(),
        name="oab-agenda-item-election-form",
    ),
    path(
        "agenda-items/<int:pk>/election-cancel/",
        gk.AgendaItemElectionCancelView.as_view(),
        name="oab-agenda-item-election-cancel",
    ),
    path(
        "agenda-items/<int:pk>/discharge/",
        gk.AgendaItemDischargeView.as_view(),
        name="oab-agenda-item-discharge",
    ),
    path(
        "agenda-items/<int:pk>/attachments/",
        gk.AgendaItemAttachmentsView.as_view(),
        name="oab-agenda-item-attachments",
    ),
    path(
        "agenda-items/<int:pk>/audit-board-attachment/",
        gk.AgendaItemAuditBoardAttachmentView.as_view(),
        name="oab-agenda-item-audit-board-attachment",
    ),
    path(
        "assemblies/<int:pk>/presiding-board/",
        gk.AssemblyPresidingBoardView.as_view(),
        name="oab-assembly-presiding-board",
    ),
    path(
        "assemblies/<int:pk>/presiding-board-cancel/",
        gk.AssemblyPresidingBoardCancelView.as_view(),
        name="oab-assembly-presiding-board-cancel",
    ),
    path(
        "assemblies/<int:pk>/candidates/",
        gk.AssemblyCandidatesView.as_view(),
        name="oab-assembly-candidates",
    ),
    path(
        "assemblies/<int:pk>/minutes/",
        gk.AssemblyMinutesView.as_view(),
        name="oab-assembly-minutes",
    ),
    path(
        "assemblies/<int:pk>/minutes-complete/",
        gk.AssemblyMinutesCompleteView.as_view(),
        name="oab-assembly-minutes-complete",
    ),
    path(
        "assemblies/<int:pk>/term-transition/",
        gk.AssemblyTermTransitionView.as_view(),
        name="oab-assembly-term-transition",
    ),
    # Genel kurul evrakı (E05-E13, E64): katalog, liste, üretim, Denetleme Kurulunun E05'i, adlı çıktı.
    path(
        "assembly-documents/catalog/",
        gk.AssemblyDocumentCatalogView.as_view(),
        name="oab-assembly-document-catalog",
    ),
    path(
        "assemblies/<int:pk>/documents/",
        gk.AssemblyDocumentListView.as_view(),
        name="oab-assembly-documents",
    ),
    path(
        "assemblies/<int:pk>/documents/e05/audit-board/",
        gk.AssemblyE05AuditBoardView.as_view(),
        name="oab-assembly-document-e05-audit-board",
    ),
    path(
        "assemblies/<int:pk>/documents/<str:kod>/named/",
        gk.AssemblyNamedDocumentView.as_view(),
        name="oab-assembly-document-named",
    ),
    path(
        "assemblies/<int:pk>/documents/<str:kod>/",
        gk.AssemblyDocumentView.as_view(),
        name="oab-assembly-document",
    ),
    # ------------------------------------------------------------------ gelen-giden evrak (M10)
    path("document-books/", gk.DocumentBookListView.as_view(), name="oab-document-book-list"),
    path("document-records/", gk.DocumentRecordListView.as_view(), name="oab-document-record-list"),
    path(
        "document-records/<int:pk>/attachments/",
        gk.DocumentRecordAttachmentsView.as_view(),
        name="oab-document-record-attachments",
    ),
    # Kullanıcı eklerinin indirilmesi (genel kurulun dosya ekleri, ilan kanıtları, evrak kaydının ekleri).
    path(
        "attachments/<int:pk>/", gk.AttachmentDownloadView.as_view(), name="oab-attachment-download"
    ),
]
