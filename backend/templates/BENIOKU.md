# Evrak şablonları

Aile iskeletinden alındı; yorumları OAB Defteri'ne göre yazıldı, görünüm ve davranış
değişmedi:

- `print/_design.css` — "Kurumsal Sade" baskı tasarım dili (renk ve tipografi
  token'ları). `base.html` içine Django `{% include %}` ile gömülür; `text-transform`
  YASAK, DejaVu Sans, `--pr-*` token'ları.
- `documents/base.html` — ortak resmî evrak tabanı (antet `shared.letterhead`
  üzerinden). Evrak çizicisi `documents/evrak.html` (tasarım §9.1) ve kurtarma
  anahtarı belgesi `documents/kurtarma_anahtari.html` (program belgesi, §9.7) bu
  tabanı `extends` eder.

PyInstaller spec bu ağacı pakete kaynak olarak kopyalar.
