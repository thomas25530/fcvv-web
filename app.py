# -*- coding: utf-8 -*-
import json
import hashlib
import streamlit as st
from config_manager import ConfigManager

from tabs.tab_news import render_news_tab
from tabs.tab_notification import render_notification_tab
from tabs.tab_about import render_about_tab
from tabs.tab_partenaires import render_partenaires_tab
from tabs.tab_boutique import render_boutique_tab

# ID de votre fichier YAML principal sur Google Drive

FILE_ID = "161ngxPQz66QumHjG_us6qqyAtA0GPX2x"

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="FC VALDAHON VERCEL - Administration", page_icon="⚽", layout="wide"
)

# 2. APPLICATION IMMÉDIATE DU STYLE CSS SOMBRE (Placé ICI pour être actif dès le Login)
st.markdown("""
<style>
    /* 1. FOND DE PAGE ET COULEUR DU TEXTE PRINCIPAL */
    .stApp {
        background-color: #0b1329 !important;
        color: #f8fafc !important;
    }
    
    /* Titres et textes généraux */
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #f8fafc !important;
    }

    /* 2. CHAMPS ÉDITABLES (Inputs & TextAreas) */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
    }

    .stTextInput input:hover, .stTextArea textarea:hover, div[data-baseweb="select"]:hover {
        border-color: #64748b !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        background-color: #1e293b !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4) !important;
        color: #ffffff !important;
    }

    /* 3. CONTENEURS / CARTES / EXPANDERS */
    div[data-testid="stVerticalBlock"] div[data-testid="stContainer"], 
    .stExpander {
        background-color: #152238 !important;
        border: 1px solid #1e293b !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }

    /* 4. ONGLETS (Tabs) */
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }
    
    button[aria-selected="true"] {
        color: #f7ec3f !important;
        border-bottom-color: #f7ec3f !important;
    }

    /* 5. BOUTONS AMÉLIORÉS */
    button[kind="primary"] {
        background-color: #16a34a !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    button[kind="primary"]:hover {
        background-color: #15803d !important;
    }

    button[kind="secondary"] {
        background-color: #334155 !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }
    button[kind="secondary"]:hover {
        background-color: #475569 !important;
    }

    .stAlert {
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation sécurisée du ConfigManager avec mise en cache Streamlit
@st.cache_resource
def get_config_manager():
    return ConfigManager(FILE_ID)

manager = get_config_manager()

# --- CHARGEMENT DES DONNÉES EN SESSION ---
if "config_data" not in st.session_state:
    with st.spinner("Chargement des configurations depuis Google Drive..."):
        try:
            st.session_state.config_data = manager.load_config()
            st.session_state.load_error = None
        except Exception as e:
            st.session_state.config_data = {"appli": {}}
            st.session_state.load_error = str(e)

data = st.session_state.config_data

# --- SYSTÈME D'AUTHENTIFICATION ---
if "auth_profile" not in st.session_state:
    st.session_state.auth_profile = None

def verify_login(selection, pwd):
    hashed_pwd = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
    appli_data = data.get("appli", {})
    vestiaires_list = appli_data.get("vestiaire", [])
    
    # 1. Recherche du hash super admin
    super_admin_hash = None
    for item in vestiaires_list:
        if isinstance(item, dict) and "password_super_admin_hash" in item:
            super_admin_hash = item.get("password_super_admin_hash")
            break
    if not super_admin_hash:
        super_admin_hash = appli_data.get("password_super_admin_hash")

    if selection == "Administrateur":
        if super_admin_hash and hashed_pwd == super_admin_hash:
            st.session_state.auth_profile = {"type": "super_admin", "allowed_tabs": "all"}
            st.rerun()
        else:
            st.error("Mot de passe Super Admin incorrect.")
    else:
        # 2. Cas d'une catégorie Vestiaire spécifique
        cat_values = {
            item.get("categorie"): item
            for item in vestiaires_list
            if isinstance(item, dict) and item.get("categorie")
        }
        vestiaire_info = cat_values.get(selection)
        if vestiaire_info:
            stored_hash = vestiaire_info.get("password_admin_hash")
            if hashed_pwd == stored_hash:
                st.session_state.auth_profile = {
                    "type": "vestiaire",
                    "allowed_tabs": ["vestiaire", "notification"],
                    "vestiaire_data": vestiaire_info,
                }
                st.rerun()
            else:
                st.error("Mot de passe incorrect pour cette catégorie.")

# Si non connecté, affichage de l'écran de login
if st.session_state.auth_profile is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚽ FC VALDAHON VERCEL")
        st.subheader("Connexion FCVV Admin")
        
        vestiaires = data.get("appli", {}).get("vestiaire", [])
        cat_values = [item.get("categorie") for item in vestiaires if isinstance(item, dict) and item.get("categorie")]
        combo_options = ["Administrateur"] + cat_values
        
        selected_profile = st.selectbox("Sélectionner un profil ou une catégorie :", combo_options)
        password_input = st.text_input("Mot de passe :", type="password")
        
        if st.button("Se connecter", type="primary", use_container_width=True):
            verify_login(selected_profile, password_input)
            
        st.stop()

# Récupération du profil connecté
profile = st.session_state.auth_profile
allowed_tabs = profile.get("allowed_tabs")
is_super_admin = (profile.get("type") == "super_admin")

# Gestion des alertes de connexion au Drive
if st.session_state.load_error:
    st.warning(f"⚠️ **Attention au chargement** : {st.session_state.load_error}. Utilisation des données de secours.")
elif getattr(manager, "is_offline", False):
    st.warning("⚠️ **Mode Hors-Ligne** : Impossible de joindre Google Drive. Utilisation du cache local.")
else:
    st.success("🟢 Connecté à Google Drive avec succès.")

if "appli" not in data:
    data["appli"] = {}

# --- EN-TÊTE & CONFIGURATION DE LA SAISON ---
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.title("⚽ FC VALDAHON VERCEL - Administration")
with col_logout:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Déconnexion", type="secondary"):
        st.session_state.auth_profile = None
        st.rerun()

# Si Super Admin, on autorise la modification de la saison et la maintenance du token
if is_super_admin:
    with st.expander("📅 Configuration de la Saison & Infos techniques", expanded=False):
        col1, col2, col3 = st.columns([2, 2, 4])
        
        saison_data = data["appli"].get("saison", {})
        with col1:
            saison_debut = st.text_input("Début de saison", value=str(saison_data.get("debut", "")))
        with col2:
            saison_fin = st.text_input("Fin de saison", value=str(saison_data.get("fin", "")))
        
        data["appli"]["saison"] = {"debut": saison_debut.strip(), "fin": saison_fin.strip()}
        
        with col3:
            st.markdown(
                """
- **Version** : 1.0.0 (Web Streamlit)
- **Développeur** : Thomas COULOT
- **Contact** : tournoivercel@gmail.com
                """
            )

        st.divider()
        
        st.markdown("🔑 **Maintenance Google Drive (Jeton d'authentification)**")
        st.write("Si le jeton a expiré ou pose problème, déposez votre nouveau fichier `token.json` ci-dessous :")
        
        uploaded_token = st.file_uploader("Importer un nouveau token.json", type=["json"], key="token_uploader")
        if uploaded_token is not None:
            if st.button("Appliquer et synchroniser le nouveau token"):
                try:
                    token_data = json.load(uploaded_token)
                    manager.authenticate_with_token_info(token_data)
                    st.session_state.config_data = manager.load_config()
                    st.session_state.load_error = None
                    st.success("Jeton mis à jour et enregistré avec succès ! Reconnexion établie.")
                    st.rerun()
                except Exception as token_err:
                    st.error(f"Erreur lors de l'application du token : {token_err}")

st.divider()

# --- SYSTÈMES D'ONGLETS ADAPTÉS AUX DROITS DU PROFIL ---
if is_super_admin:
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

    with tabs[0]:
        render_news_tab(data, manager)
    with tabs[1]:
        st.subheader("🗓️ Agenda & Résultats")
        agenda_data = data["appli"].get("agenda", {})
        resultats_data = data["appli"].get("resultats", {})
        st.write("Agenda :", agenda_data)
        st.write("Résultats :", resultats_data)
    with tabs[2]:
        st.subheader("🏆 Classements")
        classements_data = data["appli"].get("classements", {})
        st.write(classements_data)
    with tabs[3]:
        st.subheader("👥 Organigramme")
        org_data = data["appli"].get("organigramme", {})
        st.write(org_data)
    with tabs[4]:
        st.subheader("📁 Divers")
        divers_data = data["appli"].get("divers", {})
        st.write(divers_data)
    with tabs[5]:
        render_boutique_tab(data, manager)
    with tabs[6]:
        render_partenaires_tab(data, manager)
    with tabs[7]:
        render_about_tab(data, manager)
    with tabs[8]:
        st.subheader("📂 Vestiaire & Médias (Google Drive)")
        vestiaire_folder_id = manager.get_vestiaire_folder_id()
        
        uploaded_file = st.file_uploader("Choisir une image à envoyer dans le vestiaire", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file is not None:
            if st.button("Uploader ce fichier sur le Drive"):
                try:
                    with st.spinner("Téléversement vers Google Drive..."):
                        file_id, file_url = manager.upload_uploaded_file_to_drive(uploaded_file, vestiaire_folder_id)
                    st.success(f"Fichier uploadé avec succès ! ID : {file_id}")
                    st.write(f"Lien public : {file_url}")
                except Exception as up_err:
                    st.error(f"Erreur lors de l'upload : {up_err}")
    with tabs[9]:
        render_notification_tab(data, manager)

else:
    # Profil restreint (ex: Vestiaire spécifique)
    st.info(f"Connecté en tant que gestionnaire de la catégorie : **{profile.get('vestiaire_data', {}).get('categorie', '')}**")
    tab_names = ["Vestiaire", "Notification"]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        st.subheader(f"📂 Gestion Vestiaire - {profile.get('vestiaire_data', {}).get('categorie', '')}")
        vestiaire_info = profile.get('vestiaire_data', {})
        st.write("Informations de votre catégorie :", vestiaire_info)
        
        uploaded_file = st.file_uploader("Choisir une image à envoyer dans votre vestiaire", type=["jpg", "jpeg", "png", "webp"])
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

    with tabs[1]:
        render_notification_tab(data, manager)

# --- BOUTON DE SAUVEGARDE GLOBALE (UNIQUEMENT POUR LE SUPER ADMIN) ---
if is_super_admin:
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


