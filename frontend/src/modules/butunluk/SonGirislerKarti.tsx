// Genel Bakış'ta "Son Girişler" kartı (tasarım §4.6.3 "Kâğıt çapası", §4.3 tehdit 3 ve 12;
// plan F1b-1 alt commit c).
//
// İki şey söyler:
// 1. Oturumdaki hesabın kilit ekranından yaptığı son girişler (denetim izinin `GIRIS`
//    satırları; YALNIZ bu hesabın, en yeni önce, en çok 10). İlki bu oturumdur: oturum yalnız
//    kilit ekranından (parola ya da kurtarma anahtarı) açılınca `GIRIS` yazılır; kurulumdaki
//    ilk hesabın oturumu giriş yazmaz, o zaman liste boştur. Başkasının parolası sıfırlanıp
//    hesabıyla girilirse sahibi bu girişi burada görür (tehdit 12'nin kalıcı karşılığı).
// 2. Denetim izinin son kaydı — kâğıt çapası: "Kayıt no: N · Zincir: XXXX-XXXX" (son kaydın
//    sırası ve mührünün ilk 8 onaltılık hanesi). Kullanıcı bu satırı zaman zaman kâğıda
//    yazar; veritabanı kilit işaretiyle birlikte eski bir kopyayla değiştirilirse program
//    fark etmez, kâğıt fark ettirir (tasarım §4.6.3 "Kalan risk"). Aylık bildirime, deftere
//    geçirilecek baskıya ve devir-teslim tutanağına basılması o belgelerle sonraki fazlardadır.
//
// OKUNAMAYAN BÖLÜM "YOK" DEMEZ (fail-closed): backend okunamayan kartı boş değerle doldurup
// adını `okunamayan`'a yazar (`son_girisler` → `[]`, `kagit_capasi` → null). Boş liste ancak
// okunabildiyse "henüz giriş yapılmadı" demektir; okunamadıysa kart bunu söyler (yanlış olgu
// bildirmez, tehdit 12'nin öğüdü sessizce kaybolmaz). Sayfa "Bütünlük Durumu Okunamadı"
// uyarısını da gösterir.
//
// Kişisizdir: başka hesabın girişi ve kişi adı yoktur. Kayıt no ayrımsız yazılır (kâğıda
// aynen geçirilen bir kimliktir; sözlük §1 "Denetim izi").

import { formatDateTime } from "../../lib/format";
import type { KagitCapasi } from "./api";
import KartKabugu from "./KartKabugu";
import {
  SON_GIRISLER_KARTI_BASLIGI,
  SON_GIRISLER_OKUNAMADI_METNI,
  SON_KAYIT_OKUNAMADI_METNI,
  kagitCapasiSatiri,
} from "./metinler";

interface SonGirislerKartiProps {
  girisler: readonly string[];
  capa: KagitCapasi | null;
  /** Girişler okunamadı (`okunamayan` içinde `son_girisler`): boş liste "giriş yok" değildir. */
  girislerOkunamadi?: boolean;
  /** Son kayıt okunamadı (`okunamayan` içinde `kagit_capasi`). */
  capaOkunamadi?: boolean;
}

export default function SonGirislerKarti({
  girisler,
  capa,
  girislerOkunamadi = false,
  capaOkunamadi = false,
}: SonGirislerKartiProps) {
  return (
    <KartKabugu
      id="son-girisler-karti"
      baslik={SON_GIRISLER_KARTI_BASLIGI}
      ikon="history"
      ton="bilgi"
    >
      {girislerOkunamadi ? (
        <p className="text-body-medium text-on-surface">{SON_GIRISLER_OKUNAMADI_METNI}</p>
      ) : girisler.length > 0 ? (
        <>
          <p className="text-body-medium text-on-surface">
            Hesabınızla kilit ekranından yapılan son girişler:
          </p>
          <ul className="list-disc space-y-0.5 pl-5 text-body-medium text-on-surface">
            {girisler.map((an, i) => (
              <li key={an}>
                {formatDateTime(an)}
                {i === 0 ? " · bu oturum" : ""}
              </li>
            ))}
          </ul>
          <p className="text-body-small text-on-surface-variant">
            Tanımadığınız bir giriş varsa parolanızı değiştirin ve Denetleme Kuruluna bildirin.
          </p>
        </>
      ) : (
        <p className="text-body-medium text-on-surface">
          Bu hesapla henüz kilit ekranından giriş yapılmadı.
        </p>
      )}
      {capaOkunamadi && (
        <div className="border-t border-outline-variant/70 pt-3">
          <p className="text-body-medium text-on-surface">{SON_KAYIT_OKUNAMADI_METNI}</p>
        </div>
      )}
      {!capaOkunamadi && capa !== null && (
        <div className="space-y-1 border-t border-outline-variant/70 pt-3">
          <p className="text-label-large text-on-surface-variant">Denetim izinin son kaydı</p>
          <p className="font-mono text-body-large text-on-surface">{kagitCapasiSatiri(capa)}</p>
          <p className="text-body-small text-on-surface-variant">
            Bu satırı zaman zaman tarihiyle birlikte kâğıda not edin. Sonradan burada görülen kayıt
            no&apos;su kâğıttakinden küçükse kayıtlar geri sarılmıştır; Denetleme Kuruluna bildirin.
          </p>
        </div>
      )}
    </KartKabugu>
  );
}
