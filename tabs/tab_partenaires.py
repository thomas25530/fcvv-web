# -*- coding: utf-8 -*-
import streamlit as st

def render_partenaires_tab(data, config_manager):
    """
    Rendu de l'onglet de gestion des partenaires pour Streamlit.
    """
    st.subheader("🤝 Gestion des Partenaires")

    # 1. Initialisation de l'état dans le session_state pour éviter les pertes de focus
    if "partners_state" not in st.session_state:
        raw_data = data.get('appli', {}).get('partenaires', [])
        formatted_partners = []
        for item in raw_data:
            formatted_partners.append({
                'nom': str(item.get('nom', '')),
                'niveau': str(item.get('niveau', 'bronze')),
                'ordre': str(item.get('ordre', '3')),
                'logo': str(item.get('logo', '')),
                'lien': str(item.get('lien', ''))
            })
        st.session_state.partners_state = formatted_partners

    # 2. Barre d'action globale
    col_btn1, col_space = st.columns([2, 5])
    with col_btn1:
        if st.button("➕ AJOUTER UN NIVEAU / PARTENAIRE", type="primary"):
            st.session_state.partners_state.append({
                'nom': '',
                'niveau': 'nouveau',
                'ordre': '99',
                'logo': '',
                'lien': ''
            })
            st.rerun()

    st.divider()

    # 3. Regroupement par niveau
    partners_data = st.session_state.partners_state
    groups = {}
    for idx, p in enumerate(partners_data):
        lvl = p['niveau'].strip().lower() or "non classé"
        if lvl not in groups:
            groups[lvl] = []
        groups[lvl].append((idx, p))

    # Tri des niveaux par ordre du premier élément du groupe
    try:
        sorted_levels = sorted(
            groups.keys(), 
            key=lambda l: int(groups[l][0][1]['ordre'] if groups[l][0][1]['ordre'].isdigit() else 99)
        )
    except Exception:
        sorted_levels = list(groups.keys())

    partners_to_remove = []

    # 4. Affichage par niveau (équivalent des LabelFrame)
    for lvl in sorted_levels:
        group_items = groups[lvl]
        first_p = group_items[0][1]

        with st.container(border=True):
            st.markdown(f"### 🏷️ Niveau : `{lvl.upper()}`")
            
            # Paramètres de niveau partagés (modifiables)
            col_lvl, col_ord, col_add = st.columns([3, 2, 3])
            with col_lvl:
                new_lvl_name = st.text_input("Nom du niveau", value=first_p['niveau'], key=f"lvl_name_{lvl}")
            with col_ord:
                new_lvl_order = st.text_input("Ordre section", value=first_p['ordre'], key=f"lvl_order_{lvl}")
            with col_add:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("➕ Ajouter dans ce niveau", key=f"btn_add_lvl_{lvl}"):
                    st.session_state.partners_state.append({
                        'nom': '',
                        'niveau': first_p['niveau'],
                        'ordre': first_p['ordre'],
                        'logo': '',
                        'lien': ''
                    })
                    st.rerun()

            # Mise à jour synchronisée du niveau et de l'ordre pour tout le groupe si modifié
            for real_idx, p in group_items:
                p['niveau'] = new_lvl_name
                p['ordre'] = new_lvl_order

            st.markdown("---")

            # En-têtes de colonnes du tableau
            c1, c2, c3, c4 = st.columns([3, 3, 4, 1])
            with c1: st.caption("Nom du partenaire")
            with c2: st.caption("Lien URL")
            with c3: st.caption("URL Logo (ou Upload Drive)")
            with c4: st.caption("Action")

            # Liste des partenaires du groupe
            for real_idx, p in group_items:
                col_n, col_l, col_log, col_del = st.columns([3, 3, 4, 1])

                with col_n:
                    p['nom'] = st.text_input(
                        "Nom", value=p['nom'], 
                        key=f"p_nom_{real_idx}", 
                        label_visibility="collapsed"
                    )
                with col_l:
                    p['lien'] = st.text_input(
                        "Lien", value=p['lien'], 
                        key=f"p_lien_{real_idx}", 
                        label_visibility="collapsed"
                    )
                with col_log:
                    # Sous-colonnes pour le champ texte de l'URL et le bouton d'upload fichier
                    sub_col_input, sub_col_btn = st.columns([4, 1])
                    with sub_col_input:
                        p['logo'] = st.text_input(
                            "Logo", value=p['logo'], 
                            key=f"p_logo_{real_idx}", 
                            label_visibility="collapsed"
                        )
                    with sub_col_btn:
                        uploaded_file = st.file_uploader(
                            "📁", type=["png", "jpg", "jpeg", "webp"], 
                            key=f"up_logo_{real_idx}", 
                            label_visibility="collapsed"
                        )
                        if uploaded_file is not None:
                            try:
                                with st.spinner("Upload..."):
                                    sponsor_folder_id = config_manager.get_sponsor_folder_id()
                                    _, file_url = config_manager.upload_uploaded_file_to_drive(
                                        uploaded_file, sponsor_folder_id
                                    )
                                    if file_url:
                                        p['logo'] = file_url
                                        st.success("OK !")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Erreur d'upload : {e}")

                with col_del:
                    if st.button("❌", key=f"del_partner_{real_idx}"):
                        partners_to_remove.append(real_idx)

    # Suppression effective des lignes ciblées
    if partners_to_remove:
        for idx in sorted(partners_to_remove, reverse=True):
            st.session_state.partners_state.pop(idx)
        st.rerun()

    # 5. Synchronisation finale et propre vers le dictionnaire global `data`
    final_list = []
    for p in st.session_state.partners_state:
        if p['nom'].strip():
            try:
                ord_val = int(p['ordre']) if p['ordre'].strip().isdigit() else 3
            except ValueError:
                ord_val = 3

            final_list.append({
                'nom': p['nom'].strip(),
                'niveau': p['niveau'].strip(),
                'ordre': ord_val,
                'logo': p['logo'].strip(),
                'lien': p['lien'].strip()
            })

    # Tri global par ordre avant de stocker
    final_list.sort(key=lambda x: x['ordre'])

    if "appli" not in data:
        data["appli"] = {}
    data["appli"]["partenaires"] = final_list