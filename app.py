import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import urllib.parse

# Sayfa Yapısı ve Başlık Ayarı
st.set_page_config(page_title="Slotify - Find the Perfect Meeting Time", layout="centered")

# Google Apps Script Bağlantısı
@st.cache_data(ttl=1)
def verileri_getir():
    try:
        url = st.secrets["connections"]["macro_url"]
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi", "Organizasyon_ID"])
    except:
        return pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi", "Organizasyon_ID"])

def veriyi_gonder(yeni_satirlar):
    try:
        url = st.secrets["connections"]["macro_url"]
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(yeni_satirlar), headers=headers)
        return response.status_code == 200
    except:
        return False

raw_data = verileri_getir()
if not raw_data.empty:
    raw_data.columns = [c.strip() for c in raw_data.columns]
else:
    raw_data = pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi", "Organizasyon_ID"])

# Haftalık Takvim Üretici
def slot_uret(baslangic_tarih_obj):
    hafta_basi = baslangic_tarih_obj - timedelta(days=baslangic_tarih_obj.weekday())
    gunler_tarihli = []
    gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    
    for i in range(5):
        tarih = hafta_basi + timedelta(days=i)
        gunler_tarihli.append(f"{tarih.strftime('%d.%m.%Y')} {gun_isimleri[i]}")
    
    slotlar = ["09:00 - 09:30", "09:30 - 10:00", "10:00 - 10:30", "10:30 - 11:00", 
               "11:00 - 11:30", "11:30 - 12:00", "12:00 - 12:30", "12:30 - 13:00",
               "13:00 - 13:30", "13:30 - 14:00", "14:00 - 14:30", "14:30 - 15:00",
               "15:00 - 15:30", "15:30 - 16:00", "16:00 - 16:30", "16:30 - 17:00"]
    return gunler_tarihli, slotlar

# URL Parametre Kontrolü
parametreler = st.query_params
secilen_anket = parametreler.get("anket_id", None)

if secilen_anket is None:
    # -------------------------------------------------------------------------
    # 🔮 EKRAN 1: ANKET OLUŞTURMA SAYFASI (CREATE POLL)
    # -------------------------------------------------------------------------
    st.title("🔮 Slotify")
    st.subheader("Create a group meeting poll")
    
    # BLOK 1: Detaylar
    with st.container(border=True):
        st.markdown("### 📝 Poll Details")
        org_adi = st.text_input("Title", placeholder="What's the occasion? (e.g. Project Sync, Team Dinner, Jury)")
        aciklama = st.text_area("Description (optional)", placeholder="Add context, instructions, or an agenda for your participants.")
        lokasyon = st.text_input("Location (optional)", placeholder="Where will this happen? (e.g. Meeting Room 3, Cafe, Online)")
        video_konferans = st.selectbox("Video conferencing", ["Off", "Google Meet", "Zoom", "Microsoft Teams"])

    # BLOK 2: Zaman Seçimi
    with st.container(border=True):
        st.markdown("### 📅 Choose the target week")
        st.info("⏱️ Duration: 30 min per time slot")
        planlanacak_hafta = st.date_input("Select Week (Pick any day of the target week)", datetime.now())

    # BLOK 3: Özelleştirmeler
    with st.container(border=True):
        st.markdown("### ⚙️ Premium Features")
        st.checkbox("Add custom branding and logo", value=False, disabled=True, help="Upgrade to Slotify Pro")
        st.checkbox("Remove Ads (100% Ad-Free Experience)", value=True, disabled=True)
        st.checkbox("Send automatic reminders to missing participants", value=True, disabled=True)

    st.write("") 
    
    # Oluşturma Butonu
    if st.button("Create poll and generate link", type="primary", use_container_width=True):
        if org_adi:
            temiz_id = urllib.parse.quote(org_adi.strip())
            tarih_str = planlanacak_hafta.strftime("%d.%m.%Y")
            anket_kod = f"{temiz_id}_{tarih_str}"
            
            ana_url = "https://doodle-projesi-ekrapj7pb5hsifyvauhpmv.streamlit.app"
            ozel_doodle_linki = f"{ana_url}/?anket_id={anket_kod}"
            
            st.success("🎉 Meeting poll successfully created on Slotify!")
            st.markdown("#### 🔗 Share this invite link with your group:")
            st.code(ozel_doodle_linki, language="text")
        else:
            st.error("Please enter a Title for your meeting poll!")

else:
    # -------------------------------------------------------------------------
    # 👥 EKRAN 2: KATILIMCILARIN GÖRDÜĞÜ SEÇİM MATRİSİ
    # -------------------------------------------------------------------------
    gorunur_ad = urllib.parse.unquote(secilen_anket)
    try:
        tarih_parcasi = gorunur_ad.split("_")[-1]
        tarih_obj = datetime.strptime(tarih_parcasi, "%d.%m.%Y")
    except:
        tarih_obj = datetime.now()
        
    temiz_baslik = gorunur_ad.replace(f"_{tarih_obj.strftime('%d.%m.%Y')}", "")
    
    st.title(f"📅 {temiz_baslik}")
    
    # Dinamik Hafta Aralığı Hesaplama (Pazartesi - Cuma)
    hafta_basi = tarih_obj - timedelta(days=tarih_obj.weekday())
    hafta_sonu = hafta_basi + timedelta(days=4)
    
    # Net Tarih ve Hafta Bilgilendirme Kutusu
    st.info(f"📆 **Poll Target Week:** {hafta_basi.strftime('%d.%m.%Y')} to {hafta_sonu.strftime('%d.%m.%Y')}")
    
    org_data = raw_data[raw_data["Organizasyon_ID"] == secilen_anket] if not raw_data.empty else pd.DataFrame()
    
    oylar_havuzu = {}
    if not org_data.empty:
        for _, row in org_data.iterrows():
            hoca = str(row.get("Katilimci", ""))
            slot = str(row.get("Secilen_Slot", ""))
            if hoca and slot and hoca != "nan" and slot != "nan":
                if hoca not in oylar_havuzu: oylar_havuzu[hoca] = []
                if slot not in oylar_havuzu[hoca]: oylar_havuzu[hoca].append(slot)
                    
    gunler, slotlar = slot_uret(tarih_obj)
    
    with st.form("hoca_formu", clear_on_submit=True):
        st.markdown("### ✍️ Choose your availability")
        hoca_adi = st.text_input("Your Name / Adınız Soyadınız", placeholder="e.g. John Doe / Ahmet Yılmaz")
        st.markdown("---")
        
        secilen_slotlar = []
        cols = st.columns(len(gunler))
        
        for i, gun in enumerate(gunler):
            with cols[i]:
                tarih_kismi = gun.split(" ")[0]
                gun_adi = gun.split(" ")[1].upper()
                
                # Sütun başlıklarında net gün.ay.yıl ve Gün Adı
                st.markdown(f"**{gun_adi}**\n`{tarih_kismi}`")
                
                for slot in slotlar:
                    slot_id = f"{gun}_{slot}"
                    saat_gosterim = slot.split(" - ")[0]
                    if st.checkbox(saat_gosterim, key=f"chk_{slot_id}"):
                        secilen_slotlar.append(slot_id)
                        
        st.write("") 
        submit = st.form_submit_button("Submit your availability", type="primary", use_container_width=True)
        
    if submit:
        if not hoca_adi:
            st.error("Please enter your name!")
        elif not secilen_slotlar:
            st.warning("Please select at least one time slot.")
        else:
            yeni_satirlar = []
            zaman_damgasi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for slot in secilen_slotlar:
                yeni_satirlar.append({
                    "Katilimci": hoca_adi,
                    "Secilen_Slot": slot,
                    "Zaman_Damgasi": zaman_damgasi,
                    "Organizasyon_ID": secilen_anket
                })
                
            if veriyi_gonder(yeni_satirlar):
                st.success("Availability successfully submitted!")
                st.cache_data.clear()
                st.rerun()
                    
    # SONUÇLAR (SKOR TABLOSU)
    st.write("") 
    st.markdown("### 📊 Live Results (Most suitable slots on top)")
    
    if oylar_havuzu:
        hocalar = list(oylar_havuzu.keys())
        st.write(f"**Who responded ({len(hocalar)}):** " + ", ".join(hocalar))
        
        skorlar = {}
        for hoca, oylanan_slotlar in oylar_havuzu.items():
            for slot in oylanan_slotlar:
                skorlar[slot] = skorlar.get(slot, 0) + 1
                
        sonuc_verisi = []
        for gun in gunler:
            for slot in slotlar:
                slot_id = f"{gun}_{slot}"
                oy_sayisi = skorlar.get(slot_id, 0)
                verenler = [hoca for hoca, oylar in oylar_havuzu.items() if slot_id in oylar]
                verenler_metni = ", ".join(verenler) if verenler else "-"
                
                sonuc_verisi.append({
                    "Day / Date": gun,
                    "Time Slot": slot,
                    "Votes": oy_sayisi,
                    "Available People": verenler_metni
                })
                
        df_sonuc = pd.DataFrame(sonuc_verisi)
        df_sonuc = df_sonuc.sort_values(by="Votes", ascending=False)
        st.dataframe(df_sonuc, use_container_width=True, hide_index=True)
    else:
        st.info("No responses yet. Be the first to share your availability!")
        
    if st.button("⬅️ Create a new poll"):
        st.query_params.clear()
        st.rerun()
