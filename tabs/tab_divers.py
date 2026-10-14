# -*- coding: utf-8 -*-
import streamlit as st


def render_divers_tab(data, manager):
    """Rendu de l'onglet Divers (Stages & Documents)."""
    st.subheader("📁 Section Divers : Stages & Documents")

    # Initialisation de la structure si absente
    if "appli" not in data:
        data["appli"] = {}
    if "divers" not in data["appli"]:
        data["appli"]["divers"] = {"stages": [], "documents": []}

    divers_data = data["appli"]["divers"]

    # --- SÉLECTION DES SOUS-SECTIONS ---
    sub_tab1, sub_tab2 = st.tabs(["⛺ Stages", "📄 Documents"])

    # ==========================================
    # ⛺ SECTION 1 : STAGES
    # ==========================================
    with sub_tab1:
        col_title, col_add = st.columns([4, 1])
        with col_title:
            st.markdown("### Liste des Stages")
        with col_add:
            if st.button("➕ Ajouter un Stage", type="primary", key="add_stage_btn"):
                # Insertion en haut de liste (comme le insert(0, ...) Tkinter)
                new_stage = {
                    "nom": "",
                    "dates_u7_u9": "",
                    "dates_u11_u13": "",
                    "public": "",
                    "programme": "",
                    "tarif": "",
                    "repas": "",
                    "form_url": "",
                    "planning_url": "",
                }
                divers_data["stages"].insert(0, new_stage)
                st.rerun()

        stages_list = divers_data.get("stages", [])

        if not stages_list:
            st.info("Aucun stage enregistré pour le moment.")

        for i, stage in enumerate(stages_list):
            stage_name = stage.get("nom", "").strip() or f"Stage #{i + 1}"
            with st.expander(f"🎪 {stage_name}", expanded=False):
                col_fields_1, col_fields_2 = st.columns(2)

                with col_fields_1:
                    stage["nom"] = st.text_input(
                        "Nom du stage",
                        value=stage.get("nom", ""),
                        key=f"stage_nom_{i}",
                    )
                    stage["dates_u7_u9"] = st.text_input(
                        "Dates U7/U9",
                        value=stage.get("dates_u7_u9", ""),
                        key=f"stage_u7_u9_{i}",
                    )
                    stage["dates_u11_u13"] = st.text_input(
                        "Dates U11/U13",
                        value=stage.get("dates_u11_u13", ""),
                        key=f"stage_u11_u13_{i}",
                    )
                    stage["public"] = st.text_input(
                        "Public visé",
                        value=stage.get("public", ""),
                        key=f"stage_public_{i}",
                    )
                    stage["tarif"] = st.text_input(
                        "Tarif",
                        value=stage.get("tarif", ""),
                        key=f"stage_tarif_{i}",
                    )
                with col_fields_2:
                    stage["repas"] = st.text_input(
                        "Information Repas",
                        value=stage.get("repas", ""),
                        key=f"stage_repas_{i}",
                    )
                    stage["form_url"] = st.text_input(
                        "URL Formulaire d'inscription",
                        value=stage.get("form_url", ""),
                        key=f"stage_form_{i}",
                    )
                    stage["planning_url"] = st.text_input(
                        "URL Planning / PDF",
                        value=stage.get("planning_url", ""),
                        key=f"stage_plan_{i}",
                    )
                    stage["programme"] = st.text_area(
                        "Programme / Description",
                        value=stage.get("programme", ""),
                        key=f"stage_prog_{i}",
                        height=110,
                    )

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(
                    "🗑️ Supprimer ce stage",
                    key=f"del_stage_{i}",
                    type="secondary",
                ):
                    divers_data["stages"].pop(i)
                    st.success(f"Stage '{stage_name}' supprimé !")
                    st.rerun()

    # ==========================================
    # 📄 SECTION 2 : DOCUMENTS
    # ==========================================
    with sub_tab2:
        col_doc_title, col_doc_add = st.columns([4, 1])
        with col_doc_title:
            st.markdown("### Documents du Club")
        with col_doc_add:
            if st.button("➕ Ajouter Document", type="primary", key="add_doc_btn"):
                # Insertion en haut de liste
                divers_data["documents"].insert(0, {"nom": "", "url": ""})
                st.rerun()

        docs_list = divers_data.get("documents", [])

        if not docs_list:
            st.info("Aucun document répertorié pour le moment.")

        for idx, doc in enumerate(docs_list):
            col_nom, col_url, col_del = st.columns([3, 5, 1])

            with col_nom:
                doc["nom"] = st.text_input(
                    "Nom du document",
                    value=doc.get("nom", ""),
                    key=f"doc_nom_{idx}",
                    label_visibility="visible" if idx == 0 else "collapsed",
                )

            with col_url:
                doc["url"] = st.text_input(
                    "Lien / URL du document",
                    value=doc.get("url", ""),
                    key=f"doc_url_{idx}",
                    label_visibility="visible" if idx == 0 else "collapsed",
                )

            with col_del:
                if idx == 0:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_doc_{idx}", help="Supprimer ce document"):
                    divers_data["documents"].pop(idx)
                    st.rerun()
