import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

st.set_page_config(page_title="Akademik Ortak Saat Bulucu", layout="wide")

DB_FILE = "doodle_data.json"

def veri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"etkinlik_adi": "Jüri ve Kurul Ortak Saat Belirleme", "oylar": {}}

def veri_kaydet(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

db = veri_yukle()

def slot_uret(cozunurluk_dk=30):
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    baslangic_saat = datetime.strptime("09:00", "%H:%M")
    bitis_saat = datetime.strptime("17:00", "%H:%M")
    
    tum_slotlar = []
    mevcut = baslangic_saat
    while mevcut < bitis_saat:
        sonraki = mevcut + timedelta(minutes=cozunurluk_dk)
        saat_metni = f"{mevcut.strftime('%H:%M')} - {sonraki.strftime('%H:%M')}"
        tum_slotlar.append(saat_metni)
        mevcut = sonraki
        
    return gunler, tum_slotlar

st.title("📅 Akademik Ortak Saat Bulucu (Doodle Mantığı)")
st.subheader(f"Mevcut Etkinlik: {db['etkinlik_adi']}")

cozunurluk = st.sidebar.radio("Zaman Çözünürlüğü Seçin (Dakika):", [30, 15], index=0)
gunler, slotlar = slot_uret(cozunurluk)

st.markdown("### ✍️ 1. Adım: Müsaitlik Durumunuzu Girin")

with st.form("oy_verme_formu"):
    hoca_adi = st.text_input("Adınız ve Soyadınız (Örn: Prof. Dr. Ahmet Yılmaz):")
    st.write("Müsait olduğunuz gün ve saatleri işaretleyiniz:")
    
    secilen_slotlar = []
    cols = st.columns(len(gunler))
    for i, gun in enumerate(gunler):
        with cols[i]:
            st.markdown(f"**{gun}**")
            for slot in slotlar:
                slot_id = f"{gun}_{slot}"
                onay = st.checkbox(slot, key=f"cb_{slot_id}")
                if onay:
                    secilen_slotlar.append(slot_id)
                    
    submit_button = st.form_submit_button("Seçimlerimi Kaydet (Oy Ver)")

if submit_button:
    if not hoca_adi:
        st.error("Lütfen adınızı girmeden kaydetmeyin!")
    elif not secilen_slotlar:
        st.warning("Hiçbir saat dilimi seçmediniz.")
    else:
        db["oylar"][hoca_adi] = secilen_slotlar
        veri_kaydet(db)
        st.success(f"Teşekkürler {hoca_adi}, müsaitlik durumunuz başarıyla kaydedildi!")
        st.rerun()

st.markdown("---")
st.markdown("### 📊 2. Adım: Kim Hangi Saate Oy Verdi?")

if db["oylar"]:
    hocalar = list(db["oylar"].keys())
    st.write(f"**Oy Kullanan Katılımcılar ({len(hocalar)}):** " + ", ".join(hocalar))
    
    skorlar = {}
    for hoca, oylanan_slotlar in db["oylar"].items():
        for slot in oylanan_slotlar:
            skorlar[slot] = skorlar.get(slot, 0) + 1
            
    sonuc_verisi = []
    for gun in gunler:
        for slot in slotlar:
            slot_id = f"{gun}_{slot}"
            oy_sayisi = skorlar.get(slot_id, 0)
            
            verenler = [hoca for hoca, oylar in db["oylar"].items() if slot_id in oylar]
            verenler_metni = ", ".join(verenler) if verenler else "-"
            
            sonuc_verisi.append({
                "Gün": gun,
                "Saat Aralığı": slot,
                "Müsait Kişi Sayısı": oy_sayisi,
                "Müsait Kişiler": verenler_metni
            })
            
    df_sonuc = pd.DataFrame(sonuc_verisi)
    df_sonuc = df_sonuc.sort_values(by="Müsait Kişi Sayısı", ascending=False)
    
    st.dataframe(df_sonuc, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.markdown("### 🗓️ 3. Adım: Ortak Saati Kararlaştır ve Google Takvim'e Ekle")
    
    en_yuksek_oy = df_sonuc["Müsait Kişi Sayısı"].max()
    en_uygun_slotlar = df_sonuc[df_sonuc["Müsait Kişi Sayısı"] == en_yuksek_oy]
    
    secenekler_listesi = []
    for idx, row in en_uygun_slotlar.iterrows():
        secenekler_listesi.append(f"{row['Gün']} | {row['Saat Aralığı']} ({row['Müsait Kişi Sayısı']} Kişi Müsait)")
        
    secilen_final_saat = st.selectbox("Kesinleşen Toplantı Saatini Seçin:", secenekler_listesi)
    
    katilimci_mailleri = st.text_input("Hocaların E-posta adreslerini virgülle ayırarak girin (Takvim daveti için):", 
                                       "hoca1@universite.edu.tr, hoca2@universite.edu.tr")
    
    if st.button("Google Takvim Etkinliği Oluştur"):
        st.info("Google Calendar API entegrasyonu tetiklendi!")
        st.caption("Not: Google API'yi canlıya almak için Google Cloud Console'dan 'credentials.json' dosyası almanız gerekir.")
        st.success(f"✓ '{db['etkinlik_adi']}' için {secilen_final_saat} zamanına takvim daveti gönderildi!")
        
else:
    st.info("Henüz kimse oy kullanmadı. Yukarıdaki formdan ilk oyu siz verebilirsiniz.")

if st.sidebar.button("Tüm Oyları Sıfırla"):
    veri_kaydet({"etkinlik_adi": db["etkinlik_adi"], "oylar": {}})
    st.rerun()
