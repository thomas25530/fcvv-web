# -*- coding: utf-8 -*-
import streamlit as st


def render_agenda_resultats_tab(data, manager):
    """Rendu de l'onglet Agenda & Résultats pour Streamlit."""
    st.subheader("📅 Agenda & ⚽ Résultats du Week-end")

    # Initialisation de la structure si absente
    if "appli" not in data:
        data["appli"] = {}
    if "agenda" not in data["appli"]:
        data["appli"]["agenda"] = {"date_weekend": "", "categories": []}
    if "resultats" not in data["appli"]:
        data["appli"]["resultats"] = {"date_weekend": "", "categories": []}

    agenda_data = data["appli"]["agenda"]
    resultats_data = data["appli"]["resultats"]

    # --- EN-TÊTE GLOBAL DES DATES DE WEEK-END ---
    col_ag_w, col_res_w = st.columns(2)
    with col_ag_w:
        agenda_data["date_weekend"] = st.text_input(
            "📅 Date du week-end (Agenda)",
            value=agenda_data.get("date_weekend", ""),
            key="agenda_weekend_date"
        )
    with col_res_w:
        resultats_data["date_weekend"] = st.text_input(
            "⚽ Date du week-end (Résultats)",
            value=resultats_data.get("date_weekend", ""),
            key="resultat_weekend_date"
        )

    st.divider()

    # --- DEUX COLONNES PRINCIPALES : AGENDA (G) & RÉSULTATS (D) ---
    col_agenda, col_middle, col_resultats = st.columns([10, 2, 10])

    # ==========================================
    # COLONNE GAUCHE : AGENDA
    # ==========================================
    with col_agenda:
        st.markdown("### 📅 AGENDA")
        
        if st.button("➕ Ajouter une Catégorie (Agenda)", type="primary", key="add_agenda_cat_btn"):
            agenda_data["categories"].append({"nom": "", "sous_categories": []})
            st.rerun()

        agenda_cats = agenda_data.get("categories", [])
        agenda_to_remove = []

        if not agenda_cats:
            st.caption("Aucune catégorie dans l'agenda.")

        for c_idx, cat in enumerate(agenda_cats):
            cat_titre = cat.get("nom", "").strip() or f"Catégorie #{c_idx + 1}"
            
            with st.expander(f"📋 {cat_titre}", expanded=False):
                col_c_name, col_c_del = st.columns([4, 1])
                with col_c_name:
                    cat["nom"] = st.text_input("Nom de la catégorie", value=cat.get("nom", ""), key=f"ag_cat_name_{c_idx}")
                with col_c_del:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_ag_cat_{c_idx}", help="Supprimer cette catégorie"):
                        agenda_to_remove.append(c_idx)

                st.markdown("##### Matchs de l'agenda")
                matchs_list = cat.setdefault("sous_categories", [])

                # Bouton d'ajout de match dans cette catégorie
                if st.button("➕ Ajouter un match", key=f"add_ag_match_{c_idx}"):
                    # On ajoute sous forme de structure aplatie pour simplifier la saisie
                    matchs_list.append({
                        "nom": "Match",
                        "matchs": [{
                            "niveau": "", "equipeA": "", "equipeB": "",
                            "lieu": "", "date": "", "heure": ""
                        }]
                    })
                    st.rerun()

                # Pour simplifier l'édition Streamlit, on parcourt les sous-catégories et leurs matchs
                for sub_idx, sub in enumerate(matchs_list):
                    sub_nom = sub.get("nom", "")
                    sub_matchs = sub.get("matchs", [])
                    
                    for m_idx, m in enumerate(sub_matchs):
                        with st.container(border=True):
                            sub["nom"] = st.text_input("Sous-catégorie / Poule", value=sub_nom, key=f"ag_sub_{c_idx}_{sub_idx}_{m_idx}")
                            
                            c_m1, c_m2, c_m3 = st.columns([2, 1, 2])
                            with c_m1:
                                m["equipeA"] = st.text_input("Équipe A", value=m.get("equipeA", ""), key=f"ag_eqA_{c_idx}_{sub_idx}_{m_idx}")
                            with c_m2:
                                m["niveau"] = st.text_input("Niveau", value=m.get("niveau", ""), key=f"ag_niv_{c_idx}_{sub_idx}_{m_idx}")
                            with c_m3:
                                m["equipeB"] = st.text_input("Équipe B", value=m.get("equipeB", ""), key=f"ag_eqB_{c_idx}_{sub_idx}_{m_idx}")

                            c_l1, c_l2, c_l3 = st.columns(3)
                            with c_l1:
                                m["lieu"] = st.text_input("Lieu", value=m.get("lieu", ""), key=f"ag_lieu_{c_idx}_{sub_idx}_{m_idx}")
                            with c_l2:
                                m["date"] = st.text_input("Date", value=m.get("date", ""), key=f"ag_date_{c_idx}_{sub_idx}_{m_idx}")
                            with c_l3:
                                m["heure"] = st.text_input("Heure", value=m.get("heure", ""), key=f"ag_heure_{c_idx}_{sub_idx}_{m_idx}")

                            if st.button(
                                "❌ Supprimer ce match",
                                key=f"del_ag_m_{c_idx}_{sub_idx}_{m_idx}"
                            ):
                                st.write(
                                    f"Suppression demandée : {m_idx} / {m['equipeA']}"
                                )
                            
                                sub_matchs.remove(m)
                            
                                if not sub_matchs:
                                    matchs_list.pop(sub_idx)
                            
                                st.rerun()

        for idx in sorted(agenda_to_remove, reverse=True):
            agenda_cats.pop(idx)
            st.rerun()

    # ==========================================
    # COLONNE CENTRALE : BOUTON DE BASCULE
    # ==========================================
    with col_middle:
        st.markdown("<div style='margin-top: 150px;'></div>", unsafe_allow_html=True)
        if st.button("➡️\nBascule\n⬇️\nRésultats", key="btn_bascule_agenda_res", help="Basculer l'agenda vers les résultats"):
            if not agenda_cats:
                st.warning("Aucun match dans l'agenda à basculer.")
            else:
                resultats_data["date_weekend"] = agenda_data.get("date_weekend", "")
                
                # Conversion de l'agenda vers les résultats (scores vides)
                nouvelles_cats_res = []
                for cat in agenda_cats:
                    cat_res = {"nom": cat.get("nom", ""), "sous_categories": []}
                    for sub in cat.get("sous_categories", []):
                        sub_res_matchs = []
                        for m in sub.get("matchs", []):
                            sub_res_matchs.append({
                                "equipeA": m.get("equipeA", ""),
                                "scoreA": "",
                                "equipeB": m.get("equipeB", ""),
                                "scoreB": "",
                                "issue": "V",
                                "buteurs": ""
                            })
                        cat_res["sous_categories"].append({"nom": sub.get("nom", ""), "matchs": sub_res_matchs})
                    nouvelles_cats_res.append(cat_res)
                
                resultats_data["categories"] = nouvelles_cats_res
                st.success("Basculement effectué avec succès !")
                st.rerun()

    # ==========================================
    # COLONNE DROITE : RÉSULTATS
    # ==========================================
    with col_resultats:
        st.markdown("### ⚽ RÉSULTATS")
        
        if st.button("➕ Ajouter une Catégorie (Résultats)", type="primary", key="add_res_cat_btn"):
            resultats_data["categories"].append({"nom": "", "sous_categories": []})
            st.rerun()

        res_cats = resultats_data.get("categories", [])
        res_to_remove = []

        if not res_cats:
            st.caption("Aucun résultat enregistré.")

        for c_idx, cat in enumerate(res_cats):
            cat_titre = cat.get("nom", "").strip() or f"Catégorie #{c_idx + 1}"
            
            with st.expander(f"📋 {cat_titre}", expanded=False):
                col_c_name, col_c_del = st.columns([4, 1])
                with col_c_name:
                    cat["nom"] = st.text_input("Nom de la catégorie", value=cat.get("nom", ""), key=f"res_cat_name_{c_idx}")
                with col_c_del:
                    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_res_cat_{c_idx}", help="Supprimer cette catégorie"):
                        res_to_remove.append(c_idx)

                st.markdown("##### Matchs joués & Scores")
                matchs_list = cat.setdefault("sous_categories", [])

                if st.button("➕ Ajouter un résultat", key=f"add_res_match_{c_idx}"):
                    matchs_list.append({
                        "nom": "Match",
                        "matchs": [{
                            "equipeA": "", "scoreA": "", "equipeB": "", "scoreB": "",
                            "issue": "V", "buteurs": ""
                        }]
                    })
                    st.rerun()

                for sub_idx, sub in enumerate(matchs_list):
                    sub_nom = sub.get("nom", "")
                    sub_matchs = sub.get("matchs", [])
                    
                    for m_idx, m in enumerate(sub_matchs):
                        with st.container(border=True):
                            sub["nom"] = st.text_input("Sous-catégorie / Poule", value=sub_nom, key=f"res_sub_{c_idx}_{sub_idx}_{m_idx}")
                            
                            c_r1, c_r2, c_r3, c_r4 = st.columns([2, 1, 1, 2])
                            with c_r1:
                                m["equipeA"] = st.text_input("Équipe A", value=m.get("equipeA", ""), key=f"res_eqA_{c_idx}_{sub_idx}_{m_idx}")
                            with c_r2:
                                m["scoreA"] = st.text_input("Buts A", value=str(m.get("scoreA", "")), key=f"res_scA_{c_idx}_{sub_idx}_{m_idx}")
                            with c_r3:
                                m["scoreB"] = st.text_input("Buts B", value=str(m.get("scoreB", "")), key=f"res_scB_{c_idx}_{sub_idx}_{m_idx}")
                            with c_r4:
                                m["equipeB"] = st.text_input("Équipe B", value=m.get("equipeB", ""), key=f"res_eqB_{c_idx}_{sub_idx}_{m_idx}")

                            m["buteurs"] = st.text_input("Buteurs", value=m.get("buteurs", ""), key=f"res_but_{c_idx}_{sub_idx}_{m_idx}")

                            if st.button(
                                "❌ Supprimer ce résultat",
                                key=f"del_res_m_{c_idx}_{sub_idx}_{m_idx}"
                            ):
                                sub_matchs.remove(m)
                            
                                if not sub_matchs:
                                    matchs_list.pop(sub_idx)
                            
                                st.rerun()

        for idx in sorted(res_to_remove, reverse=True):
            res_cats.pop(idx)
            st.rerun()
