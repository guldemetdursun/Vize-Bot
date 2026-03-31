"""
Schengen Vize Randevu Takip Botu
iDATA / VFS Global - Türkiye
7/24 Railway Sunucusu
"""

import os
import time
import logging
import smtplib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("vize-bot")

# ─── Ayarlar (Railway Environment Variables) ────────────────────────────────
EMAIL_GONDEREN  = os.environ.get("EMAIL_GONDEREN", "")
EMAIL_SIFRE     = os.environ.get("EMAIL_SIFRE", "")      # Gmail App Password
EMAIL_ALICI     = os.environ.get("EMAIL_ALICI", "")
ARALIK_SANIYE   = int(os.environ.get("ARALIK_SANIYE", "45"))

# ─── Takip Edilecek Ülkeler ─────────────────────────────────────────────────
ULKELER = {
    "Almanya":    "https://www.idata.com.tr/tr/almanya/",
    "Fransa":     "https://www.idata.com.tr/tr/fransa/",
    "İtalya":     "https://www.idata.com.tr/tr/italya/",
    "İspanya":    "https://www.idata.com.tr/tr/ispanya/",
    "Hollanda":   "https://www.idata.com.tr/tr/hollanda/",
    "Danimarka":  "https://www.idata.com.tr/tr/danimarka/",
    "Belçika":    "https://www.idata.com.tr/tr/belcika/",
    "İsviçre":    "https://www.idata.com.tr/tr/isvicre/",
    "Avusturya":  "https://www.idata.com.tr/tr/avusturya/",
    "Yunanistan": "https://www.idata.com.tr/tr/yunanistan/",
}

# Randevu YOK olduğunu belirten ifadeler (küçük harf)
YOK_IFADELER = [
    "randevu bulunmamaktadır",
    "müsait randevu yok",
    "şu an randevu",
    "no appointment available",
    "no slots available",
    "appointment not available",
    "randevu alınamıyor",
]

# Randevu VAR olduğunu belirten ifadeler
VAR_IFADELER = [
    "randevu al",
    "appointment",
    "tarih seç",
    "uygun tarih",
    "müsait",
    "book appointment",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── Durum takibi (aynı ülke için tekrar e-posta spam'i önler) ─────────────
son_durum: dict[str, bool] = {ulke: False for ulke in ULKELER}
toplam_kontrol = 0
bulunan_toplam = 0


# ─── Sayfa Kontrolü ─────────────────────────────────────────────────────────
def kontrol_et(ulke: str, url: str) -> tuple[bool, str]:
    """Sayfayı çek, randevu var mı yok mu analiz et."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        return False, f"Bağlantı hatası: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    metin = soup.get_text(separator=" ").lower()

    # Önce "yok" ifadelerini ara
    for ifade in YOK_IFADELER:
        if ifade in metin:
            return False, "Randevu yok"

    # Sonra "var" ifadelerini ara
    for ifade in VAR_IFADELER:
        if ifade in metin:
            return True, f"Randevu mevcut olabilir! ({ifade})"

    # Belirsiz durum — ihtiyatlı davran
    return False, "Belirsiz sayfa içeriği"


# ─── E-posta ────────────────────────────────────────────────────────────────
def email_gonder(bulunan_ulkeler: list[tuple[str, str, str]]) -> None:
    if not EMAIL_GONDEREN or not EMAIL_SIFRE or not EMAIL_ALICI:
        log.warning("E-posta ayarları eksik, bildirim atlandı.")
        return

    zaman = datetime.now().strftime("%d.%m.%Y %H:%M")

    satirlar = "".join(
        f"""
        <tr>
          <td style="padding:10px 16px;font-weight:600;color:#1a1a2e">{u}</td>
          <td style="padding:10px 16px;color:#555">{m}</td>
          <td style="padding:10px 16px">
            <a href="{link}" style="background:#00b894;color:#fff;padding:6px 14px;
               border-radius:6px;text-decoration:none;font-size:13px">
              Randevu Al →
            </a>
          </td>
        </tr>
        """
        for u, m, link in bulunan_ulkeler
    )

    html = f"""
    <html><body style="font-family:'Segoe UI',sans-serif;background:#f5f6fa;margin:0;padding:20px">
      <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;
                  box-shadow:0 4px 20px rgba(0,0,0,0.1);overflow:hidden">
        <div style="background:linear-gradient(135deg,#0984e3,#00cec9);padding:28px 32px">
          <h1 style="color:#fff;margin:0;font-size:22px">🚨 Schengen Vize Randevusu Açıldı!</h1>
          <p style="color:rgba(255,255,255,0.85);margin:8px 0 0">{zaman}</p>
        </div>
        <div style="padding:24px 32px">
          <p style="color:#444;margin:0 0 20px">
            Aşağıdaki ülkelerde iDATA/VFS Global üzerinde randevu müsaitliği tespit edildi.
            Hemen kontrol et!
          </p>
          <table style="width:100%;border-collapse:collapse;border:1px solid #eee;border-radius:8px;overflow:hidden">
            <thead>
              <tr style="background:#f8f9fa">
                <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;
                           text-transform:uppercase;letter-spacing:1px">Ülke</th>
                <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;
                           text-transform:uppercase;letter-spacing:1px">Durum</th>
                <th style="padding:10px 16px;text-align:left;font-size:12px;color:#888;
                           text-transform:uppercase;letter-spacing:1px">İşlem</th>
              </tr>
            </thead>
            <tbody>{satirlar}</tbody>
          </table>
          <p style="color:#999;font-size:12px;margin-top:20px">
            Bu mesaj otomatik olarak Schengen Vize Takip Botu tarafından gönderilmiştir.<br>
            Bot her {ARALIK_SANIYE} saniyede bir kontrol yapmaktadır.
          </p>
        </div>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 Vize Randevusu Açıldı — {', '.join(u for u,_,_ in bulunan_ulkeler)}"
    msg["From"]    = EMAIL_GONDEREN
    msg["To"]      = EMAIL_ALICI
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_GONDEREN, EMAIL_SIFRE)
            smtp.send_message(msg)
        log.info(f"✅ E-posta gönderildi → {EMAIL_ALICI}")
    except Exception as e:
        log.error(f"E-posta gönderilemedi: {e}")


# ─── Ana Döngü ───────────────────────────────────────────────────────────────
def main() -> None:
    global toplam_kontrol, bulunan_toplam

    log.info("=" * 60)
    log.info("  Schengen Vize Randevu Takip Botu — Başlatıldı")
    log.info(f"  Takip edilen ülkeler : {', '.join(ULKELER.keys())}")
    log.info(f"  Kontrol aralığı      : {ARALIK_SANIYE} saniye")
    log.info(f"  Bildirim e-postası   : {EMAIL_ALICI or '(ayarlanmamış)'}")
    log.info("=" * 60)

    while True:
        toplam_kontrol += 1
        log.info(f"── Kontrol #{toplam_kontrol} başlıyor ──")

        bulunan_bu_tur: list[tuple[str, str, str]] = []

        for ulke, url in ULKELER.items():
            bulundu, mesaj = kontrol_et(ulke, url)

            if bulundu:
                log.info(f"  ✅  {ulke:12s} → {mesaj}")
                bulunan_bu_tur.append((ulke, mesaj, url))
                # Sadece durumu yeni değiştiyse say
                if not son_durum[ulke]:
                    bulunan_toplam += 1
                son_durum[ulke] = True
            else:
                log.info(f"  ⏳  {ulke:12s} → {mesaj}")
                son_durum[ulke] = False

            time.sleep(2)  # Her ülke arasında kısa bekleme (rate limiting)

        # Yeni randevu bulunduysa e-posta gönder
        yeni_bulunanlar = [
            (u, m, l) for (u, m, l) in bulunan_bu_tur
            if son_durum[u]
        ]
        if yeni_bulunanlar:
            log.info(f"📧 {len(yeni_bulunanlar)} ülke için e-posta bildirimi gönderiliyor...")
            email_gonder(yeni_bulunanlar)
        else:
            log.info(f"  → Randevu bulunamadı. Toplam kontrol: {toplam_kontrol}")

        log.info(f"  💤 {ARALIK_SANIYE} saniye bekleniyor...\n")
        time.sleep(ARALIK_SANIYE)


if __name__ == "__main__":
    main()
