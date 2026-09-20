# -*- coding: utf-8 -*-
import streamlit as st

def render_about_tab(data, config_manager):
    """
    Rendu de l'onglet 'About / À propos' pour Streamlit.
    """
    st.subheader("ℹ️ Configuration de la section 'À propos' (About)")

    # Initialisation de l'état dans le session_state pour éviter les pertes de focus et les appels directs
    if "about_data_state" not in st.session_state:
        raw_about = data.get("appli", {}).get("about", {})
        
        # Formatage initial des détails techniques
        existing_details = raw_about.get('details', [])
        formatted_details = [
            {
                'label': d.get('label', ''), 
                'label_en': d.get('label_en', ''), 
                'value': d.get('value', '')
            }
            for d in existing_details
        ]

        st.session_state.about_data_state = {
            "version_android": str(raw_about.get('version_android', '')),
            "version_ios": str(raw_about.get('version_ios', '')),
            "intro_text": str(raw_about.get('intro_text', '')),
            "intro_text_en": str(raw_about.get('intro_text_en', '')),
            "logo_partenaire": str(raw_about.get('logo_partenaire', '')),
            "sponsor_url": str(raw_about.get('sponsor_url', '')),
            "details": formatted_details
        }

    about_state = st.session_state.about_data_state

    # --- SECTION VERSIONS DE LA CIBLE ---
    with st.expander("📱 Versions Cibles", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            about_state["version_android"] = st.text_input(
                "Version Android", 
                value=about_state["version_android"],
                key="input_version_android"
            )
        with col2:
            about_state["version_ios"] = st.text_input(
                "Version iOS", 
                value=about_state["version_ios"],
                key="input_version_ios"
            )

    # --- SECTION TEXTES D'INTRODUCTION ---
    with st.expander("📝 Textes d'Introduction", expanded=True):
        about_state["intro_text"] = st.text_area(
            "Français", 
            value=about_state["intro_text"],
            height=100,
            key="input_intro_fr"
        )
        about_state["intro_text_en"] = st.text_area(
            "English", 
            value=about_state["intro_text_en"],
            height=100,
            key="input_intro_en"
        )

    # --- SECTION PARTENAIRE & LOGO ---
    with st.expander("🤝 Partenariat & Logo", expanded=True):
        col_url, col_btn = st.columns([4, 1])
        with col_url:
            about_state["logo_partenaire"] = st.text_input(
                "URL Image Logo (Google Drive)", 
                value=about_state["logo_partenaire"],
                key="input_logo_partenaire"
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)  
            uploaded_logo = st.file_uploader(
                "📁", 
                type=["png", "jpg", "jpeg", "webp"], 
                key="upload_sponsor_logo", 
                label_visibility="collapsed"
            )
            if uploaded_logo is not None:
                try:
                    with st.spinner("Upload vers Google Drive en cours..."):
                        # Sécurisation de l'appel réseau Drive avec gestion d'erreur locale
                        sponsor_folder_id = config_manager.get_sponsor_folder_id()
                        file_id, file_url = config_manager.upload_uploaded_file_to_drive(
                            uploaded_logo, sponsor_folder_id
                        )
                        if file_url:
                            about_state["logo_partenaire"] = file_url
                            st.success("Logo uploadé avec succès !")
                            st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'upload sur Google Drive : {e}")

        about_state["sponsor_url"] = st.text_input(
            "Lien de redirection (Site du Sponsor)", 
            value=about_state["sponsor_url"],
            key="input_sponsor_url"
        )

    # --- SECTION DÉTAILS DYNAMIQUES (Tableau du bas) ---
    with st.expander("📊 Détails Techniques (Bas de page)", expanded=True):
        st.markdown("Gérez les lignes d'information affichées en bas de page de l'application.")

        details_to_remove = []
        for index, detail in enumerate(about_state["details"]):
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
                about_state["details"].pop(i)
            st.rerun()

        if st.button("➕ Ajouter une information", key="btn_add_detail"):
            about_state["details"].append({'label': '', 'label_en': '', 'value': ''})
            st.rerun()

    # --- SYNCHRONISATION FINALE AVEC LE DICTIONNAIRE GLOBAL `data` ---
    if "appli" not in data:
        data["appli"] = {}
        
    data["appli"]["about"] = {
        "version_android": about_state["version_android"].strip(),
        "version_ios": about_state["version_ios"].strip(),
        "intro_text": about_state["intro_text"].strip(),
        "intro_text_en": about_state["intro_text_en"].strip(),
        "logo_partenaire": about_state["logo_partenaire"].strip(),
        "sponsor_url": about_state["sponsor_url"].strip(),
        "details": [
            {
                'label': d['label'].strip(),
                'label_en': d['label_en'].strip(),
                'value': d['value'].strip()
            }
            for d in about_state["details"] if d.get('label', '').strip()
        ]
    }