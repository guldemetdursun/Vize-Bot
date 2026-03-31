# 🚀 Railway Deployment Rehberi
## Schengen Vize Randevu Takip Botu

---

## 1. Gmail App Password Oluştur (5 dakika)

1. Gmail'e giriş yap → **Google Hesabım** → **Güvenlik**
2. **2 Adımlı Doğrulama**'yı aç (zorunlu)
3. Arama çubuğuna "Uygulama şifreleri" yaz → gir
4. Uygulama: **Posta** / Cihaz: **Diğer** → `Vize Bot` yaz → **Oluştur**
5. Çıkan **16 haneli şifreyi** kopyala (boşluksuz)

---

## 2. GitHub'a Yükle (3 dakika)

```bash
# Terminalde bu klasörde çalıştır:
git init
git add .
git commit -m "vize bot"

# GitHub'da yeni repo oluştur, sonra:
git remote add origin https://github.com/KULLANICI_ADIN/vize-bot.git
git push -u origin main
```

**GitHub hesabın yoksa:** https://github.com/signup adresinden ücretsiz aç.

---

## 3. Railway'e Deploy Et (5 dakika)

1. **https://railway.app** → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Repo listesinden `vize-bot`'u seç → **Deploy Now**

---

## 4. Environment Variables Ayarla

Railway dashboard'da projeye gir → **Variables** sekmesi → şunları ekle:

| Değişken | Değer |
|---|---|
| `EMAIL_GONDEREN` | senin@gmail.com |
| `EMAIL_SIFRE` | 16hanelishifre (boşluksuz) |
| `EMAIL_ALICI` | senin@gmail.com |
| `ARALIK_SANIYE` | 45 |

Kaydet → Railway otomatik yeniden başlatır.

---

## 5. Kontrol Et

- **Logs** sekmesine tık → canlı logları izle
- Şunu görüyorsan bot çalışıyor demektir:
  ```
  Schengen Vize Randevu Takip Botu — Başlatıldı
  ⏳  Almanya     → Randevu yok
  ⏳  Fransa      → Randevu yok
  ...
  💤 45 saniye bekleniyor...
  ```

---

## 💰 Maliyet

Railway **ücretsiz planı** aylık **500 saat** veriyor.  
Bu bot ayda ~720 saat çalışır → **küçük bir ücret çıkabilir** (~1-2$).  
Ücretsiz kalmak için **Render.com** alternatifini kullanabilirsin (aşağıda).

### Render Alternatifi (Tamamen Ücretsiz)
1. https://render.com → New → **Background Worker**
2. GitHub reposunu bağla
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Environment variables'ı aynı şekilde ekle

> ⚠️ Render ücretsiz planda 15 dakika işlem yoksa uyuyor.  
> Bot sürekli çalıştığı için bu sorun olmaz.

---

## ❓ Sık Sorulan Sorular

**Bot iDATA sitesini bulamadı derse?**  
iDATA URL yapısı değişmiş olabilir. `bot.py` içindeki `ULKELER` sözlüğündeki URL'leri güncelle.

**E-posta gelmiyor?**  
Gmail App Password'u doğru girdiğinden emin ol. Normal şifre çalışmaz.

**Bot çok sık kontrol ederse ban yer miyim?**  
45 saniye aralık güvenli. 30 saniyenin altına düşürme.
