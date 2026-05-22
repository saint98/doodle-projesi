import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import urllib.parse

# Sayfa Yapısı ve Genişlik Ayarları (Doodle Tasarımı İçin Ortalanmış)
st.set_page_config(page_title="Create a poll - Doodle", layout="centered", initial_sidebar_state="collapsed")

# Doodle Tasarımı İçin CSS Temizliği (Hatasız Tek Satır Formatında)
st.markdown("<style>.main { background-color: #f8f9fa; } .doodle-card { background-color: white; padding: 30px; border-radius: 8px; border: 1px solid #e3e6e8; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); } .doodle-section-title { font-size: 22px; font-weight: 600; color: #1a1a1a; margin-bottom: 15px; } div.stButton > button:first-child { background-color: #0066cc; color: white; border-radius: 4px; font-weight: bold; border: none; padding: 0.6rem 2rem; } div.stButton > button:first-child:hover { background-color: #0052a3; }</style>", unsafe_allowed_html=True)

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

parametreler = st.query_params
secilen_anket = parametreler.get("anket_id", None)

if secilen_anket is None:
    # -------------------------------------------------------------------------
    # 🧡 EKRAN 1: ANKET OLUŞTURMA SAYFASI (CREATE GROUP POLL)
    # -------------------------------------------------------------------------
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/s/s7/Doodle_Logo.svg/512px-Doodle_Logo.svg.png", width=120)
    st.markdown("<br>", unsafe_allowed_html=True)

    # BLOK 1: Detaylar
    st.markdown('<div class="doodle-card">', unsafe_allowed_html=True)
    st.markdown('<div class="doodle-section-title">Create group poll</div>', unsafe_allowed_html=True)
    org_adi = st.text_input("Title", placeholder="What's the occasion?")
    aciklama = st.text_area("Description (optional)", placeholder="Here you can include things like an agenda, instructions, or other details.")
    lokasyon = st.text_input("Location (optional)", placeholder="Where will this happen?")
    video_konferans = st.selectbox("Video conferencing", ["Off", "Google Meet", "Zoom", "Microsoft Teams"])
    st.markdown('</div>', unsafe_allowed_html=True)

    # BLOK 2: Zaman Seçimi
    st.markdown('<div class="doodle-card">', unsafe_allowed_html=True)
    st.markdown('<div class="doodle-section-title">Add your times</div>', unsafe_allowed_html=True)
    st.write("⏱️ Duration: **30 min** (Akademik Standart)")
    planlanacak_hafta = st.date_input("Select Week (Planlanacak Haftadan Bir Gün Seçin)", datetime.now())
    st.markdown('</div>', unsafe_allowed_html=True)

    # BLOK 3: Özelleştirmeler
    st.markdown('<div class="doodle-card">', unsafe_allowed_html=True)
    st.markdown('<div class="doodle-section-title">Customize your poll ✨</div>', unsafe_allowed_html=True)
    st.checkbox("Add your logo and brand colors", disabled=True, help="Pro Özelliği")
    st.checkbox("Remove Ads (Reklamları Kaldır)", value=True, disabled=True)
    st.checkbox("Send automatic reminders (Otomatik hatırlatıcılar aktif)", value=True, disabled=True)
    st.markdown('</div>', unsafe_allowed_html=True)

    # Buton
    if st.button("Create poll and generate link"):
        if org_adi:
            temiz_id = urllib.parse.quote(org_adi.strip())
            tarih_str = planlanacak_hafta.strftime("%d.%m.%Y")
            anket_kod = f"{temiz_id}_{tarih_str}"
            
            ana_url = "https://doodle-projesi-ekrapj7pb5hsifyvauhpmv.streamlit.app"
            ozel_doodle_linki = f"{ana_url}/?anket_id={anket_kod}"
            
            st.success("🎉 Poll created successfully!")
            st.markdown("### 🔗 Share this link with your participants:")
            st.code(ozel_doodle_linki, language="text")
        else:
            st.error("Please enter a Title for your poll!")

else:
    # -------------------------------------------------------------------------
    # 👨‍🏫 EKRAN 2: HOCALARIN GÖRDÜĞÜ ANKET KATILIM MATRİSİ
    # -------------------------------------------------------------------------
    gorunur_ad = urllib.parse.unquote(secilen_anket)
    try:
        tarih_parcasi = gorunur_ad.split("_")[-1]
        tarih_obj = datetime.strptime(tarih_parcasi, "%d.%m.%Y")
    except:
        tarih_obj = datetime.now()
        
    temiz_baslik = gorunur_ad.replace(f"_{tarih_obj.strftime('%d.%m.%Y')}", "")
    
    st.markdown(f'<div class="doodle-card" style="border-left: 5px solid #0066cc;"><h2>📅 {temiz_baslik}</h2><p style="color:#65696b;">Haftalık Seçim Matrisi / Başlangıç: {tarih_obj.strftime("%d.%m.%Y")}</p></div>', unsafe_allowed_html=True)
    
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
    
    st.markdown('<div class="doodle-card">', unsafe_allowed_html=True)
    st.markdown('<div class="doodle-section-title">✍️ Choose your availability</div>', unsafe_allowed_html=True)
    
    with st.form("hoca_formu"):
        hoca_adi = st.text_input("Your name", placeholder="e.g. Prof. Dr. Ahmet Yılmaz")
        st.markdown("<hr>", unsafe_allowed_html=True)
        
        secilen_slotlar = []
        cols = st.columns(len(gunler))
        
        for i, gun in enumerate(gunler):
            with cols[i]:
                gun_tarih = gun.split(" ")[0].split(".")[0]
                gun_adi = gun.split(" ")[1][:3].upper()
                st.markdown(f"<div style='text-align:center; background:#f1f3f5; padding:5px; font-weight:bold; border-radius:4px; margin-bottom:10px;'>{gun_adi}\n{gun_tarih}</div>", unsafe_allowed_html=True)
                
                for slot in slotlar:
                    slot_id = f"{gun}_{slot}"
                    if st.checkbox(slot.split(" - ")[0], key=f"chk_{slot_id}", help=slot):
                        secilen_slotlar.append(slot_id)
                        
        st.markdown("<br>", unsafe_allowed_html=True)
        submit = st.form_submit_button("Submit your vote")
        
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
                st.success("Vote submitted successfully!")
                st.cache_data.clear()
                st.rerun()
    st.markdown('</div>', unsafe_allowed_html=True)
                    
    # SONUÇLAR
    st.markdown('<div class="doodle-card">', unsafe_allowed_html=True)
    st.markdown('<div class="doodle-section-title">📊 Final Results (Most suitable slots on top)</div>', unsafe_allowed_html=True)
    
    if oylar_havuzu:
        hocalar = list(oylar_havuzu.keys())
        st.write(f"**Votes registered ({len(hocalar)}):** " + ", ".join(hocalar))
        
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
        df_sonuc = df_sonuc.sort_values
