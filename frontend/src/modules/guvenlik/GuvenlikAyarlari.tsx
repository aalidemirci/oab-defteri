// Güvenlik ayarları bölümü — Ayarlar sayfasına bir sekme olarak takılır (sözlük §4.6).
//
// Kartlar, sırasıyla (başlıklar sabit addır, durum başlığın altındaki cümlededir):
//   * "Hesap ve Parola" — oturumdaki hesabın rol etiketi ve tanıtıcısı (kişi adı yok,
//     sözlük §5), "Parolayı değiştir" ve "Kilitle". Her hesap burada KENDİ parolasını
//     değiştirir (tasarım §4.4.2 matrisi: bütün roller; TK15). Parola politikası ve güç
//     göstergesi kilit ekranındakiyle aynı paylaşılan alanlardan gelir
//     (`oturum/YeniParolaAlanlari`, `oturum/parolaPolitikasi`); yeni parola eskisiyle
//     aynı olamaz. Değişim oturum sözleşmesinden geçer (`oturum/eylemler.parolayiDegistir`;
//     pencere yeniden YÜKLENMEZ, tasarım §13 D53). "Kilitle" üst çubuktakiyle aynı yoldur
//     (`oturum/useKilitle`; pencere yeniden yüklenir).
//   * "Boşta Kilit Süresi" — 3-30 dakika, varsayılan 10 (`BostaKilitSuresiKarti`;
//     yalnız hesap kurulduktan sonra).
//   * "Şifreleme" — şifrelenen ve şifrelenmeyen alanlar, dürüst sınır "en zayıf hesap
//     parolası kadar" (tasarım §4.4.6). Metinler `metinler.ts`'ten gelir ve DÜRÜSTTÜR:
//     bu koruma alan şifrelemesidir, tam disk şifrelemesi değildir.
//   * Kurtarma kartları (bekleyen anahtar paneli, doğrula, yenile, kurtarma anahtarı
//     belgesi) ve yedek kartları. Kurtarma kartlarının yalnız program yöneticisine
//     görünmesi rol kapısıyla 2. adımda gelir (bugün yalnız program yöneticisi hesabı
//     açılabilir).
//
// Program yöneticisi hesabı YALNIZ kurulum sihirbazının ilk adımında kurulur (kurtarma
// anahtarı orada gösterilir ve saklandığı doğrulanır); bu ekranda "hesabı kur" ya da
// "parolayı kaldır" eylemi YOKTUR (tasarım §4.4.3: kurulumdan sonra hesapsız durum yoktur).
// Hesap kurulmamışsa (kurulum kapısı bunu zaten sihirbaza yönlendirir) yalnız sihirbaza
// giden bağlantı gösterilir. Aile iskeletinin kütüphaneye bağlı Görev Devri kartı
// F1a-2'de söküldü (OAB devir-teslimi F4'te — tasarım §13 D10).
// Yenilenen anahtar modül belleğinde bekler (`bekleyenAnahtar`) ve bu ekranda
// `KurtarmaAnahtariPaneli` ile saklatılıp doğrulatılır; doğrulanınca bırakılır.
// "Parolayı değiştir" penceresi açılınca "Mevcut parola" alanı odaktadır
// (`ui/Dialog` `initialFocusRef`). Hata hangi alanınsa orada çıkar ve odak oraya döner:
// "Parola hatalı." (mevcut parola yanlış; hesabın hatalı deneme sayacına ve gecikmesine
// sayılır) "Mevcut parola"nın altında, alan boşaltılır; politika ve sunucunun yeni parola
// reddi "Yeni parola"nın, eşleşmeme "Parola (tekrar)"ın altında; alana bağlı olmayan ret
// pencerenin genel uyarısıdır. İstek sürerken bütün alanlar kapalıdır ve pencere kilit
// ekranındaki gibi "Denetleniyor…" der (yanlış denemeden sonra yanıt gecikebilir).

import { useCallback, useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";

import Button from "../../ui/Button";
import Card from "../../ui/Card";
import Dialog from "../../ui/Dialog";
import Icon from "../../ui/Icon";
import { SkeletonList } from "../../ui/Skeleton";
import { useSnackbar } from "../../ui/SnackbarProvider";
import TextField from "../../ui/TextField";
import YeniParolaAlanlari from "../oturum/YeniParolaAlanlari";
import { oturumApi } from "../oturum/api";
import type { OturumHesabi } from "../oturum/api";
import { parolayiDegistir } from "../oturum/eylemler";
import { dogrulamaReddiMi, oturumHatasi } from "../oturum/hatalar";
import { yeniParolaHatalari } from "../oturum/parolaPolitikasi";
import { useKilitle } from "../oturum/useKilitle";
import BostaKilitSuresiKarti from "./BostaKilitSuresiKarti";
import { DENETLENIYOR_METNI } from "./KurtarmaIleAcma";
import KurtarmaAnahtariPaneli from "./KurtarmaAnahtariPaneli";
import KurtarmaAnahtariniDogrulaKarti from "./KurtarmaAnahtariniDogrulaKarti";
import KurtarmaAnahtariniYenileKarti from "./KurtarmaAnahtariniYenileKarti";
import KurtarmaCiktisiKarti from "./KurtarmaCiktisiKarti";
import SifreliYedekleme from "./SifreliYedekleme";
import YedektenGeriYukleme from "./YedektenGeriYukleme";
import { guvenlikApi } from "./api";
import type { GuvenlikDurumu } from "./api";
import {
  bekleyenKurtarmaAnahtariniYaz,
  useBekleyenKurtarmaAnahtari,
  useBekleyenKurtarmaKimligi,
} from "./bekleyenAnahtar";
import { guncelKurtarmaKimligi } from "./kurtarma";
import {
  DOGRULANMADI_BASLIGI,
  DOGRULANMADI_METNI,
  EN_ZAYIF_PAROLA_METNI,
  KAPSAM_DISI_METNI,
  KAPSAM_METNI,
  YARIM_GECIS_METNI,
} from "./metinler";

/** Kart başlıkları (docs/sozluk.md §4.6) — yol tarifi ve testler buradan okur. */
export const HESAP_KARTI_BASLIGI = "Hesap ve Parola";
export const SIFRELEME_KARTI_BASLIGI = "Şifreleme";

/** Kendi parolasını değiştiren hesabın snackbar'ı (hesap dili; sözlük §3). */
export const PAROLA_DEGISTI_ILETISI = "Parolanız değiştirildi.";

export default function GuvenlikAyarlari() {
  const snackbar = useSnackbar();
  const [durum, setDurum] = useState<GuvenlikDurumu | null>(null);
  // Oturumdaki hesabın kişisiz özeti (rol etiketi + tanıtıcı); okunamazsa satır yok.
  const [hesap, setHesap] = useState<OturumHesabi | null>(null);
  const [degistirAcik, setDegistirAcik] = useState(false);
  const mevcutParolaAlani = useRef<HTMLInputElement>(null);
  const yeniParolaAlani = useRef<HTMLInputElement>(null);
  const tekrarAlani = useRef<HTMLInputElement>(null);
  const [parola, setParola] = useState("");
  const [parolaTekrar, setParolaTekrar] = useState("");
  const [yeniParola, setYeniParola] = useState("");
  // Hatalar alan alan (dosya başı notu).
  const [mevcutHata, setMevcutHata] = useState<string | null>(null);
  const [yeniHata, setYeniHata] = useState<string | null>(null);
  const [tekrarHata, setTekrarHata] = useState<string | null>(null);
  const [genelHata, setGenelHata] = useState<string | null>(null);
  const [calisiyor, setCalisiyor] = useState(false);
  // Retten sonra odak hatalı alana; alanlar istek sürerken kapalıydı, odak yeniden
  // çizimden SONRA verilir.
  const [odak, setOdak] = useState<{ n: number; alan: "mevcut" | "yeni" | "tekrar" }>({
    n: 0,
    alan: "mevcut",
  });
  useEffect(() => {
    if (odak.n === 0) return;
    const alanlar = { mevcut: mevcutParolaAlani, yeni: yeniParolaAlani, tekrar: tekrarAlani };
    alanlar[odak.alan].current?.focus();
  }, [odak]);
  // Yenilenmiş (ya da sihirbazda gösterilmiş) ve henüz doğrulanmamış anahtar.
  const bekleyenAnahtar = useBekleyenKurtarmaAnahtari();
  const bekleyenKimlik = useBekleyenKurtarmaKimligi();
  const kilitle = useKilitle();

  const oku = useCallback(() => {
    guvenlikApi
      .durum()
      .then(setDurum)
      .catch(() => snackbar.error("Güvenlik durumu okunamadı."));
  }, [snackbar]);

  useEffect(() => oku(), [oku]);

  // Oturum özeti etkinliksiz okunur (yoklama gibi; ekranı açmak kullanıcı eylemi sayılmaz).
  useEffect(() => {
    let iptal = false;
    oturumApi
      .ozet(false)
      .then((ozet) => {
        if (!iptal) setHesap(ozet.durum === "acik" ? ozet.hesap : null);
      })
      .catch(() => undefined);
    return () => {
      iptal = true;
    };
  }, []);

  // Panel `true`yu sunucu damgayı yazınca bildirir: anahtar bellekten bırakılır.
  const yeniAnahtarDogrulandi = useCallback(
    (dogru: boolean) => {
      if (!dogru) return;
      bekleyenKurtarmaAnahtariniYaz(null);
      snackbar.success("Yeni kurtarma anahtarının saklandığı doğrulandı.");
      oku();
    },
    [oku, snackbar],
  );

  function hatalariSil() {
    setMevcutHata(null);
    setYeniHata(null);
    setTekrarHata(null);
    setGenelHata(null);
  }

  function kapat() {
    setDegistirAcik(false);
    setParola("");
    setParolaTekrar("");
    setYeniParola("");
    hatalariSil();
  }

  async function gonder(e: FormEvent) {
    e.preventDefault();
    hatalariSil();
    // Ön denetim backend'in kuralıyla birebir (otorite backend'dir): politika, eşleşme,
    // eskisiyle aynı olmama.
    const sorun = yeniParolaHatalari(yeniParola, parolaTekrar, parola);
    if (sorun.yeni || sorun.tekrar) {
      setYeniHata(sorun.yeni);
      setTekrarHata(sorun.tekrar);
      setOdak((o) => ({ n: o.n + 1, alan: sorun.yeni ? "yeni" : "tekrar" }));
      return;
    }
    setCalisiyor(true);
    try {
      await parolayiDegistir(parola, yeniParola);
      snackbar.success(PAROLA_DEGISTI_ILETISI);
      kapat();
      oku();
    } catch (err) {
      const { kod, metin } = oturumHatasi(err, "Parola değiştirilemedi.");
      if (kod === "parola_yanlis") {
        // Mevcut parola yanlış: o alanın hatasıdır; alan boşaltılır, odak oraya döner.
        setMevcutHata(metin);
        setParola("");
        setOdak((o) => ({ n: o.n + 1, alan: "mevcut" }));
      } else if (dogrulamaReddiMi(err)) {
        // Sunucu yeni parolayı reddetti (politika, eskisiyle aynı).
        setYeniHata(metin);
        setOdak((o) => ({ n: o.n + 1, alan: "yeni" }));
      } else {
        setGenelHata(metin);
      }
    } finally {
      setCalisiyor(false);
    }
  }

  if (durum === null) return <SkeletonList rows={2} />;

  return (
    <div className="flex flex-col gap-4">
      <Card className="p-6">
        {/* Kart başlığı SABİT bir addır (docs/sozluk.md §3, §4.6): kullanıcıya
            "Ayarlar → Güvenlik → Hesap ve Parola" diye yol tarif edilebilsin. Durum
            cümlesi başlığın altındadır. */}
        <div className="mb-2 flex items-center gap-3">
          <Icon name="account_circle" className="text-primary" />
          <h2 className="text-title-large text-on-surface">{HESAP_KARTI_BASLIGI}</h2>
        </div>

        {durum.password_set ? (
          <>
            {hesap && (
              <p className="text-body-medium text-on-surface">
                Bu oturum: <strong>{hesap.rol_etiketi}</strong> · tanıtıcı{" "}
                <span className="font-mono">{hesap.tanitici}</span>
              </p>
            )}
            <p className="mt-2 text-body-medium text-on-surface-variant">
              Herkes programı kendi hesabıyla ve kendi parolasıyla açar; parola paylaşılmaz.
              Parolanızı buradan değiştirirsiniz. Başka bir hesaba geçmek için Kilitle&apos;ye basıp
              kilit ekranında o hesabı seçin.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-2">
              <Button variant="tonal" icon="key" onClick={() => setDegistirAcik(true)}>
                Parolayı değiştir
              </Button>
              <Button variant="outlined" icon="lock" onClick={() => void kilitle()}>
                Kilitle
              </Button>
            </div>
          </>
        ) : (
          <>
            <p className="text-body-medium text-on-surface">Program yöneticisi hesabı kurulmadı.</p>
            <p className="mt-2 text-body-medium text-on-surface-variant">
              Program yöneticisi hesabı kurulum sihirbazının ilk adımında kurulur; kurtarma anahtarı
              da orada verilir.
            </p>
            <Link
              to="/kurulum"
              className="mt-4 inline-flex items-center gap-1.5 text-label-large font-medium text-primary underline-offset-4 hover:underline"
            >
              Kurulum Sihirbazı&apos;nı aç
              <Icon name="arrow_forward" size="sm" />
            </Link>
          </>
        )}
      </Card>

      {durum.password_set && <BostaKilitSuresiKarti />}

      <Card className="p-6">
        <div className="mb-2 flex items-center gap-3">
          <Icon name={durum.password_set ? "lock" : "lock_open"} className="text-primary" />
          <h2 className="text-title-large text-on-surface">{SIFRELEME_KARTI_BASLIGI}</h2>
        </div>

        <p className="text-body-medium text-on-surface">
          {durum.password_set
            ? "Kişisel veri alanları şifreli."
            : "Kişisel veri alanları, program yöneticisi hesabı kurulunca şifrelenir."}
        </p>
        <p className="mt-2 text-body-medium text-on-surface-variant">{KAPSAM_METNI}</p>
        <p className="mt-2 text-body-small text-on-surface-variant">{KAPSAM_DISI_METNI}</p>
        <p className="mt-2 text-body-small text-on-surface-variant">{EN_ZAYIF_PAROLA_METNI}</p>

        {durum.protected_fields.length > 0 && (
          <p className="mt-3 text-body-small text-on-surface-variant">
            <span className="text-label-large">Şifrelenen alanlar: </span>
            {durum.protected_fields.join(", ")}
          </p>
        )}

        {durum.transition_pending && (
          <p className="mt-3 rounded-shape-md bg-tertiary-container p-3 text-body-small text-on-tertiary-container">
            {YARIM_GECIS_METNI}
          </p>
        )}
      </Card>

      {durum.password_set && bekleyenAnahtar !== null && (
        <KurtarmaAnahtariPaneli
          anahtar={bekleyenAnahtar}
          kimlik={bekleyenKimlik}
          onDogrulama={yeniAnahtarDogrulandi}
          dogrulandiMetni="Doğrulandı."
        />
      )}

      {durum.password_set && bekleyenAnahtar === null && !durum.recovery_key_confirmed && (
        <>
          <div className="flex items-start gap-2 rounded-shape-sm bg-error-container px-4 py-3 text-body-medium text-on-error-container">
            <Icon name="key_off" size="lg" />
            <span>
              <strong>{DOGRULANMADI_BASLIGI}.</strong> {DOGRULANMADI_METNI}
            </span>
          </div>
          <KurtarmaAnahtariniDogrulaKarti onDogrulandi={setDurum} />
        </>
      )}

      {durum.password_set && bekleyenAnahtar === null && (
        <KurtarmaAnahtariniYenileKarti onYenilendi={oku} />
      )}

      {durum.password_set && <KurtarmaCiktisiKarti kimlik={guncelKurtarmaKimligi(durum)} />}

      <SifreliYedekleme parolaKurulu={durum.password_set} />

      <YedektenGeriYukleme />

      <Dialog
        open={degistirAcik}
        onClose={kapat}
        title="Parolayı değiştir"
        initialFocusRef={mevcutParolaAlani}
      >
        <form onSubmit={gonder} noValidate className="flex flex-col gap-4">
          <TextField
            ref={mevcutParolaAlani}
            label="Mevcut parola"
            type="password"
            value={parola}
            onChange={(e) => setParola(e.target.value)}
            autoComplete="current-password"
            error={mevcutHata ?? undefined}
            disabled={calisiyor}
            required
          />

          <YeniParolaAlanlari
            ref={yeniParolaAlani}
            tekrarRef={tekrarAlani}
            yeniParola={yeniParola}
            onYeniParola={setYeniParola}
            tekrar={parolaTekrar}
            onTekrar={setParolaTekrar}
            yeniHata={yeniHata}
            tekrarHata={tekrarHata}
            disabled={calisiyor}
          />

          {genelHata && (
            <p role="alert" className="text-body-medium text-error">
              {genelHata}
            </p>
          )}
          {calisiyor && (
            <p role="status" className="text-body-small text-on-surface-variant">
              {DENETLENIYOR_METNI}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="text" type="button" onClick={kapat}>
              Vazgeç
            </Button>
            <Button type="submit" disabled={calisiyor || !parola || !yeniParola || !parolaTekrar}>
              {calisiyor ? "Uygulanıyor…" : "Uygula"}
            </Button>
          </div>
        </form>
      </Dialog>
    </div>
  );
}
