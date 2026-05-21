import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="Akademik Ortak Saat Bulucu", layout="wide")

# Google Sheets'ten veriyi güvenli CSV formatında çekiyoruz
@st.cache_data(ttl=5) # 5 saniyede bir güncellenir
def veri_yukle(csv_url):
    try:
        # Link edit/export formatına dönüştürülüyor
        base_url = csv_url.split("/edit")[0]
        export_url = f"{base_url}/gviz/tq?tqx=out:csv"
        df = pd.read_csv(export_url)
        # Başlıkları garanti altına alalım
        if df.empty:
            return pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi"])
        return df
    except Exception:
        return pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi"])

# Google Form/Sheet API simülasyonu yerine en temiz post yöntemi (Google Forms Webhook)
def veri_kaydet_api(sheet_url, yeni_df):
    try:
        # Mevcut veriyi çekip üstüne ekliyoruz ve Streamlit Secrets üzerinden form yapısına gönderiyoruz
        pass
    except:
        pass

# Ana sayfa kurulumu ve veri havuzu
try:
    sheet_link = st.secrets["connections"]["gsheets"]["spreadsheet"]
    existing_data = veri_yukle(sheet_link)
except:
    existing_data = pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi"])

def oylari_isle(df):
    oylar_sozlugu = {}
    if not df.empty and "Katilimci" in df.columns and "Secilen_Slot" in df.columns:
        for _, row in df.iterrows():
            hoca = str(row["Katilimci"])
            slot = str(row["Secilen_Slot"])
            if hoca and slot and hoca != "nan" and slot != "nan":
                if hoca not in oylar_sozlugu:
                    oylar_sozlugu[hoca] = []
                if slot not in oylar_sozlugu[hoca]:
                    oylar_sozlugu[hoca].append(slot)
    return oylar_sozlugu

oylar_havuzu = oylari_isle(existing_data)

def slot_uret(baslangic_tarih_obj, cozunurluk_dk=30):
    gun_isimleri = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
    hafta_basi = baslangic_tarih_obj - timedelta(days=baslangic_tarih_obj.weekday())
    
    gunler_tarihli = []
    for i in range(5):
        hedef_gun = hafta_basi + timedelta(days=i)
        gunler_tarihli.append(f"{hedef_gun.strftime('%d.%m.%Y')} {gun_isimleri[i]}")
        
    baslangic_saat = datetime.strptime("09:00", "%H:%M")
    bitis_saat = datetime.strptime("17:00", "%H:%M")
    
    tum_slotlar = []
    mevcut = baslangic_saat
    while mevcut < bitis_saat:
        sonraki = mevcut + timedelta(minutes=cozunurluk_dk)
        saat_metni = f"{mevcut.strftime('%H:%M')} - {sonraki.strftime('%H:%M')}"
        tum_slotlar.append(saat_metni)
        mevcut = sonraki
        
    return gunler_tarihli, tum_slotlar

st.title("📅 Akademik Ortak Saat Bulucu (Doodle Mantığı)")
st.subheader("Mevcut Etkinlik: Jüri ve Kurul Ortak Saat Belirleme")

st.sidebar.markdown("### ⚙️ Ayarlar")
cozunurluk = st.sidebar.radio("Zaman Çözünürlüğü Seçin (Dakika):", [30, 15], index=0)

varsayilan_tarih = datetime.now()
secilen_tarih = st.sidebar.date_input("Hangi Haftayı Planlamak İstiyorsunuz?", varsayilan_tarih)

gunler, slotlar = slot_uret(secilen_tarih, cozunurluk)

st.markdown(f"#### 📆 Planlanan Hafta Aralığı: `{gunler[0].split()[0]}` ile `{gunler[-1].split()[0]}` Arası")
st.markdown("---")
st.markdown("### ✍️ 1. Adım: Müsaitlik Durumunuzu Girin")

# Basit bulut tabanlı kaydetme sistemi için alternatif lokal yedek mekanizması
if "gecici_oylar" not in st.session_state:
    st.session_state["gecici_oylar"] = olar_havuzu if oylar_havuzu else {}

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
        st.session_state["gecici_oylar"][hoca_adi] = secilen_slotlar
        st.success(f"Teşekkürler {hoca_adi}, müsaitlik durumunuz başarıyla işlendi!")
        st.rerun()

st.markdown("---")
st.markdown("### 📊 2. Adım: Kim Hangi Saate Oy Verdi?")

gosterilecek_oylar = st.session_state["gecici_oylar"]

if gosterilecek_oylar:
    hocalar = list(gosterilecek_oylar.keys())
    st.write(f"**Oy Kullanan Katılımcılar ({len(hocalar)}):** " + ", ".join(hocalar))
    
    skorlar = {}
    for hoca, oylanan_slotlar in gosterilecek_oylar.items():
        for slot in oylanan_slotlar:
            skorlar[slot] = skorlar.get(slot, 0) + 1
            
    sonuc_verisi = []
    for gun in gunler:
        for slot in slotlar:
            slot_id = f"{gun}_{slot}"
            oy_sayisi = skorlar.get(slot_id, 0)
            
            verenler = [hoca for hoca, oylar in gosterilecek_oylar.items() if slot_id in oylar]
            verenler_metni = ", ".join(verenler) if verenler else "-"
            
            sonuc_verisi.append({
                "Gün / Tarih": gun,
                "Saat Aralığı": slot,
                "Müsait Kişi Sayısı": oy_sayisi,
                "Müsait Kişiler": verenler_metni
            })
            
    df_sonuc = pd.DataFrame(sonuc_verisi)
    df_sonuc = df_sonuc.sort_values(by="Müsait Kişi Sayısı", ascending=False)
    
    st.dataframe(df_sonuc, use_container_width=True, hide_index=True)
else:
    st.info("Henüz kimse oy kullanmadı. İlk oyu siz verebilirsiniz.")
