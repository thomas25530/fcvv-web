import streamlit as st
from config_manager import ConfigManager

# ID de votre fichier YAML principal sur Google Drive
FILE_ID = "161ngxPQz66QumHjG_us6qqyAtA0GPX2x"

st.set_page_config(
    page_title="Administration FCVV", page_icon="⚽", layout="wide"
)

st.title("⚽ Administration FCVV - Gestion YAML")


# Initialisation sécurisée du ConfigManager avec mise en cache Streamlit
@st.cache_resource
def get_config_manager():
    return ConfigManager(FILE_ID)


manager = get_config_manager()

# --- CHARGEMENT DES DONNÉES ---
with st.spinner("Chargement des configurations depuis Google Drive..."):
    try:
        data = manager.load_config()
    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        data = {}

# Alerte si mode hors-ligne
if getattr(manager, "is_offline", False):
    st.warning(
        "⚠️ **Mode Hors-Ligne** : Impossible de joindre Google Drive. Utilisation du cache local."
    )
else:
    st.success("🟢 Connecté à Google Drive avec succès.")

# --- INTERFACE D'ADMINISTRATION ---
if data:
    st.subheader("Structure actuelle des données (YAML)")

    # Option 1 : Affichage et édition interactive via l'éditeur de données Streamlit ou texte brut
    # Streamlit propose un éditeur de code intégré très pratique pour le YAML ou JSON
    updated_chat_status = st.checkbox(
        "Activer le mode admin uniquement pour le chat",
        value=data.get("chat_admin_only", False),
    )
    data["chat_admin_only"] = updated_chat_status

    # Affichage brut ou textuel pour modifier les sections complexes
    with st.expander("Voir / Modifier le contenu brut du YAML"):
        # On convertit le dictionnaire en texte modifiable
        import yaml

        yaml_str = yaml.dump(
            data, allow_unicode=True, sort_keys=False, default_flow_style=False
        )
        new_yaml_str = st.text_area(
            "Éditeur YAML", yaml_str, height=300, key="yaml_editor"
        )

        try:
            parsed_data = yaml.safe_load(new_yaml_str)
        except Exception as parse_err:
            st.error(freur de syntaxe YAML : {parse_err}")
            parsed_data = None

    # --- BOUTON DE SAUVEGARDE ---
    if st.button(
        "💾 Sauvegarder les modifications sur Google Drive", type="primary"
    ):
        target_data = parsed_data if parsed_data is not None else data
        try:
            with st.spinner("Enregistrement en cours..."):
                manager.save_config(target_data)
            st.success("Modifications enregistrées et synchronisées avec succès !")
            st.rerun()
        except Exception as err:
            st.error(f"Erreur lors de la sauvegarde : {err}")

    # --- SECTION UPLOAD DE FICHIERS / IMAGES ---
    st.divider()
    st.subheader("📤 Gestion des médias (Google Drive)")

    uploaded_file = st.file_uploader(
        "Choisir une image à envoyer dans le vestiaire",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if uploaded_file is not None:
        if st.button("Uploader ce fichier sur le Drive"):
            try:
                with st.spinner("Téléversement vers Google Drive..."):
                    vestiaire_folder_id = manager.get_vestiaire_folder_id()
                    file_id, file_url = manager.upload_uploaded_file_to_drive(
                        uploaded_file, vestiaire_folder_id
                    )
                st.success(f"Fichier uploadé avec succès ! ID : {file_id}")
                st.write(f"Lien public : {file_url}")
            except Exception as up_err:
                st.error(f"Erreur lors de l'upload : {up_err}")

else:
    st.info("Aucune donnée trouvée ou chargement en cours...")