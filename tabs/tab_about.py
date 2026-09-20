# -*- coding: utf-8 -*-
import streamlit as st

def render_about_tab(data, config_manager):
    """
    Rendu de l'onglet 'About / À propos' pour Streamlit, 
    aligné avec le fonctionnement global de l'application (sauvegarde globale).
    """
    # 1. Vérification et sécurisation de la structure des données
    if "appli" not in data:
        data["appli"] = {}
    if "about" not in data["appli"]:
        data["appli"]["about"] = {}
        
    about_data = data["appli"]["about"]
    sponsor_folder_id = config_manager.get_sponsor_folder_id()

    st.subheader("ℹ️ Configuration de la section 'À propos' (About)")

    # --- SECTION VERSIONS DE LA CIBLE ---
    with st.expander("📱 Versions Cibles", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            v_android = st.text_input(
                "Version Android", 
                value=str(about_data.get('version_android', '')),
                key="input_version_android"
            )
        with col2:
            v_ios = st.text_input(
                "Version iOS", 
                value=str(about_data.get('version_ios', '')),
                key="input_version_ios"
            )

    # --- SECTION TEXTES D'INTRODUCTION ---
    with st.expander("📝 Textes d'Introduction", expanded=True):
        txt_intro_fr = st.text_area(
            "Français", 
            value=str(about_data.get('intro_text', '')),
            height=100,
            key="input_intro_fr"
        )
        txt_intro_en = st.text_area(
            "English", 
            value=str(about_data.get('intro_text_en', '')),
            height=100,
            key="input_intro_en"
        )

    # --- SECTION PARTENAIRE & LOGO ---
    with st.expander("🤝 Partenariat & Logo", expanded=True):
        col_url, col_btn = st.columns([4, 1])
        with col_url:
            v_logo = st.text_input(
                "URL Image Logo (Google Drive)", 
                value=str(about_data.get('logo_partenaire', '')),
                key="input_logo_partenaire"
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)  # Ajustement visuel de l'alignement
            uploaded_logo = st.file_uploader(
                "📁", 
                type=["png", "jpg", "jpeg", "webp"], 
                key="upload_sponsor_logo", 
                label_visibility="collapsed"
            )
            if uploaded_logo is not None:
                try:
                    with st.spinner("Téléchargement sur Drive..."):
                        file_id, file_url = config_manager.upload_uploaded_file_to_drive(
                            uploaded_logo, sponsor_folder_id
                        )
                        if file_url:
                            about_data['logo_partenaire'] = file_url
                            st.success("Logo uploadé avec succès ! Pensez à sauvegarder.")
                            st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'upload : {e}")

        v_sponsor_url = st.text_input(
            "Lien de redirection (Site du Sponsor)", 
            value=str(about_data.get('sponsor_url', '')),
            key="input_sponsor_url"
        )

    # --- SECTION DÉTAILS DYNAMIQUES (Tableau du bas) ---
    with st.expander("📊 Détails Techniques (Bas de page)", expanded=True):
        st.markdown("Gérez les lignes d'information affichées en bas de page de l'application.")

        # Initialisation de la liste des détails dans le session_state si absente
        if "about_details_list" not in st.session_state:
            existing_details = about_data.get('details', [])
            st.session_state.about_details_list = [
                {
                    'label': d.get('label', ''), 
                    'label_en': d.get('label_en', ''), 
                    'value': d.get('value', '')
                }
                for d in existing_details
            ]

        # Affichage et édition dynamique des lignes
        details_to_remove = []
        for index, detail in enumerate(st.session_state.about_details_list):
            cols = st.columns([3, 3, 4, 1])
            with cols[0]:
                detail['label'] = st.text_input(
                    "Libellé (FR)", 
                    value=detail['label'], 
                    key=f"d_fr_{index}", 
                    label_visibility="collapsed" if index > 0 else "visible"
                )
            with cols[1]:
                detail['label_en'] = st.text_input(
                    "Libellé (EN)", 
                    value=detail['label_en'], 
                    key=f"d_en_{index}", 
                    label_visibility="collapsed" if index > 0 else "visible"
                )
            with cols[2]:
                detail['value'] = st.text_input(
                    "Valeur", 
                    value=detail['value'], 
                    key=f"d_val_{index}", 
                    label_visibility="collapsed" if index > 0 else "visible"
                )
            with cols[3]:
                st.markdown("<br>" if index == 0 else "", unsafe_allow_html=True)
                if st.button("❌", key=f"del_detail_{index}"):
                    details_to_remove.append(index)

        # Gestion des suppressions de lignes
        if details_to_remove:
            for i in sorted(details_to_remove, reverse=True):
                st.session_state.about_details_list.pop(i)
            st.rerun()

        if st.button("➕ Ajouter une information", key="btn_add_detail"):
            st.session_state.about_details_list.append({'label': '', 'label_en': '', 'value': ''})
            st.rerun()

    # --- SYNCHRONISATION EN TEMPS RÉEL AVEC LE DICTIONNAIRE GLOBAL ---
    about_data['version_android'] = v_android.strip()
    about_data['version_ios'] = v_ios.strip()
    about_data['intro_text'] = txt_intro_fr.strip()
    about_data['intro_text_en'] = txt_intro_en.strip()
    about_data['logo_partenaire'] = v_logo.strip()
    about_data['sponsor_url'] = v_sponsor_url.strip()
    
    # On filtre pour ignorer les lignes dont le libellé français est vide
    about_data['details'] = [
        {
            'label': d['label'].strip(),
            'label_en': d['label_en'].strip(),
            'value': d['value'].strip()
        }
        for d in st.session_state.about_details_list if d.get('label', '').strip()
    ]