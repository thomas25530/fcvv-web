# -*- coding: utf-8 -*-
import streamlit as st
import hashlib
import requests

def render_notification_tab(data, config_manager, auth_profile=None):
    st.subheader("🔔 Gestion des Notifications Push")

    # Si le profil n'est pas passé en argument, on essaie de le récupérer depuis st.session_state
    if not auth_profile:
        auth_profile = st.session_state.get("auth_profile", {"type": "super_admin", "allowed_tabs": "all"})

    is_super = (auth_profile.get("type") == "super_admin")

    # --- FONCTION INTERNE POUR L'API ---
    def _get_admin_api_key():
        try:
            admin_api_key = data.get("appli", {}).get("admin_api_key", "")
            admin_api_key = str(admin_api_key).strip()
            if not admin_api_key:
                return None
            return admin_api_key
        except Exception:
            return None

    def _post_api_notification(endpoint_target, titre, corps):
        admin_api_key = _get_admin_api_key()
        if not admin_api_key:
            return False, "Clé API admin introuvable dans la configuration."

        url = f"https://fcvv-api.onrender.com/admin/notifier/{endpoint_target}"
        payload = {"titre": titre, "corps": corps}
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Token": admin_api_key
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code in (200, 201):
                return True, "Notification envoyée avec succès !"
            return False, f"Erreur Serveur ({response.status_code}) : {response.text}"
        except requests.exceptions.Timeout:
            return False, "Le serveur a mis trop de temps à répondre (Cold Start Render ?). Réessayez dans un instant."
        except requests.exceptions.RequestException as e:
            return False, f"Impossible de contacter l'API :\n{e}"

    # ==========================================
    # CAS 1 : SUPER ADMIN (Voit tout)
    # ==========================================
    if is_super:
        # --- PARTIE 1 : Notification Globale (TournoiVercel) repliée par défaut ---
        with st.expander("📢 1. Notification Générale (Toutes les applis)", expanded=False):
            st.caption("Cette notification sera transmise à TOUTES les applications connectées.")

            gen_title = st.text_input("Titre de la notification (Générale)", key="gen_notif_title")
            gen_msg = st.text_area("Message (corps)", height=100, key="gen_notif_msg")

            if st.button("🚀 ENVOYER À TOUTES LES APPLIS", type="primary", key="btn_send_gen"):
                if not gen_title.strip() or not gen_msg.strip():
                    st.warning("Veuillez remplir le titre et le corps du message.")
                else:
                    with st.spinner("Envoi de la notification globale en cours..."):
                        succes, message = _post_api_notification("TournoiVercel", gen_title.strip(), gen_msg.strip())
                    if succes:
                        st.success(message)
                    else:
                        st.error(message)

        # --- PARTIE 2 : Notification par Catégorie Spécifique repliée par défaut ---
        with st.expander("🎯 2. Notification par Catégorie Spécifique", expanded=False):
            vestiaires = data.get("appli", {}).get("vestiaire", [])
            categories_dispo = [
                item.get("categorie")
                for item in vestiaires
                if isinstance(item, dict) and item.get("categorie")
            ]

            if not categories_dispo:
                st.warning("⚠️ Aucune catégorie trouvée dans le vestiaire.")
            else:
                cat_choisie = st.selectbox("Sélectionner la catégorie destinataire :", categories_dispo, key="notif_cat_select_super")
                cat_title = st.text_input("Titre de la notification :", key="notif_cat_title_super")
                cat_msg = st.text_area("Message (corps) :", height=100, key="notif_cat_msg_super")

                if st.button("🚀 ENVOYER À LA CATÉGORIE", type="primary", key="btn_send_cat_super"):
                    if not cat_choisie:
                        st.warning("Aucune catégorie sélectionnée.")
                    elif not cat_title.strip() or not cat_msg.strip():
                        st.warning("Veuillez remplir le titre et le corps du message.")
                    else:
                        with st.spinner(f"Envoi vers la catégorie [{cat_choisie}]..."):
                            succes, message = _post_api_notification(cat_choisie, cat_title.strip(), cat_msg.strip())
                        if succes:
                            st.success(message)
                        else:
                            st.error(message)

    # ==========================================
    # CAS 2 : PROFIL RESTREINT (Catégorie spécifique)
    # ==========================================
    else:
        vestiaire_data = auth_profile.get("vestiaire_data", {})
        current_categorie = vestiaire_data.get("categorie", "Inconnue")

        with st.expander(f"🎯 Envoi de Notification - Catégorie : {current_categorie}", expanded=False):
            st.caption(f"Vous êtes connecté pour la catégorie [{current_categorie}]. Vous pouvez envoyer des notifications uniquement à vos membres.")

            cat_title = st.text_input("Titre de la notification :", key="notif_cat_title_restreint")
            cat_msg = st.text_area("Message (corps) :", height=100, key="notif_cat_msg_restreint")

            if st.button(f"🚀 ENVOYER À [{current_categorie}]", type="primary", key="btn_send_cat_restreint"):
                if not cat_title.strip() or not cat_msg.strip():
                    st.warning("Veuillez remplir le titre et le corps du message.")
                else:
                    with st.spinner(f"Envoi vers la catégorie [{current_categorie}]..."):
                        succes, message = _post_api_notification(current_categorie, cat_title.strip(), cat_msg.strip())
                    if succes:
                        st.success(message)
                    else:
                        st.error(message)
