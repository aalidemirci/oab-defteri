"""`oab` URL'leri — `/api/v1/oab/` altında, kebab-case, çoğul kaynak adları (ailenin API sözleşmesi).

Yeni uç `okul`'daki gibi ADIYLA rol tablosuna (`rol_izinleri.KURALLAR`) ve yazma ucuysa izsiz yazım
kapısının `IZLI_UCLAR` ya da `MUAF_UCLAR` kümesine girer; girmezse testler düşer.
"""

from __future__ import annotations

from django.urls import URLPattern, URLResolver, path

from apps.oab import views

urlpatterns: list[URLPattern | URLResolver] = [
    path(
        "okul-karti-bilgileri/",
        views.OkulKartiBilgileriView.as_view(),
        name="oab-okul-karti-bilgileri",
    ),
    path("terms/", views.TermListCreateView.as_view(), name="oab-term-list"),
    path("terms/<int:pk>/", views.TermDetailView.as_view(), name="oab-term-detail"),
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
    path(
        "documents/<int:pk>/<str:bicim>/",
        views.DocumentDownloadView.as_view(),
        name="oab-document-download",
    ),
]
