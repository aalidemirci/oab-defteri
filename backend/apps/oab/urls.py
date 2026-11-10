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
]
