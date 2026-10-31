#!/usr/bin/env bash
# =============================================================================
# kur.sh — OAB Defteri'ni yönetici yetkisi OLMADAN kurar
# =============================================================================
# Taşınabilir arşivin (.tar.gz) içinden çalıştırılır:
#
#     tar -xzf oab-defteri-*-linux-x64.tar.gz
#     cd oab-defteri-*
#     ./kur.sh
#
# Her şey kullanıcının kendi ev dizinine kurulur; sistem dosyalarına
# DOKUNULMAZ. Okul bilgisayarında yönetici parolası yoksa bu yol kullanılır
# (.deb kurulumu için `sudo` gerekir).
#
# Kaldırmak için: ./kaldir.sh   (verileriniz silinmez)
# =============================================================================
set -euo pipefail

KAYNAK="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HEDEF="$HOME/.local/opt/oab-defteri"
BIN_DIZINI="$HOME/.local/bin"
UYGULAMALAR="$HOME/.local/share/applications"
IKON_KOKU="$HOME/.local/share/icons/hicolor"

if [ ! -x "$KAYNAK/uygulama/oab-defteri" ]; then
    echo "HATA: Arşiv eksik görünüyor (uygulama/oab-defteri bulunamadı)." >&2
    exit 1
fi

echo "Kuruluyor: $HEDEF"
rm -rf "$HEDEF"
mkdir -p "$HEDEF" "$BIN_DIZINI" "$UYGULAMALAR"
cp -a "$KAYNAK/uygulama/." "$HEDEF/"

ln -sf "$HEDEF/oab-defteri" "$BIN_DIZINI/oab-defteri"

# Masaüstü kısayolu — Exec satırı ev dizinindeki yola çevrilir.
sed "s|^Exec=.*|Exec=$HEDEF/oab-defteri|" \
    "$KAYNAK/oab-defteri.desktop" > "$UYGULAMALAR/oab-defteri.desktop"
chmod 0644 "$UYGULAMALAR/oab-defteri.desktop"

for boyut in 16 24 32 48 64 128 256; do
    dizin="$IKON_KOKU/${boyut}x${boyut}/apps"
    mkdir -p "$dizin"
    cp "$KAYNAK/ikonlar/oab-defteri-${boyut}.png" "$dizin/oab-defteri.png"
done

command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database -q "$UYGULAMALAR" || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -q -f "$IKON_KOKU" || true

echo
echo "Kurulum tamamlandı."
echo "  Menüden 'OAB Defteri' ile açabilirsiniz."
echo "  Uçbirimden: oab-defteri"
case ":$PATH:" in
    *":$BIN_DIZINI:"*) ;;
    *)
        echo
        echo "NOT: $BIN_DIZINI PATH'inizde görünmüyor. Uçbirimden çalıştırmak için"
        echo "     ~/.bashrc dosyanıza şu satırı ekleyin:"
        echo "     export PATH=\"\$HOME/.local/bin:\$PATH\""
        ;;
esac
echo
echo "Verileriniz: $HOME/.local/share/oab-defteri"
