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



@st.fragment
def render_effectif(v_data, manager):
    """Affiche et gère l’effectif dans un fragment Streamlit isolé."""
    with st.expander("⚽ Effectif Complet", expanded=False):
        col_p_btn1, col_p_btn2 = st.columns([2, 2])
        with col_p_btn1:
            if st.button("➕ Ajouter un joueur", type="primary", key="add_player_modal_btn"):
                st.session_state.editing_player_idx = "new"
                st.session_state.show_csv_uploader = False
                st.session_state.csv_rows_to_import = None
        with col_p_btn2:
            if st.button("📥 Importer depuis un CSV", type="secondary", key="open_csv_uploader_btn"):
                st.session_state.show_csv_uploader = not st.session_state.get("show_csv_uploader", False)
                st.session_state.editing_player_idx = None

        joueurs = v_data.setdefault("tous_les_joueurs", [])

        # --- GESTION DE L'UPLOAD DU FICHIER CSV ---
        if st.session_state.get("show_csv_uploader", False):
            with st.container(border=True):
                st.markdown("#### 📥 Importer des joueurs par fichier CSV")
                uploaded_csv = st.file_uploader("Sélectionner le fichier CSV FFF", type=["csv"], key="vestiaire_csv_file_input")

                if uploaded_csv is not None:
                    try:
                        import csv
                        import io

                        bytes_data = uploaded_csv.getvalue()
                        sample = bytes_data[:2048].decode("utf-8-sig", errors="ignore")
                        delimiter = ";" if ";" in sample else ","

                        f_text = io.TextIOWrapper(io.BytesIO(bytes_data), encoding="utf-8-sig")
                        reader = csv.DictReader(f_text, delimiter=delimiter)
                        rows = list(reader)

                        if not rows:
                            st.error("Le fichier CSV est vide.")
                        else:
                            st.session_state.csv_rows_to_import = rows
                            st.session_state.show_csv_uploader = False
                            st.success(f"{len(rows)} lignes lues avec succès ! Veuillez sélectionner les joueurs ci-dessous.")
                    except Exception as err:
                        st.error(f"Erreur lors de la lecture du fichier CSV : {err}")

        # --- INTERFACE DE SÉLECTION DES JOUEURS DU CSV ---
        if st.session_state.get("csv_rows_to_import"):
            rows = st.session_state.csv_rows_to_import

            def nettoyer_cat(cat_str):
                return str(cat_str).split("(")[0].strip()

            categories = sorted({
                nettoyer_cat(row.get("Sous catégorie_1", ""))
                for row in rows
                if row.get("Sous catégorie_1", "").strip()
            })

            with st.container(border=True):
                st.markdown("### 📋 Sélection des joueurs à importer")

                selected_cat_import = st.selectbox("1. Choisir une catégorie :", categories, key="csv_select_cat")

                filtered_indices = [
                    idx for idx, r in enumerate(rows)
                    if nettoyer_cat(r.get("Sous catégorie_1", "")) == selected_cat_import
                ]

                st.markdown(f"**2. Joueurs de la catégorie ({selected_cat_import}) :**")

                if "csv_selected_indices" not in st.session_state:
                    st.session_state.csv_selected_indices = set()

                col_chk1, col_chk2 = st.columns(2)
                with col_chk1:
                    if st.button("Tout cocher pour cette catégorie", key="csv_check_all"):
                        for idx in filtered_indices:
                            st.session_state.csv_selected_indices.add(idx)
                with col_chk2:
                    if st.button("Tout décocher", key="csv_uncheck_all"):
                        for idx in filtered_indices:
                            st.session_state.csv_selected_indices.discard(idx)

                for idx in filtered_indices:
                    row = rows[idx]
                    nom = row.get("Nom", "").strip().upper()
                    prenom = row.get("Prénom", "").strip().capitalize()
                    disp_name = f"{nom} {prenom}" if (nom or prenom) else f"Joueur #{idx+1}"

                    is_checked = idx in st.session_state.csv_selected_indices
                    checked = st.checkbox(disp_name, value=is_checked, key=f"csv_player_chk_{idx}")

                    if checked:
                        st.session_state.csv_selected_indices.add(idx)
                    else:
                        st.session_state.csv_selected_indices.discard(idx)

                st.markdown("---")
                total_selected = len(st.session_state.csv_selected_indices)
                st.info(f"📊 **{total_selected}** joueur(s) sélectionné(s) au total pour l'importation.")

                col_imp_val, col_imp_can = st.columns(2)
                with col_imp_val:
                    if st.button("✅ Valider l'importation des sélectionnés", type="primary", use_container_width=True):
                        if total_selected == 0:
                            st.warning("Veuillez cocher au moins un joueur.")
                        else:
                            effectif = v_data.setdefault("tous_les_joueurs", [])
                            nb_importes = 0
                            nb_mis_a_jour = 0

                            for idx in st.session_state.csv_selected_indices:
                                row = rows[idx]
                                nom = row.get("Nom", "").strip().upper()
                                prenom = row.get("Prénom", "").strip().capitalize()
                                licence = row.get("Numéro personne_1", "").strip()
                                tel = row.get("Mobile personnel_1", "").strip()

                                tel_clean = "".join(filter(str.isdigit, tel))
                                if tel_clean:
                                    if len(tel_clean) == 9 and not tel_clean.startswith("0"):
                                        tel = "0" + tel_clean
                                    elif len(tel_clean) == 10 and not tel_clean.startswith("0"):
                                        tel = "0" + tel_clean[1:]
                                    else:
                                        tel = tel_clean

                                voie = row.get("Voie-rue_1", "").strip()
                                cp = row.get("Code postal_1", "").strip()
                                ville = row.get("Bureau distributeur_2", "").strip()
                                adresse_complete = " ".join(filter(None, [voie, cp, ville]))

                                donnees_csv = {
                                    "nom": nom,
                                    "prenom": prenom,
                                    "categorie": nettoyer_cat(row.get("Sous catégorie_1", "")),
                                    "date_naissance": row.get("Né(e) le_2", "").strip(),
                                    "licence": licence,
                                    "telephone": tel,
                                    "email": row.get("Email principal_1", "").strip(),
                                    "adresse": adresse_complete,
                                }

                                joueur_existant = None
                                for j in effectif:
                                    lic_ex = str(j.get("licence", "")).strip()
                                    nom_ex = str(j.get("nom", "")).strip().upper()
                                    pren_ex = str(j.get("prenom", "")).strip().capitalize()
                                    if (licence and lic_ex == licence) or (nom_ex == nom and pren_ex == prenom):
                                        joueur_existant = j
                                        break

                                if joueur_existant:
                                    joueur_existant.update({k: v for k, v in donnees_csv.items() if v})
                                    nb_mis_a_jour += 1
                                else:
                                    donnees_csv["poste"] = ""
                                    donnees_csv["photo_url"] = ""
                                    effectif.append(donnees_csv)
                                    nb_importes += 1

                            st.session_state.csv_rows_to_import = None
                            st.session_state.csv_selected_indices = set()
                            st.success(f"Importation réussie : {nb_importes} ajouté(s), {nb_mis_a_jour} mis à jour !")

                with col_imp_can:
                    if st.button("Annuler l'import", use_container_width=True):
                        st.session_state.csv_rows_to_import = None
                        st.session_state.csv_selected_indices = set()

        # Formulaire si ajout d'un NOUVEAU joueur (affiché en haut de liste)
        if st.session_state.editing_player_idx == "new":
            with st.container(border=True):
                st.markdown("#### ➕ Ajouter un nouveau joueur")

                p_nom = st.text_input("Nom", value="", key="form_p_nom_new")
                p_prenom = st.text_input("Prénom", value="", key="form_p_prenom_new")
                p_cat = st.text_input("Catégorie", value="", key="form_p_cat_new")
                p_poste = st.selectbox("Poste / Position", POSTES_FOOTBALL, index=0, key="form_p_poste_new")
                p_naiss = st.text_input("Date de Naissance (JJ/MM/AAAA)", value="", key="form_p_naiss_new")
                p_licence = st.text_input("Numéro de Licence", value="", key="form_p_licence_new")
                p_photo = st.text_input("URL Photo de profil", value="", key="form_p_photo_new")

                uploaded_p_photo = st.file_uploader("Ou uploader une photo", type=["png", "jpg", "jpeg", "webp"], key="up_p_photo_file_new")
                if uploaded_p_photo is not None:
                    try:
                        with st.spinner("Téléversement..."):
                            profil_folder_id = manager.get_vestiaire_photo_profil_folder_id()
                            _, photo_url = manager.upload_uploaded_file_to_drive(uploaded_p_photo, profil_folder_id)
                            if photo_url:
                                p_photo = photo_url
                                st.success("Photo uploadée !")
                    except Exception as err:
                        st.error(f"Erreur photo : {err}")

                p_tel = st.text_input("Téléphone", value="", key="form_p_tel_new")
                p_email = st.text_input("Email", value="", key="form_p_email_new")
                p_adresse = st.text_input("Adresse", value="", key="form_p_adresse_new")

                col_f_save, col_f_cancel = st.columns(2)
                with col_f_save:
                    if st.button("✅ Enregistrer", type="primary", use_container_width=True, key="btn_save_p_new"):
                        if not p_nom.strip() or not p_prenom.strip():
                            st.error("Le nom et le prénom sont obligatoires.")
                        else:
                            joueurs.insert(0, {
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
                            })
                            st.session_state.editing_player_idx = None

                with col_f_cancel:
                    if st.button("Annuler", use_container_width=True, key="btn_cancel_p_new"):
                        st.session_state.editing_player_idx = None

        # Liste des joueurs
        if joueurs:
            for j_idx, j in enumerate(joueurs):
                col_j_info, col_j_edit, col_j_del = st.columns([4, 1, 1])
                with col_j_info:
                    st.markdown(f"**{j_idx + 1}. {j.get('nom', '').upper()} {j.get('prenom', '')}** — *{j.get('poste', 'Poste non défini')}*")
                with col_j_edit:
                    if st.button("✏️", key=f"edit_p_{j_idx}", help="Modifier"):
                        st.session_state.editing_player_idx = j_idx
                        st.session_state.show_csv_uploader = False
                        st.session_state.csv_rows_to_import = None
                with col_j_del:
                    if st.button("🗑️", key=f"del_p_{j_idx}", help="Supprimer"):
                        joueurs.pop(j_idx)

                # Le formulaire d'édition s'affiche DÉROULÉ SOUS LE JOUEUR CONCERNÉ
                if st.session_state.editing_player_idx == j_idx:
                    with st.container(border=True):
                        st.markdown(f"#### ✏️ Modifier {j.get('nom', '').upper()} {j.get('prenom', '')}")

                        p_nom = st.text_input("Nom", value=j.get("nom", ""), key=f"form_p_nom_{j_idx}")
                        p_prenom = st.text_input("Prénom", value=j.get("prenom", ""), key=f"form_p_prenom_{j_idx}")
                        p_cat = st.text_input("Catégorie", value=j.get("categorie", ""), key=f"form_p_cat_{j_idx}")

                        current_poste = j.get("poste", "")
                        poste_idx = POSTES_FOOTBALL.index(current_poste) if current_poste in POSTES_FOOTBALL else 0
                        p_poste = st.selectbox("Poste / Position", POSTES_FOOTBALL, index=poste_idx, key=f"form_p_poste_{j_idx}")

                        p_naiss = st.text_input("Date de Naissance (JJ/MM/AAAA)", value=j.get("date_naissance", ""), key=f"form_p_naiss_{j_idx}")
                        p_licence = st.text_input("Numéro de Licence", value=j.get("licence", ""), key=f"form_p_licence_{j_idx}")
                        p_photo = st.text_input("URL Photo de profil", value=j.get("photo_url", ""), key=f"form_p_photo_{j_idx}")

                        uploaded_p_photo = st.file_uploader("Ou uploader une photo", type=["png", "jpg", "jpeg", "webp"], key=f"up_p_photo_file_{j_idx}")
                        if uploaded_p_photo is not None:
                            try:
                                with st.spinner("Téléversement photo..."):
                                    profil_folder_id = manager.get_vestiaire_photo_profil_folder_id()
                                    _, photo_url = manager.upload_uploaded_file_to_drive(uploaded_p_photo, profil_folder_id)
                                    if photo_url:
                                        p_photo = photo_url
                                        st.success("Photo uploadée !")
                            except Exception as err:
                                st.error(f"Erreur photo : {err}")

                        p_tel = st.text_input("Téléphone", value=j.get("telephone", ""), key=f"form_p_tel_{j_idx}")
                        p_email = st.text_input("Email", value=j.get("email", ""), key=f"form_p_email_{j_idx}")
                        p_adresse = st.text_input("Adresse", value=j.get("adresse", ""), key=f"form_p_adresse_{j_idx}")

                        col_f_save, col_f_cancel = st.columns(2)
                        with col_f_save:
                            if st.button("✅ Enregistrer", type="primary", use_container_width=True, key=f"btn_save_p_{j_idx}"):
                                if not p_nom.strip() or not p_prenom.strip():
                                    st.error("Le nom et le prénom sont obligatoires.")
                                else:
                                    joueurs[j_idx] = {
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
                                    st.session_state.editing_player_idx = None

                        with col_f_cancel:
                            if st.button(
                                "Annuler",
                                use_container_width=True,
                                key="btn_cancel_p_new"
                            ):
                                st.session_state.editing_player_idx = None
                                st.rerun()

        else:
            st.info("Aucun joueur enregistré dans cet effectif.")

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
    render_effectif(v_data, manager)
    joueurs = v_data.setdefault("tous_les_joueurs", [])

    # ==========================================
    # SECTION GROUPES (Convocations)
    # ==========================================
    with st.expander("👥 Gestion des Groupes (Convocations)", expanded=False):
        if st.button("➕ Créer un nouveau groupe", key="add_vestiaire_group_btn"):
            v_data.setdefault("groupes", {})["Nouveau Groupe"] = []
            st.rerun()

        groupes = v_data.get("groupes", {})
        groupes_to_remove = []

        for g_idx, (g_nom, membres_in_groupe) in enumerate(list(groupes.items())):
            with st.container(border=True):
                new_g_nom = st.text_input("Nom du groupe", value=g_nom, key=f"v_g_nom_{g_idx}")
                
                st.markdown("**Sélection des joueurs :**")
                selected_membres = []
                
                for j_idx, j in enumerate(joueurs):
                    j_full_name = f"{j.get('nom', '').upper()} {j.get('prenom', '')}".strip()
                    is_checked = any(j.get('nom', '').lower() in m.lower() and j.get('prenom', '').lower() in m.lower() for m in membres_in_groupe)
                    
                    if st.checkbox(j_full_name, value=is_checked, key=f"chk_grp_{g_idx}_{j_idx}"):
                        selected_membres.append(j_full_name)

                if st.button("🗑️ Supprimer ce groupe", key=f"del_grp_{g_idx}"):
                    groupes_to_remove.append(g_nom)

                if new_g_nom != g_nom:
                    groupes.pop(g_nom, None)
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
