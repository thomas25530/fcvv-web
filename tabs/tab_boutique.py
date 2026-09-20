# -*- coding: utf-8 -*-
import streamlit as st

def render_boutique_tab(data, config_manager):
    """
    Rendu de l'onglet de gestion de la boutique pour Streamlit.
    """
    st.subheader("👕 Gestion de la Boutique")

    # 1. Initialisation de l'état dans le session_state pour éviter les pertes de focus
    if "boutique_state" not in st.session_state:
        raw_boutique = data.get('appli', {}).get('boutique', {})
        raw_produits = raw_boutique.get('produits', [])
        
        formatted_produits = []
        for item in raw_produits:
            formatted_produits.append({
                'nom': str(item.get('nom', '')),
                'type': str(item.get('type', 'Général')),
                'prix': str(item.get('prix', '0')),
                'description': str(item.get('description', '')),
                'image_url': str(item.get('image_url', ''))
            })

        st.session_state.boutique_state = {
            'url_externe': str(raw_boutique.get('url_externe', '')),
            'produits': formatted_produits
        }
        
    if "preview_boutique_product" not in st.session_state:
        st.session_state.preview_boutique_product = None

    boutique_state = st.session_state.boutique_state

    # 2. URL Externe Globale de la Boutique
    with st.container(border=True):
        boutique_state['url_externe'] = st.text_input(
            "URL Boutique Externe (Lien global)",
            value=boutique_state['url_externe'],
            key="input_boutique_url_externe"
        )

    # Bouton d'ajout global d'un type de produit
    col_btn1, col_space = st.columns([2, 5])
    with col_btn1:
        if st.button("➕ AJOUTER UN TYPE DE PRODUIT", type="primary"):
            boutique_state['produits'].append({
                'nom': '',
                'type': 'Nouveau Type',
                'prix': '0',
                'description': '',
                'image_url': ''
            })
            st.rerun()

    st.divider()

    # --- SECTION APERÇU VISUEL (Style Mobile) ---
    if st.session_state.preview_boutique_product:
        prod = st.session_state.preview_boutique_product
        with st.container(border=True):
            col_prev_head, col_prev_close = st.columns([10, 1])
            with col_prev_head:
                st.markdown("### 👁 Aperçu du Produit (Style Mobile)")
            with col_prev_close:
                if st.button("✖", key="close_boutique_preview"):
                    st.session_state.preview_boutique_product = None
                    st.rerun()

            col_img, col_info = st.columns([1, 2])
            with col_img:
                valid_url = prod['image_url'].strip()
                if valid_url:
                    st.image(valid_url, width=150, caption="Image du produit")
                else:
                    st.info("Aucune image renseignée.")
            with col_info:
                st.markdown(f"## {prod['nom'] or 'Nom du produit'}")
                st.caption(f"📁 Catégorie : {prod['type']}")
                try:
                    prix_val = float(prod['prix']) if prod['prix'].strip() else 0.0
                except ValueError:
                    prix_val = 0.0
                st.markdown(f"### 💶 {prix_val:.2f} €")

            st.markdown("---")
            st.markdown("**Description :**")
            st.markdown(prod['description'])
        st.divider()

    # 3. Regroupement des produits par Type / Catégorie
    produits_data = boutique_state['produits']
    groups = {}
    for idx, p in enumerate(produits_data):
        t = p['type'].strip() or "Général"
        if t not in groups:
            groups[t] = []
        groups[t].append((idx, p))

    produits_to_remove = []

    for t in sorted(groups.keys()):
        group_items = groups[t]
        
        with st.container(border=True):
            col_cat_title, col_cat_btn = st.columns([6, 2])
            with col_cat_title:
                st.markdown(f"### 🏷️ Catégorie : `{t}`")
            with col_cat_btn:
                if st.button("➕ Produit", key=f"btn_add_prod_{t}"):
                    boutique_state['produits'].append({
                        'nom': '',
                        'type': t,
                        'prix': '0',
                        'description': '',
                        'image_url': ''
                    })
                    st.rerun()

            st.markdown("---")

            # Liste des produits de la catégorie
            for real_idx, p in group_items:
                col_nom, col_prix, col_img, col_actions = st.columns([3, 1, 4, 2])

                with col_nom:
                    p['nom'] = st.text_input(
                        "Nom", value=p['nom'], 
                        key=f"boutique_nom_{real_idx}",
                        placeholder="Nom du produit"
                    )
                with col_prix:
                    p['prix'] = st.text_input(
                        "Prix (€)", value=p['prix'], 
                        key=f"boutique_prix_{real_idx}"
                    )
                with col_img:
                    sub_col_txt, sub_col_up = st.columns([4, 1])
                    with sub_col_txt:
                        p['image_url'] = st.text_input(
                            "URL Image", value=p['image_url'], 
                            key=f"boutique_img_{real_idx}",
                            placeholder="https://..."
                        )
                    with sub_col_up:
                        uploaded_file = st.file_uploader(
                            "📁", type=["png", "jpg", "jpeg", "webp"], 
                            key=f"up_boutique_img_{real_idx}", 
                            label_visibility="collapsed"
                        )
                        if uploaded_file is not None:
                            try:
                                with st.spinner("Upload..."):
                                    boutique_folder_id = config_manager.get_boutique_folder_id()
                                    _, file_url = config_manager.upload_uploaded_file_to_drive(
                                        uploaded_file, boutique_folder_id
                                    )
                                    if file_url:
                                        p['image_url'] = file_url
                                        st.success("OK !")
                                        st.rerun()
                            except Exception as e:
                                st.error(f"Erreur d'upload : {e}")

                with col_actions:
                    st.markdown("<br>", unsafe_allow_html=True)
                    ac_col1, _, ac_col3 = st.columns(3)
                    with ac_col1:
                        if st.button("👁", key=f"preview_boutique_{real_idx}", help="Aperçu"):
                            st.session_state.preview_boutique_product = p
                            st.rerun()
                    with ac_col3:
                        if st.button("❌", key=f"del_boutique_{real_idx}", help="Supprimer"):
                            produits_to_remove.append(real_idx)

                # Modification du Type et Description détaillée sous chaque produit
                col_type_edit, col_desc_edit = st.columns([2, 5])
                with col_type_edit:
                    p['type'] = st.text_input(
                        "Type / Catégorie", value=p['type'], 
                        key=f"boutique_type_edit_{real_idx}"
                    )
                with col_desc_edit:
                    p['description'] = st.text_area(
                        "Description (supporte [b], [i], [color=#...])", 
                        value=p['description'], 
                        height=80, 
                        key=f"boutique_desc_{real_idx}"
                    )

                st.markdown("---")

    # Suppression effective
    if produits_to_remove:
        for idx in sorted(produits_to_remove, reverse=True):
            boutique_state['produits'].pop(idx)
        st.rerun()

    # 4. Synchronisation finale vers le dictionnaire global `data`
    final_produits = []
    for p in boutique_state['produits']:
        if p['nom'].strip():
            try:
                prix_val = float(p['prix'].strip()) if p['prix'].strip() else 0.0
            except ValueError:
                prix_val = 0.0

            final_produits.append({
                'nom': p['nom'].strip(),
                'type': p['type'].strip() or "Général",
                'prix': prix_val,
                'description': p['description'].strip(),
                'image_url': p['image_url'].strip()
            })

    if "appli" not in data:
        data["appli"] = {}
        
    data["appli"]["boutique"] = {
        'url_externe': boutique_state['url_externe'].strip(),
        'produits': final_produits
    }