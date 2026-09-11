import streamlit as st
import hashlib
import requests

def render_notification_tab(data, config_manager):
    st.subheader("🔔 Gestion des Notifications Push")

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
    # PARTIE 1 : Notification Globale (TournoiVercel)
    # ==========================================
    with st.container(border=True):
        st.markdown("### 📢 1. Notification Générale (Canal : TournoiVercel)")
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

    st.divider()

    # ==========================================
    # PARTIE 2 : Notification par Catégorie Spécifique
    # ==========================================
    with st.container(border=True):
        st.markdown("### 🎯 2. Notification par Catégorie Spécifique")

        # Récupération dynamique des catégories depuis les vestiaires
        vestiaires = data.get("appli", {}).get("vestiaire", [])
        cat_map = {
            item.get("categorie"): item.get("password_admin_hash")
            for item in vestiaires
            if item.get("categorie")
        }

        categories_dispo = list(cat_map.keys())

        if not categories_dispo:
            st.warning("⚠️ Aucune catégorie trouvée dans le vestiaire.")
        else:
            cat_choisie = st.selectbox("Sélectionner la catégorie destinataire :", categories_dispo, key="notif_cat_select")
            cat_pwd = st.text_input("Mot de passe Administrateur de la catégorie :", type="password", key="notif_cat_pwd")
            cat_title = st.text_input("Titre de la notification :", key="notif_cat_title")
            cat_msg = st.text_area("Message (corps) :", height=100, key="notif_cat_msg")

            if st.button("🔒 VÉRIFIER & ENVOYER À LA CATÉGORIE", type="secondary", key="btn_send_cat"):
                if not cat_pwd or not cat_title.strip() or not cat_msg.strip():
                    st.warning("Veuillez remplir le mot de passe, le titre et le corps du message.")
                else:
                    # Vérification du hash du mot de passe
                    stored_hash = cat_map.get(cat_choisie)
                    pwd_hash_saisi = hashlib.sha256(cat_pwd.encode("utf-8")).hexdigest()

                    if pwd_hash_saisi != stored_hash:
                        st.error("Mot de passe administrateur incorrect pour cette catégorie.")
                    else:
                        with st.spinner(f"Envoi vers la catégorie [{cat_choisie}]..."):
                            succes, message = _post_api_notification(cat_choisie, cat_title.strip(), cat_msg.strip())
                        if succes:
                            st.success(message)
                        else:
                            st.error(message)