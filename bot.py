"""
Schengen Vize Randevu Takip Botu v2
visasbot.com API kullanır — 403 hatası yok!
"""

import os
import time
import logging
import smtplib
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("vize-bot")

EMAIL_GONDEREN = os.environ.get("EMAIL_GONDEREN", "")
EMAIL_SIFRE    = os.environ.get("EMAIL_SIFRE", "")
EMAIL_ALICI    = os.environ.get("EMAIL_ALICI", "")
ARALIK_SANIYE  = int(os.environ.get("ARALIK_SANIYE", "60"))

VISA_API_URL = "https://api.visasbot.com/api/visa/list"
KAYNAK_ULKE  = "tur"

HEDEF_ULKELER = {
    "deu": "Almanya",
    "fra": "Fransa",
    "ita": "Italya",
    "esp": "Ispanya",
    "nld": "Hollanda",
    "dnk": "Danimarka",
    "bel": "Belcika",
    "che": "Isvicre",
    "aut": "Avusturya",
    "grc": "Yunanistan",
}

VIZE_TIPLERI = ["Tourism", "Tourist", "Short", "Turizm"]
bildirildi: set = set()
toplam_kontrol = 0


def api_kontrol() -> list:
    try:
        resp = requests.get(
            VISA_API_URL,
            params={"country_code": KAYNAK_ULKE},
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("data", [])
    except Exception as e:
        log.error(f"API hatasi: {e}")
        return []


def filtrele(randevular: list) -> list:
    bulunanlar = []
    for r in randevular:
        mission  = r.get("mission_code", "").lower()
        durum    = r.get("status", "").lower()
        vize_tip = r.get("visa_type", "")
        if mission not in HEDEF_ULKELER:
            continue
        if durum not in ("open", "waitlist_open"):
            continue
        if VIZE_TIPLERI:
            if not any(t.lower() in vize_tip.lower() for t in VIZE_TIPLERI):
                continue
        bulunanlar.append(r)
    return bulunanlar


def email_gonder(bulunanlar: list) -> None:
    if not EMAIL_GONDEREN or not EMAIL_SIFRE or not EMAIL_ALICI:
        log.warning("E-posta ayarlari eksik, atlandi.")
        return

    zaman = datetime.now().strftime("%d.%m.%Y %H:%M")
    satirlar = ""
    for r in bulunanlar:
        ulke_adi = HEDEF_ULKELER.get(r.get("mission_code", ""), r.get("mission_code", ""))
        merkez   = r.get("center", "-")
        son_tar  = r.get("last_appointment", "-")
        durum    = r.get("status", "-")
        vize_tip = r.get("visa_type", "-")
        durum_renk = "#00b894" if durum == "open" else "#f39c12"
        satirlar += f"""
        <tr>
          <td style="padding:12px 16px;font-weight:700">{ulke_adi}</td>
          <td style="padding:12px 16px;color:#555">{merkez}</td>
          <td style="padding:12px 16px">{vize_tip}</td>
          <td style="padding:12px 16px">
            <span style="background:{durum_renk};color:#fff;padding:3px 10px;
                         border-radius:20px;font-size:12px">{durum.upper()}</span>
          </td>
          <td style="padding:12px 16px;font-weight:600">{son_tar}</td>
        </tr>"""

    html = f"""<html><body style="font-family:Arial,sans-serif;background:#f5f6fa;padding:20px">
      <div style="max-width:680px;margin:0 auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.1)">
        <div style="background:linear-gradient(135deg,#0984e3,#00cec9);padding:32px">
          <div style="font-size:40px">&#x1F6A8;</div>
          <h1 style="color:#fff;margin:8px 0 0">Schengen Vize Randevusu Acildi!</h1>
          <p style="color:rgba(255,255,255,0.85);margin:8px 0 0">{zaman}</p>
        </div>
        <div style="padding:28px 32px">
          <p style="color:#444">Asagidaki randevular musait durumda. <strong>Hemen randevu alin!</strong></p>
          <table style="width:100%;border-collapse:collapse">
            <thead><tr style="background:#f8f9fa;border-bottom:2px solid #eee">
              <th style="padding:10px 16px;text-align:left;color:#888;font-size:11px">ULKE</th>
              <th style="padding:10px 16px;text-align:left;color:#888;font-size:11px">MERKEZ</th>
              <th style="padding:10px 16px;text-align:left;color:#888;font-size:11px">VIZE TIPI</th>
              <th style="padding:10px 16px;text-align:left;color:#888;font-size:11px">DURUM</th>
              <th style="padding:10px 16px;text-align:left;color:#888;font-size:11px">SON TARIH</th>
            </tr></thead>
            <tbody>{satirlar}</tbody>
          </table>
          <div style="margin-top:28px;text-align:center">
            <a href="https://idata.com.tr" style="background:#00b894;color:#fff;padding:14px 40px;border-radius:100px;text-decoration:none;font-weight:700">
              iDATA Randevu Al
            </a>
          </div>
          <p style="color:#b2bec3;font-size:11px;margin-top:24px;text-align:center">
            Her {ARALIK_SANIYE} saniyede bir otomatik kontrol yapilmaktadir.
          </p>
        </div>
      </div>
    </body></html>"""

    ulke_listesi = ", ".join(HEDEF_ULKELER.get(r.get("mission_code",""),"") for r in bulunanlar)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Vize Randevusu Acildi: {ulke_listesi}"
    msg["From"]    = EMAIL_GONDEREN
    msg["To"]      = EMAIL_ALICI
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_GONDEREN, EMAIL_SIFRE)
            smtp.send_message(msg)
        log.info(f"E-posta gonderildi: {EMAIL_ALICI}")
    except Exception as e:
        log.error(f"E-posta gonderilemedi: {e}")


def main() -> None:
    global toplam_kontrol
    log.info("=" * 55)
    log.info("  Schengen Vize Randevu Takip Botu v2")
    log.info(f"  API: {VISA_API_URL}")
    log.info(f"  Aralik: {ARALIK_SANIYE}sn | E-posta: {EMAIL_ALICI or '(ayarlanmamis)'}")
    log.info("=" * 55)

    while True:
        toplam_kontrol += 1
        log.info(f"Kontrol #{toplam_kontrol}")
        randevular = api_kontrol()

        if not randevular:
            log.warning("  API bos dondu veya hata.")
        else:
            bulunanlar = filtrele(randevular)
            if bulunanlar:
                yeni = []
                for r in bulunanlar:
                    rid = f"{r.get('mission_code')}_{r.get('center')}_{r.get('visa_type')}"
                    ulke = HEDEF_ULKELER.get(r.get("mission_code", ""), "?")
                    log.info(f"  BULUNDU: {ulke} | {r.get('center')} | {r.get('last_appointment')}")
                    if rid not in bildirildi:
                        bildirildi.add(rid)
                        yeni.append(r)
                if yeni:
                    email_gonder(yeni)
            else:
                log.info(f"  Acik randevu yok. (API {len(randevular)} kayit dondurdu)")

        log.info(f"  {ARALIK_SANIYE}sn bekleniyor...\n")
        time.sleep(ARALIK_SANIYE)


if __name__ == "__main__":
    main()
