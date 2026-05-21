import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Akademik Ortak Saat Bulucu", layout="wide")

# Google Sheets Bağlantısını Kuruyoruz
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Mevcut verileri e-tablodan çekiyoruz
    existing_data = conn.read(ttl=0) # ttl=0 anlık çekim sağlar
except Exception as e:
    existing_data = pd.DataFrame(columns=["Katilimci", "Secilen_Slot", "Zaman_Damgasi"])

def oylari_isle(df):
    """ Google Sheets'ten gelen ham veriyi Doodle formatına dönüştürür """
    oylar_sozlugu = {}
    if not df.empty:
        for _, row in df.iterrows():
            hoca = row["Katilimci"]
            slot = row["Secilen_Slot"]
            if hoca not in oylar_sozlugu:
                oylar_sozlugu[hoca] = []
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
        # Yeni oyları DataFrame formatına getirip Google Sheets'e ekliyoruz
        yeni_satirlar = []
        zaman_damgasi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for slot in secilen_slotlar:
            yeni_satirlar.append({
                "Katilimci": hoca_adi,
                "Secilen_Slot": slot,
                "Zaman_Damgasi": zaman_damgasi
            })
        
        yeni_df = pd.DataFrame(yeni_satirlar)
        guncel_df = pd.concat([existing_data, yeni_df], ignore_index=True)
        
        # Veriyi Google Sheets'e yazdır
        conn.update(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], data=guncel_df)
        st.success(f"Teşekkürler {hoca_adi}, müsaitlik durumunuz Google Sheets'e kalıcı olarak kaydedildi!")
        st.rerun()

st.markdown("---")
st.markdown("### 📊 2. Adım: Kim Hangi Saate Oy Verdi?")

if oylar_havuzu:
    hocalar = list(oylar_havuzu.keys())
    st.write(f"**Oy Kullanan Katılımcılar ({len(hocalar)}):** " + ", ".join(hocalar))
    
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
