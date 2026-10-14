# -*- coding: utf-8 -*-
import streamlit as st


def render_organigramme_tab(data, manager):
    """Rendu de l'onglet Organigramme (Gestion par groupes et membres)."""
    st.subheader("👥 Organigramme du Club")

    # Initialisation de la structure si absente
    if "appli" not in data:
        data["appli"] = {}
    if "organigramme" not in data["appli"]:
        data["appli"]["organigramme"] = []

    orga_data = data["appli"]["organigramme"]

    if not orga_data:
        st.info("Aucun groupe d'organigramme trouvé dans les données.")
        return

    # Boucle sur les groupes (ex: Direction, Pôle Technique, etc.)
    for g_idx, groupe in enumerate(orga_data):
        nom_groupe = groupe.get("groupe", f"Groupe #{g_idx + 1}")
        membres = groupe.get("membres", [])

        with st.expander(f"📋 **{nom_groupe}** ({len(membres)} membres)", expanded=False):

            # --- BOUTON D'AJOUT DE MEMBRE ---
            col_g_title, col_g_add = st.columns([4, 1])
            with col_g_add:
                if st.button(f"➕ Membre", key=f"add_m_{g_idx}", type="primary"):
                    # Vérification de la limite de 3 membres pour 'Direction'
                    if nom_groupe.strip().lower() == "direction" and len(membres) >= 3:
                        st.warning("⚠️ Le groupe 'Direction' est limité à 3 membres maximum.")
                    else:
                        membres.append({
                            "titre": "Nouveau",
                            "nom": "",
                            "tel": "",
                            "email": "",
                            "taches": "",
                            "photo_id": "",
                        })
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            # --- LISTE DES MEMBRES DU GROUPE ---
            if not membres:
                st.caption("Aucun membre dans ce groupe.")

            for m_idx, membre in enumerate(membres):
                st.markdown(f"##### 👤 Membre #{m_idx + 1} : {membre.get('nom') or membre.get('titre') or 'Sans nom'}")

                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    membre["titre"] = st.text_input(
                        "Titre / Rôle",
                        value=membre.get("titre", ""),
                        key=f"orga_titre_{g_idx}_{m_idx}",
                    )
                    membre["nom"] = st.text_input(
                        "Nom & Prénom",
                        value=membre.get("nom", ""),
                        key=f"orga_nom_{g_idx}_{m_idx}",
                    )

                with col2:
                    membre["tel"] = st.text_input(
                        "Téléphone",
                        value=membre.get("tel", ""),
                        key=f"orga_tel_{g_idx}_{m_idx}",
                    )
                    membre["email"] = st.text_input(
                        "E-mail",
                        value=membre.get("email", ""),
                        key=f"orga_email_{g_idx}_{m_idx}",
                    )

                with col3:
                    membre["taches"] = st.text_input(
                        "Tâches / Missions",
                        value=membre.get("taches", ""),
                        key=f"orga_taches_{g_idx}_{m_idx}",
                    )

                # SECTION PHOTO & UPLOAD DRIVE
                col_ph1, col_ph2, col_del = st.columns([5, 3, 1])
                with col_ph1:
                    membre["photo_id"] = st.text_input(
                        "ID Photo Google Drive",
                        value=membre.get("photo_id", ""),
                        key=f"orga_photo_{g_idx}_{m_idx}",
                    )

                with col_ph2:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    uploaded_photo = st.file_uploader(
                        "Changer la photo",
                        type=["jpg", "jpeg", "png", "webp"],
                        key=f"up_photo_{g_idx}_{m_idx}",
                        label_visibility="collapsed",
                    )
                    if uploaded_photo is not None:
                        if st.button("📁 Téléverser", key=f"btn_up_ph_{g_idx}_{m_idx}"):
                            try:
                                with st.spinner("Envoi de la photo sur Google Drive..."):
                                    orga_folder_id = manager.get_orga_folder_id()
                                    file_id, _ = manager.upload_uploaded_file_to_drive(
                                        uploaded_photo, orga_folder_id
                                    )
                                    membre["photo_id"] = file_id
                                st.success("Photo enregistrée !")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Erreur d'envoi : {err}")

                with col_del:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_m_{g_idx}_{m_idx}", help="Supprimer ce membre"):
                        membres.pop(m_idx)
                        st.rerun()

                st.divider()
