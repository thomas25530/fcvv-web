import streamlit as st
from config_manager import ConfigManager

from tabs.tab_news import render_news_tab

# ID de votre fichier YAML principal sur Google Drive
FILE_ID = "161ngxPQz66QumHjG_us6qqyAtA0GPX2x"

st.set_page_config(
    page_title="FC VALDAHON VERCEL - Administration", page_icon="⚽", layout="wide"
)

# Initialisation sécurisée du ConfigManager avec mise en cache Streamlit
@st.cache_resource
def get_config_manager():
    return ConfigManager(FILE_ID)

manager = get_config_manager()

# --- CHARGEMENT DES DONNÉES ---
with st.spinner("Chargement des configurations depuis Google Drive..."):
    try:
        data = manager.load_config()
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        data = {}

# Alerte si mode hors-ligne
if getattr(manager, "is_offline", False):
    st.warning("⚠️ **Mode Hors-Ligne** : Impossible de joindre Google Drive. Utilisation du cache local.")
else:
    st.success("🟢 Connecté à Google Drive avec succès.")

# Assurez-vous que la structure de base existe dans le dictionnaire
if "appli" not in data:
    data["appli"] = {}

# --- EN-TÊTE & CONFIGURATION DE LA SAISON (Similaire au Header Tkinter) ---
st.title("⚽ FC VALDAHON VERCEL - Administration")

with st.expander("📅 Configuration de la Saison & Infos techniques", expanded=False):
    col1, col2, col3 = st.columns([2, 2, 4])
    
    saison_data = data["appli"].get("saison", {})
    with col1:
        saison_debut = st.text_input("Début de saison", value=str(saison_data.get("debut", "")))
    with col2:
        saison_fin = st.text_input("Fin de saison", value=str(saison_data.get("fin", "")))
    
    # Mise à jour de la saison dans le dictionnaire global
    data["appli"]["saison"] = {"debut": saison_debut.strip(), "fin": saison_fin.strip()}
    
    with col3:
        st.markdown(
            """
            * **Version** : 1.0.0 (Web Streamlit)
            * **Développeur** : Thomas COULOT
            * **Contact** : tournoivercel@gmail.com
            """
        )

st.divider()

# --- SYSTÈME D'ONGLETS WEB (Remplace le ttk.Notebook) ---
tab_names = [
    "News",
    "Agenda & Résultats",
    "Classements",
    "Organigramme",
    "Divers",
    "Boutique",
    "Partenaires",
    "About",
    "Vestiaire",
    "Notification"
]

tabs = st.tabs(tab_names)

# 1. Onglet News
with tabs[0]:
    render_news_tab(data, manager)

# 2. Onglet Agenda & Résultats
with tabs[1]:
    st.subheader("🗓️ Agenda & Résultats")
    agenda_data = data["appli"].get("agenda", {})
    resultats_data = data["appli"].get("resultats", {})
    st.write("Agenda :", agenda_data)
    st.write("Résultats :", resultats_data)

# 3. Onglet Classements
with tabs[2]:
    st.subheader("🏆 Classements")
    classements_data = data["appli"].get("classements", {})
    st.write(classements_data)

# 4. Onglet Organigramme
with tabs[3]:
    st.subheader("👥 Organigramme")
    org_data = data["appli"].get("organigramme", {})
    st.write(org_data)

# 5. Onglet Divers
with tabs[4]:
    st.subheader("📁 Divers")
    divers_data = data["appli"].get("divers", {})
    st.write(divers_data)

# 6. Onglet Boutique
with tabs[5]:
    st.subheader("👕 Boutique")
    boutique_data = data["appli"].get("boutique", {})
    st.write(boutique_data)

# 7. Onglet Partenaires
with tabs[6]:
    st.subheader("🤝 Partenaires")
    partenaires_data = data["appli"].get("partenaires", {})
    st.write(partenaires_data)

# 8. Onglet About
with tabs[7]:
    st.subheader("ℹ️ À propos")
    about_data = data["appli"].get("about", {})
    st.write(about_data)

# 9. Onglet Vestiaire (Gestion des médias avec st.file_uploader)
with tabs[8]:
    st.subheader("📂 Vestiaire & Médias (Google Drive)")
    vestiaire_data = data["appli"].get("vestiaire", {})
    
    uploaded_file = st.file_uploader("Choisir une image à envoyer dans le vestiaire", type=["jpg", "jpeg", "png", "webp"])
    if uploaded_file is not None:
        if st.button("Uploader ce fichier sur le Drive"):
            try:
                with st.spinner("Téléversement vers Google Drive..."):
                    vestiaire_folder_id = manager.get_vestiaire_folder_id()
                    file_id, file_url = manager.upload_uploaded_file_to_drive(uploaded_file, vestiaire_folder_id)
                st.success(f"Fichier uploadé avec succès ! ID : {file_id}")
                st.write(f"Lien public : {file_url}")
            except Exception as up_err:
                st.error(f"Erreur lors de l'upload : {up_err}")

# 10. Onglet Notification
with tabs[9]:
    st.subheader("🔔 Notifications")
    notif_data = data["appli"].get("notification", {})
    st.write(notif_data)

# --- BOUTON DE SAUVEGARDE GLOBAL (Bas de page, masqué dans l'onglet Vestiaire si besoin) ---
st.divider()
col_save_left, col_save_right = st.columns([6, 2])

with col_save_right:
    if st.button("💾 SAUVEGARDE GLOBALE", type="primary", use_container_width=True):
        try:
            with st.spinner("Enregistrement sur Google Drive en cours..."):
                manager.save_config(data)
            st.success("Modifications enregistrées et synchronisées avec succès !")
        except Exception as err:
            st.error(f"Erreur lors de la sauvegarde : {err}")