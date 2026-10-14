# -*- coding: utf-8 -*-
import hashlib
import streamlit as st

POSTES_FOOTBALL = [
    "",
    "Gardien",
    "Défenseur central",
    "Latéral droit",
    "Latéral gauche",
    "Piston droit",
    "Piston gauche",
    "Milieu défensif",
    "Milieu central",
    "Milieu offensif",
    "Ailier droit",
    "Ailier gauche",
    "Second attaquant",
    "Avant-centre",
    "Dirigeant",
]


def render_vestiaire_tab(data, manager):
    """Rendu de l'onglet Vestiaire & Médias adapté à Streamlit."""
    st.subheader("📂 Gestion des Vestiaires & Effectifs")

    # Initialisation de la session state pour la gestion vestiaire
    if "vestiaire_current_file_id" not in st.session_state:
        st.session_state.vestiaire_current_file_id = None
    if "vestiaire_data" not in st.session_state:
        st.session_state.vestiaire_data = {}
    if "editing_player_idx" not in st.session_state:
        st.session_state.editing_player_idx = None  # None, "new", ou index entier
    if "show_create_cat_modal" not in st.session_state:
        st.session_state.show_create_cat_modal = False

    vestiaires_list = data.get("appli", {}).get("vestiaire", [])
    cat_map = {item.get("categorie"): item.get("file_id") for item in vestiaires_list if item.get("categorie")}

    # --- 1. SÉLECTION DE LA CATÉGORIE (Si non chargée) ---
    if not st.session_state.vestiaire_current_file_id:
        st.markdown("### Sélection de la catégorie à administrer")
        
        col_sel1, col_sel2 = st.columns([3, 1])
        with col_sel1:
            selected_cat = st.selectbox("Choisir une catégorie :", list(cat_map.keys()), key="select_cat_dropdown")
        with col_sel2:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Ouvrir", type="primary", use_container_width=True):
                if selected_cat:
                    file_id = cat_map.get(selected_cat)
                    if file_id:
                        try:
                            with st.spinner("Chargement des données du vestiaire..."):
                                v_data = manager.load_yaml_from_drive(file_id)
                                if v_data:
                                    st.session_state.vestiaire_data = v_data
                                    st.session_state.vestiaire_current_file_id = file_id
                                    st.success(f"Catégorie {selected_cat} chargée !")
                                    st.rerun()
                                else:
                                    st.error("Fichier de données vide ou introuvable.")
                        except Exception as e:
                            st.error(f"Erreur de chargement : {e}")

        st.divider()
        if st.button("➕ Créer une nouvelle catégorie de vestiaire", type="secondary"):
            st.session_state.show_create_cat_modal = True
            st.rerun()

        # Modal de création de catégorie
        if st.session_state.get("show_create_cat_modal", False):
            with st.expander("🚀 Créer une nouvelle catégorie", expanded=True):
                new_cat_name = st.text_input("Nom de la catégorie (ex: U13)").strip().upper()
                new_pwd = st.text_input("Mot de passe utilisateur", type="password")
                new_pwd_admin = st.text_input("Mot de passe administrateur", type="password")

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    if st.button("Valider la création", type="primary"):
                        if not all([new_cat_name, new_pwd, new_pwd_admin]):
                            st.error("Tous les champs sont obligatoires.")
                        elif any(item.get("categorie") == new_cat_name for item in vestiaires_list):
                            st.error(f"La catégorie {new_cat_name} existe déjà.")
                        else:
                            try:
                                initial_content = {
                                    "chat_admin_only": True,
                                    "calendrier_saison": {},
                                    "documents": [],
                                    "tous_les_joueurs": [],
                                    "groupes": {},
                                }
                                new_id = manager.create_file_on_drive(f"config_{new_cat_name.lower()}.yaml", initial_content)
                                nouvelle_entree = {
                                    "categorie": new_cat_name,
                                    "password_hash": hashlib.sha256(new_pwd.encode()).hexdigest(),
                                    "password_admin_hash": hashlib.sha256(new_pwd_admin.encode()).hexdigest(),
                                    "file_id": new_id,
                                }
                                data.setdefault("appli", {}).setdefault("vestiaire", []).append(nouvelle_entree)
                                manager.save_config(data)
                                st.success(f"Catégorie {new_cat_name} créée avec succès !")
                                st.session_state.show_create_cat_modal = False
                                st.rerun()
                            except Exception as err:
                                st.error(f"Erreur lors de la création : {err}")
                with col_c2:
                    if st.button("Annuler"):
                        st.session_state.show_create_cat_modal = False
                        st.rerun()
        return

    # --- 2. INTERFACE D'ADMINISTRATION DU VESTIAIRE CHARGÉ ---
    v_data = st.session_state.vestiaire_data
    file_id = st.session_state.vestiaire_current_file_id

    col_h_title, col_h_back = st.columns([4, 1])
    with col_h_title:
        st.markdown("### ⚙️ Administration du Vestiaire")
    with col_h_back:
        if st.button("🚪 Changer de catégorie", type="secondary"):
            st.session_state.vestiaire_current_file_id = None
            st.session_state.vestiaire_data = {}
            st.rerun()

    st.divider()

    # Restreindre chat
    v_data["chat_admin_only"] = st.checkbox(
        "Restreindre le chat aux administrateurs uniquement",
        value=v_data.get("chat_admin_only", False)
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # SECTION ÉQUIPES (Calendrier / Classement)
    # ==========================================
    with st.expander("📅 Gestion des Équipes (Calendriers & Classements FFF)", expanded=False):
        if st.button("➕ Ajouter une équipe", key="add_vestiaire_eq_btn"):
            v_data.setdefault("calendrier_saison", {})["Nouvelle équipe"] = {
                "liens_fff": {"calendrier": "", "classement": ""}
            }
            st.rerun()

        calendrier_saison = v_data.get("calendrier_saison", {})
        eq_to_delete = []

        for nom_eq, liens in list(calendrier_saison.items()):
            fff = liens.get("liens_fff", {})
            with st.container(border=True):
                new_nom = st.text_input("Nom de l'équipe", value=nom_eq, key=f"v_eq_nom_{nom_eq}")
                c_cal = st.text_input("URL Calendrier FFF", value=fff.get("calendrier", ""), key=f"v_eq_cal_{nom_eq}")
                c_class = st.text_input("URL Classement FFF", value=fff.get("classement", ""), key=f"v_eq_class_{nom_eq}")

                if st.button("🗑️ Supprimer cette équipe", key=f"del_eq_{nom_eq}"):
                    eq_to_delete.append(nom_eq)

                if new_nom != nom_eq:
                    calendrier_saison[new_nom] = calendrier_saison.pop(nom_eq)
                calendrier_saison[new_nom]["liens_fff"] = {"calendrier": c_cal, "classement": c_class}

        for eq in eq_to_delete:
            calendrier_saison.pop(eq, None)
            st.rerun()

    # ==========================================
    # SECTION DOCUMENTS UTILES
    # ==========================================
    with st.expander("📄 Documents Utiles", expanded=False):
        if st.button("➕ Ajouter un document", key="add_vestiaire_doc_btn"):
            v_data.setdefault("documents", []).append({"nom": "", "url": ""})
            st.rerun()

        documents = v_data.get("documents", [])
        docs_to_remove = []

        for d_idx, doc in enumerate(documents):
            col_dn, col_du, col_dd = st.columns([3, 5, 1])
            with col_dn:
                doc["nom"] = st.text_input("Nom du doc", value=doc.get("nom", ""), key=f"v_doc_nom_{d_idx}", label_visibility="collapsed" if d_idx > 0 else "visible")
            with col_du:
                doc["url"] = st.text_input("URL du doc", value=doc.get("url", ""), key=f"v_doc_url_{d_idx}", label_visibility="collapsed" if d_idx > 0 else "visible")
            with col_dd:
                if d_idx == 0:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("❌", key=f"del_doc_{d_idx}"):
                    docs_to_remove.append(d_idx)

        for idx in sorted(docs_to_remove, reverse=True):
            documents.pop(idx)
            st.rerun()

    # ==========================================
    # SECTION EFFECTIF / JOUEURS
    # ==========================================
    with st.expander("⚽ Effectif Complet", expanded=True):
        col_p_btn1, col_p_btn2 = st.columns([2, 2])
        with col_p_btn1:
            if st.button("➕ Ajouter un joueur", type="primary", key="add_player_modal_btn"):
                st.session_state.editing_player_idx = "new"
                st.rerun()

        joueurs = v_data.setdefault("tous_les_joueurs", [])

        if joueurs:
            # Affichage en tableau résumé
            for j_idx, j in enumerate(joueurs):
                col_j_info, col_j_act = st.columns([5, 1])
                with col_j_info:
                    st.markdown(f"**{j_idx + 1}. {j.get('nom', '').upper()} {j.get('prenom', '')}** — *{j.get('poste', 'Poste non défini')}* (Licence: {j.get('licence', 'N/A')})")
                with col_j_act:
                    if st.button("✏️", key=f"edit_p_{j_idx}", help="Modifier"):
                        st.session_state.editing_player_idx = j_idx
                        st.rerun()
                    if st.button("🗑️", key=f"del_p_{j_idx}", help="Supprimer"):
                        joueurs.pop(j_idx)
                        st.rerun()
        else:
            st.info("Aucun joueur enregistré dans cet effectif.")

        # Formulaire d'ajout / modification de joueur
        if st.session_state.editing_player_idx is not None:
            st.markdown("---")
            is_new = st.session_state.editing_player_idx == "new"
            titre_form = "➕ Ajouter un nouveau joueur" if is_new else "✏️ Modifier le joueur"
            st.markdown(f"#### {titre_form}")

            current_p = {} if is_new else joueurs[st.session_state.editing_player_idx]

            p_nom = st.text_input("Nom", value=current_p.get("nom", ""), key="form_p_nom")
            p_prenom = st.text_input("Prénom", value=current_p.get("prenom", ""), key="form_p_prenom")
            p_cat = st.text_input("Catégorie", value=current_p.get("categorie", ""), key="form_p_cat")
            
            # Poste avec selectbox
            current_poste = current_p.get("poste", "")
            poste_idx = POSTES_FOOTBALL.index(current_poste) if current_poste in POSTES_FOOTBALL else 0
            p_poste = st.selectbox("Poste / Position", POSTES_FOOTBALL, index=poste_idx, key="form_p_poste")

            p_naiss = st.text_input("Date de Naissance (JJ/MM/AAAA)", value=current_p.get("date_naissance", ""), key="form_p_naiss")
            p_licence = st.text_input("Numéro de Licence", value=current_p.get("licence", ""), key="form_p_licence")
            p_photo = st.text_input("URL Photo de profil", value=current_p.get("photo_url", ""), key="form_p_photo")
            
            # Upload photo direct vers Drive
            uploaded_p_photo = st.file_uploader("Ou uploader une photo de profil", type=["png", "jpg", "jpeg", "webp"], key="up_p_photo_file")
            if uploaded_p_photo is not None:
                try:
                    with st.spinner("Téléversement photo..."):
                        profil_folder_id = manager.get_vestiaire_photo_profil_folder_id()
                        _, photo_url = manager.upload_uploaded_file_to_drive(uploaded_p_photo, profil_folder_id)
                        if photo_url:
                            p_photo = photo_url
                            st.success("Photo uploadée !")
                except Exception as err:
                    st.error(f"Erreur upload photo : {err}")

            p_tel = st.text_input("Téléphone", value=current_p.get("telephone", ""), key="form_p_tel")
            p_email = st.text_input("Email", value=current_p.get("email", ""), key="form_p_email")
            p_adresse = st.text_input("Adresse", value=current_p.get("adresse", ""), key="form_p_adresse")

            col_f_save, col_f_cancel = st.columns(2)
            with col_f_save:
                if st.button("✅ Enregistrer le joueur", type="primary", use_container_width=True):
                    if not p_nom.strip() or not p_prenom.strip():
                        st.error("Le nom et le prénom sont obligatoires.")
                    else:
                        updated_player = {
                            "nom": p_nom.strip().upper(),
                            "prenom": p_prenom.strip().capitalize(),
                            "categorie": p_cat.strip(),
                            "poste": p_poste,
                            "date_naissance": p_naiss.strip(),
                            "licence": p_licence.strip(),
                            "photo_url": p_photo.strip(),
                            "telephone": p_tel.strip(),
                            "email": p_email.strip(),
                            "adresse": p_adresse.strip(),
                        }
                        if is_new:
                            joueurs.append(updated_player)
                        else:
                            joueurs[st.session_state.editing_player_idx] = updated_player
                        
                        st.session_state.editing_player_idx = None
                        st.success("Joueur enregistré avec succès !")
                        st.rerun()

            with col_f_cancel:
                if st.button("Annuler", use_container_width=True):
                    st.session_state.editing_player_idx = None
                    st.rerun()

            with col_f_cancel:
                if st.button("Annuler", use_container_width=True):
                    st.session_state.editing_player_idx = None
                    st.rerun()

    # ==========================================
    # SECTION GROUPES (Convocations)
    # ==========================================
    with st.expander("👥 Gestion des Groupes (Convocations)", expanded=False):
        if st.button("➕ Créer un nouveau groupe", key="add_vestiaire_group_btn"):
            v_data.setdefault("groupes", {})["Nouveau Groupe"] = []
            st.rerun()

        groupes = v_data.get("groupes", {})
        groupes_to_remove = []

        for g_nom, membres_in_groupe in list(groupes.items()):
            with st.container(border=True):
                new_g_nom = st.text_input("Nom du groupe", value=g_nom, key=f"v_g_nom_{g_nom}")
                
                st.markdown("**Sélection des joueurs :**")
                selected_membres = []
                
                for j in joueurs:
                    j_full_name = f"{j.get('nom', '').upper()} {j.get('prenom', '')}".strip()
                    # Vérifier si ce joueur était déjà dans le groupe
                    is_checked = any(j.get('nom', '').lower() in m.lower() and j.get('prenom', '').lower() in m.lower() for m in membres_in_groupe)
                    
                    if st.checkbox(j_full_name, value=is_checked, key=f"chk_grp_{g_nom}_{j_full_name}"):
                        selected_membres.append(j_full_name)

                if st.button("🗑️ Supprimer ce groupe", key=f"del_grp_{g_nom}"):
                    groupes_to_remove.append(g_nom)

                if new_g_nom != g_nom:
                    groupes.pop(g_nom)
                groupes[new_g_nom] = selected_membres

        for g in groupes_to_remove:
            groupes.pop(g, None)
            st.rerun()

    st.divider()

    # --- BOUTON DE SAUVEGARDE GLOBALE DU VESTIAIRE ---
    if st.button("💾 ENREGISTRER ET SYNCHRONISER LE VESTIAIRE", type="primary", use_container_width=True):
        try:
            with st.spinner("Synchronisation des données du vestiaire sur Google Drive..."):
                manager.update_file_on_drive(file_id, v_data)
            st.success("Données du vestiaire synchronisées avec succès sur le Cloud !")
        except Exception as err:
            st.error(f"Erreur lors de la sauvegarde : {err}")
