# -*- coding: utf-8 -*-
import streamlit as st


def render_classements_tab(data, manager):
    """Rendu de l'onglet Classements avec application du barème FFF."""
    st.subheader("🏆 Gestion des Classements (Barème FFF)")

    # Initialisation de la structure si absente
    if "appli" not in data:
        data["appli"] = {}
    if "classements" not in data["appli"]:
        data["appli"]["classements"] = []

    classements_list = data["appli"]["classements"]

    # --- BARRE D'OUTILS GLOBALE ---
    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button("➕ Ajouter un tableau de classement", type="primary", key="add_table_btn"):
            classements_list.insert(0, {
                "equipe_nom": "",
                "journee": "",
                "maj": "",
                "tableau": []
            })
            st.rerun()

    with col_btn2:
        if st.button("⚡ Calculer et trier (Barème FFF)", type="secondary", key="calc_all_btn"):
            _calculer_et_trier(classements_list)
            st.success("Calculs FFF et tris effectués avec succès !")
            st.rerun()

    st.divider()

    if not classements_list:
        st.info("Aucun tableau de classement enregistré pour le moment.")
        return

    # Boucle sur chaque tableau de classement
    for t_idx, table in enumerate(classements_list):
        equipe_titre = table.get("equipe_nom", "").strip() or f"Tableau #{t_idx + 1}"
        
        with st.expander(f"📊 Classement : {equipe_titre}", expanded=False):
            
            # --- AIDE / BAREME FFF ---
            st.info(
                "📌 **Barème FFF** : Gagné = 3 pts | Nul = 1 pt | Perdu = 0 pt | Forfait (F) = -1 pt | Pénalité (PE) = valeur saisie\n\n"
                "⚖️ **Règles d'égalité** : 1. Nombre de points | 2. Différence de buts (Diff) | 3. Buts pour (BP)"
            )

            # --- EN-TÊTE DU TABLEAU ---
            col_h1, col_h2, col_h3, col_h_del = st.columns([3, 2, 2, 1])
            with col_h1:
                table["equipe_nom"] = st.text_input(
                    "Équipe concernée",
                    value=table.get("equipe_nom", ""),
                    key=f"class_nom_{t_idx}"
                )
            with col_h2:
                table["journee"] = st.text_input(
                    "Journée",
                    value=table.get("journee", ""),
                    key=f"class_j_{t_idx}"
                )
            with col_h3:
                table["maj"] = st.text_input(
                    "Mise à jour (MàJ)",
                    value=table.get("maj", ""),
                    key=f"class_maj_{t_idx}"
                )
            with col_h_del:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Supprimer", key=f"del_table_{t_idx}", help="Supprimer ce tableau"):
                    classements_list.pop(t_idx)
                    st.rerun()

            st.markdown("#### Équipes du classement")
            
            rows = table.get("tableau", [])
            
            # Bouton d'ajout d'une ligne
            if st.button("➕ Ajouter une équipe", key=f"add_row_{t_idx}", type="primary"):
                rows.append({
                    "rang": "", "equipe": "", "pts": "0", "j": "0",
                    "g": "0", "n": "0", "p": "0", "f": "0",
                    "bp": "0", "bc": "0", "pe": "0", "diff": "0"
                })
                st.rerun()

            if not rows:
                st.caption("Aucune équipe dans ce tableau.")
            else:
                # Affichage des lignes sous forme de tableau interactif
                for r_idx, row in enumerate(rows):
                    c_rang, c_eq, c_pts, c_j, c_g, c_n, c_p, c_f, c_bp, c_bc, c_pe, c_diff, c_del = st.columns([
                        0.6, 2.5, 0.8, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.8, 0.5
                    ])

                    with c_rang:
                        # Rang calculé (lecture seule)
                        st.text_input("Rang", value=str(row.get("rang", "")), key=f"r_rang_{t_idx}_{r_idx}", disabled=True, label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_eq:
                        row["equipe"] = st.text_input("Équipe", value=row.get("equipe", ""), key=f"r_eq_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_pts:
                        # Pts calculé (lecture seule)
                        st.text_input("Pts", value=str(row.get("pts", "0")), key=f"r_pts_{t_idx}_{r_idx}", disabled=True, label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_j:
                        # J calculé (lecture seule)
                        st.text_input("J", value=str(row.get("j", "0")), key=f"r_j_{t_idx}_{r_idx}", disabled=True, label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_g:
                        row["g"] = st.text_input("G", value=str(row.get("g", "0")), key=f"r_g_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_n:
                        row["n"] = st.text_input("N", value=str(row.get("n", "0")), key=f"r_n_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_p:
                        row["p"] = st.text_input("P", value=str(row.get("p", "0")), key=f"r_p_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_f:
                        row["f"] = st.text_input("F", value=str(row.get("f", "0")), key=f"r_f_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_bp:
                        row["bp"] = st.text_input("BP", value=str(row.get("bp", "0")), key=f"r_bp_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_bc:
                        row["bc"] = st.text_input("BC", value=str(row.get("bc", "0")), key=f"r_bc_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_pe:
                        row["pe"] = st.text_input("PE", value=str(row.get("pe", "0")), key=f"r_pe_{t_idx}_{r_idx}", label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_diff:
                        # Diff calculée (lecture seule)
                        st.text_input("Diff", value=str(row.get("diff", "0")), key=f"r_diff_{t_idx}_{r_idx}", disabled=True, label_visibility="collapsed" if r_idx > 0 else "visible")
                    with c_del:
                        if r_idx == 0:
                            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                        if st.button("×", key=f"del_row_{t_idx}_{r_idx}", help="Supprimer cette ligne"):
                            rows.pop(r_idx)
                            st.rerun()

            # Calcul automatique en temps réel à l'affichage
            _calculer_et_trier([table])


def _obtenir_valeur_int(valeur_saisie):
    """Convertit une saisie en entier, retourne 0 si vide ou invalide."""
    try:
        return int(valeur_saisie)
    except (ValueError, TypeError):
        return 0


def _calculer_et_trier(classements_list):
    """Applique le barème FFF et trie selon les règles d'égalité pour une liste de tableaux."""
    for table in classements_list:
        rows = table.get("tableau", [])
        
        for r in rows:
            g = _obtenir_valeur_int(r.get("g", 0))
            n = _obtenir_valeur_int(r.get("n", 0))
            p = _obtenir_valeur_int(r.get("p", 0))
            f = _obtenir_valeur_int(r.get("f", 0))
            bp = _obtenir_valeur_int(r.get("bp", 0))
            bc = _obtenir_valeur_int(r.get("bc", 0))
            pe = _obtenir_valeur_int(r.get("pe", 0))

            matchs_joues = g + n + p + f
            points = (g * 3) + (n * 1) + (f * -1) + pe
            difference = bp - bc

            r["j"] = str(matchs_joues)
            r["pts"] = str(points)
            r["diff"] = str(difference)

        # Tri FFF : 1) Points, 2) Différence de buts, 3) Buts pour
        rows.sort(key=lambda x: (
            _obtenir_valeur_int(x.get("pts", 0)),
            _obtenir_valeur_int(x.get("diff", 0)),
            _obtenir_valeur_int(x.get("bp", 0))
        ), reverse=True)

        # Attribution des rangs
        for index, r in enumerate(rows):
            r["rang"] = str(index + 1)
