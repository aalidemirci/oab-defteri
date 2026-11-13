#!/usr/bin/env bash
# =============================================================================
# packaging/linux/sistem_denetimi.sh — kurulum provasının sistem kütüphanesi denetimleri
# =============================================================================
# Pardus 25 saha bulgusu (12.11.2026): paket bullseye'da derlenir; gömülü bullseye
# libstdc++/libgbm/… sistemden yüklenen yeni Mesa sürücüsünü kırıyordu ("Could not
# initialize GLX" → Aborted). Kurulum provası ekransız koştuğu için yakalamadı: aşağıdaki
# üç denetim aynı sınıfı pencere açmadan yakalar.
#
# Kullanım (kaynak olarak alınır, çalıştırılmaz; apt_dene.sh gibi):
#
#     . "$(dirname "${BASH_SOURCE[0]}")/sistem_denetimi.sh"
#     sistemden_alinanlar_pakette_yok /opt/oab-defteri
#     paket_elfleri_cozuluyor /opt/oab-defteri
#     mesa_paketle_baglaniyor /opt/oab-defteri/_internal NESNE...
#
# Her işlev başarısızlıkta HATA satırını stderr'e basar ve 1 döner. kap-ici-test.sh onları
# `set -euo pipefail` altında ÇIPLAK deyim olarak çağırır, dönüş 1 provayı durdurur.
# Davranış sahte paket ağacı ve sahte `ldd` ile sınanır, çağrı biçimi de metinle bağlanır
# (packaging/tests/test_sistem_kutuphaneleri.py).
# =============================================================================

# Desen packaging/linux/sistem_kutuphaneleri.py::SISTEMDEN_ERE ile AYNI (kapı testi sınar).
SISTEMDEN_ERE='^(libstdc\+\+\.so\.6|libgcc_s\.so\.1|libgbm\.so\.1|libdrm\.so\.2|libdrm_[a-z0-9]+\.so\.[0-9]+|libglapi\.so\.0|lib(E?(Open)?GLX?(ESv1_CM|ESv2)?(dispatch)?)\.so\.[0-9]+|lib(GLX|EGL)_mesa\.so\.0|libwayland-client\.so\.0|libwayland-server\.so\.0|libX11-xcb\.so\.1|libxcb-glx\.so\.0|libxcb-present\.so\.0|libxcb-sync\.so\.1|libxcb-dri2\.so\.0|libxcb-dri3\.so\.0|libxshmfence\.so\.1|libexpat\.so\.1|libz\.so\.1|libzstd\.so\.1)(\.[0-9]+)*$'

# İSTEĞE BAĞLI Qt parçaları ldd denetiminin DIŞINDADIR (eksikleri BİLGİ olarak basılır): Qt
# onları yalnız gerektiğinde yükler, yüklenemezse atlar; program hiçbirini kullanmaz ve
# bağımlılıkları Depends'te bilerek YOKTUR (ilk koşu, debian:13, 12.11.2026):
#   Wayland platform eklentisi ve kitaplıkları (libwayland-cursor0, libwayland-egl1). DİKKAT
#     (denetim bulgusu 13.11.2026): libwayland-client sistemden alındığı için bu iki paketin
#     kurulu olduğu her makinede (GNOME/GTK masaüstleri) eklenti eksiksiz bağlanır ve Qt onu
#     Wayland oturumunda xcb'den ÖNCE yükler — eskiden gömülü Wayland 1.18
#     `wl_proxy_marshal_flags`'i vermediği için bu yol çalışamazdı. Pencere yolu bu yüzden
#     Depends'le değil, paketin çalışma zamanı kancasında (pyinstaller/rthook_od.py) Qt'yi
#     sınanmış xcb'ye sabitleyerek korunur; Wayland oturumunda pencere XWayland üzerinden
#     açılır. Wayland yolunu açmak gerçek pencere sınaması ister.
#   platformthemes/libqgtk3 (GTK 3) — yalnız masaüstü teması
#   printsupport (libcups2) — evrak WeasyPrint'ten basılır (spec: QtPrintSupport yok)
#   Multimedia/SpatialAudio/TextToSpeech (libpulse0) — QML toplamasıyla gelir, kullanılmaz
# Pencere yolu (libqxcb, xcbglintegrations, QtWebEngine, QtWidgets) bu desene GİRMEZ.
ISTEGE_BAGLI_ELF='^_internal/PySide6/Qt/(lib/libQt6(Wayland[A-Za-z]*|WlShellIntegration|Multimedia[A-Za-z]*|SpatialAudio|TextToSpeech)\.so\.6|plugins/(platforms/libqwayland-[a-z-]+\.so|wayland-[a-z-]+/[^/]+\.so|platformthemes/libqgtk3\.so|printsupport/libcupsprintersupport\.so)|qml/(QtWayland|QtMultimedia|QtTextToSpeech)/.+\.so)$'

# sistemden_alinanlar_pakette_yok KOK
# Grafik sürücüsüyle paylaşılan kütüphanelerden (SISTEMDEN_ERE) hiçbiri paket ağacında
# dosya ya da sembolik bağ olarak bulunmamalı.
sistemden_alinanlar_pakette_yok() {
    local kok="$1" bulgu
    bulgu="$(find "$kok" \( -type f -o -type l \) -printf '%f\n' |
        grep -E "$SISTEMDEN_ERE" | sort -u || true)"
    if [ -n "$bulgu" ]; then
        echo "HATA: sistemden alınması gereken kütüphaneler pakette (spec \`sistemden_suz\`):" >&2
        echo "$bulgu" >&2
        return 1
    fi
    echo "   sistemden alınan kütüphanelerin hiçbiri pakette yok"
}

# paket_elfleri_cozuluyor KOK
# Önyükleyici `KOK/_internal`'ı kitaplık arama yoluna koyar; ldd aynı yolla çalıştırılır. Bir
# bağımlılık ne pakette ne bu dağıtımda (Depends ile) varsa "not found" çıkar. İsteğe bağlı
# Qt parçalarının (ISTEGE_BAGLI_ELF) eksikleri yalnız BİLGİ'dir.
paket_elfleri_cozuluyor() {
    local kok="$1" elf eksik goreli hata=""
    local ic="$kok/_internal"
    while IFS= read -r -d '' elf; do
        # ELF imzası: 0x7f 'E' 'L' 'F' (yalnız "ELF" ile başlayan bir metin dosyası sayılmaz).
        head -c 4 "$elf" 2>/dev/null | grep -q $'^\x7fELF' || continue
        eksik="$(LD_LIBRARY_PATH="$ic" ldd "$elf" 2>/dev/null | grep 'not found' | sort -u || true)"
        [ -n "$eksik" ] || continue
        goreli="${elf#"$kok"/}"
        if printf '%s\n' "$goreli" | grep -Eq "$ISTEGE_BAGLI_ELF"; then
            echo "   BİLGİ (isteğe bağlı): $goreli:" $(printf '%s\n' "$eksik" | awk '{print $1}')
            continue
        fi
        hata+="${goreli}:"$'\n'"$eksik"$'\n'
    done < <(find "$kok" -type f \( -name '*.so' -o -name '*.so.*' -o -perm -u+x \) -print0)
    if [ -n "$hata" ]; then
        echo "HATA: paketteki ikililerin bağımlılığı bu dağıtımda bulunamadı (Depends eksik):" >&2
        printf '%s' "$hata" >&2
        return 1
    fi
    echo "   paketteki ikililerin bağımlılıkları çözülüyor"
}

# mesa_paketle_baglaniyor IC NESNE...
# Sistemin Mesa sürücüsü paketin kütüphaneleriyle eksik sembolsüz bağlanıyor mu? Sürücü GPU
# olmadan da kurulur; `ldd -r` bütün yer değiştirmeleri çözer. Sürücünün KENDİ eksikleri
# (paket yolu olmadan da görünen satırlar) sayılmaz; yalnız paket yolu (IC) eklenince
# DOĞANLAR hata olur — debian:13'te saha hatası tam böyle görünür ("GLIBCXX_3.4.29 not
# found", "undefined symbol: gbm_bo_create_with_modifiers2", "wl_proxy_marshal_flags").
# Var olmayan NESNE atlanır (eşleşmeyen glob); üçten azı bulunursa denetim boşa koşar → hata.
mesa_paketle_baglaniyor() {
    local ic="$1" nesne taban paketle yeni sayi=0 hata=""
    shift
    for nesne in "$@"; do
        [ -e "$nesne" ] || continue
        sayi=$((sayi + 1))
        taban="$(ldd -r "$nesne" 2>&1 | grep -E 'not found|undefined symbol' | sort -u || true)"
        paketle="$(LD_LIBRARY_PATH="$ic" ldd -r "$nesne" 2>&1 |
            grep -E 'not found|undefined symbol' | sort -u || true)"
        yeni="$(comm -13 <(printf '%s\n' "$taban") <(printf '%s\n' "$paketle") | sed '/^$/d')"
        if [ -n "$yeni" ]; then
            hata+="${nesne}:"$'\n'"$(printf '%s\n' "$yeni" | head -5)"$'\n'
        fi
    done
    if [ "$sayi" -lt 3 ]; then
        echo "HATA: Mesa sürücü dosyaları bulunamadı ($sayi); denetim boşa koşar" >&2
        return 1
    fi
    if [ -n "$hata" ]; then
        echo "HATA: paketteki kütüphaneler sistemin Mesa sürücüsünü kırıyor (sürücüyle paylaşılan" >&2
        echo "      kütüphane pakete gömülmüş — packaging/linux/sistem_kutuphaneleri.py):" >&2
        printf '%s' "$hata" >&2
        return 1
    fi
    echo "   $sayi Mesa nesnesi paket yoluyla eksiksiz bağlandı"
}
