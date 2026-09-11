# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path
import sys
from datetime import datetime
import yaml
import streamlit as st

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaFileUpload


class ConfigManager:

    def __init__(self, file_id):
        self.file_id = file_id
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.creds = None
        self.service = None
        self.data = {}
        self.is_offline = False

        # Sur le cloud (Streamlit), on utilise un dossier local sécurisé dans le répertoire de l'app
        self.base_dir = Path(".") / "fcvv_cache_data"
        self.cache_path = self.base_dir / "config_cache.yaml"

    def authenticate(self):
        """Authentification Google Drive adaptée pour le web/cloud et le local"""
        
        # 1. Tentative de chargement via les Secrets Streamlit (pour le Cloud)
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "google_token" in st.secrets:
                token_info = dict(st.secrets["google_token"])
                self.creds = Credentials.from_authorized_user_info(token_info, self.scopes)
        except Exception as e:
            print(f"Secrets Streamlit non utilisés ou indisponibles : {e}")

        # 2. Sinon, tentative via le fichier token.json local
        if not self.creds or not self.creds.valid:
            token_dir = self.base_dir / "credentials"
            token_dir.mkdir(parents=True, exist_ok=True)
            token_path = token_dir / "token.json"

            if token_path.exists():
                try:
                    self.creds = Credentials.from_authorized_user_file(str(token_path), self.scopes)
                except Exception as e:
                    print(f"Erreur de lecture du token local : {e}")

        # 3. Rafraîchissement si le jeton est expiré mais possède un refresh_token
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
            except Exception as e:
                print(f"Impossible de rafraîchir le jeton : {e}")
                self.creds = None

        # 4. Si aucune accréditation valide n'a pu être trouvée
        if not self.creds or not self.creds.valid:
            raise Exception(
                "Jeton Google Drive invalide ou absent. Veuillez configurer correctement "
                "les `google_token` dans les Secrets Streamlit ou fournir un token.json valide."
            )

        self.service = build(
            "drive", "v3", credentials=self.creds, static_discovery=True
        )

    def load_config(self):
        """Télécharge le fichier YAML depuis Drive"""
        try:
            if not self.service:
                self.authenticate()

            print("Tentative de téléchargement depuis Google Drive...")
            request = self.service.files().get_media(fileId=self.file_id)
            content = request.execute()

            yaml_text = content.decode("utf-8")
            self.data = yaml.safe_load(yaml_text) or {}

            # Sauvegarde locale de cache
            try:
                self.base_dir.mkdir(parents=True, exist_ok=True)
                with open(self.cache_path, "w", encoding="utf-8") as f:
                    yaml.dump(
                        self.data,
                        f,
                        allow_unicode=True,
                        sort_keys=False,
                        default_flow_style=False,
                    )
            except Exception as cache_err:
                print(f"Impossible de mettre à jour le cache local : {cache_err}")

            self.is_offline = False
            return self.data

        except Exception as e:
            print(
                f"Mode en ligne indisponible ({e}). Tentative de chargement du cache..."
            )
            self.is_offline = True
            return self._load_local_cache()

    def _load_local_cache(self):
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.data = yaml.safe_load(f) or {}
                return self.data
            except Exception as e:
                print(f"Erreur de lecture du cache local : {e}")

        self.data = {}
        return self.data

    def save_config(self, new_data):
        """Enregistre sur Google Drive"""
        self.data = new_data
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.data,
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                )
        except Exception as local_err:
            print(f"Erreur d'écriture du cache local : {local_err}")

        try:
            if not self.service:
                self.authenticate()

            yaml_content = yaml.dump(
                new_data,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )

            fh = io.BytesIO(yaml_content.encode("utf-8"))
            media = MediaIoBaseUpload(fh, mimetype="text/yaml", resumable=True)

            self.service.files().update(
                fileId=self.file_id, media_body=media
            ).execute()

            self.is_offline = False
        except Exception as e:
            self.is_offline = True
            raise ConnectionError(
                "Modifications enregistrées UNIQUEMENT en local (Échec de la synchronisation Cloud)."
            )

    def load_yaml_from_drive(self, file_id):
        try:
            if not self.service:
                self.authenticate()
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            return yaml.safe_load(content.decode("utf-8")) or {}
        except Exception as e:
            raise e

    def update_file_on_drive(self, file_id, data):
        try:
            if not self.service:
                self.authenticate()
            yaml_content = yaml.dump(
                data,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
            fh = io.BytesIO(yaml_content.encode("utf-8"))
            media = MediaIoBaseUpload(fh, mimetype="text/yaml", resumable=True)
            self.service.files().update(
                fileId=file_id, media_body=media
            ).execute()
        except Exception as e:
            raise e

    def create_file_on_drive(self, title, data, parent_folder_id=None):
        try:
            if not self.service:
                self.authenticate()
            if not parent_folder_id:
                parent_folder_id = self.get_vestiaire_folder_id()

            if data is None:
                data = {}

            yaml_content = yaml.safe_dump(
                data,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
            fh = io.BytesIO(yaml_content.encode("utf-8"))
            media = MediaIoBaseUpload(fh, mimetype="text/yaml", resumable=True)
            file_metadata = {"name": title, "parents": [parent_folder_id]}

            file = self.service.files().create(
                body=file_metadata, media_body=media, fields="id"
            ).execute()
            file_id = file.get("id")
            self._set_file_public_reader(file_id)
            return file_id
        except Exception as e:
            raise

    def _set_file_public_reader(self, file_id):
        try:
            permission = {"type": "anyone", "role": "reader"}
            self.service.permissions().create(
                fileId=file_id, body=permission, fields="id"
            ).execute()
        except Exception as e:
            print(f"Impossible de rendre le fichier public : {e}")

    def get_or_create_folder(self, folder_name, parent_id=None):
        try:
            if not self.service:
                self.authenticate()

            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            else:
                query += " and 'root' in parents"

            results = self.service.files().list(
                q=query, spaces="drive", fields="files(id, name)"
            ).execute()
            files = results.get("files", [])

            if files:
                return files[0]["id"]
            else:
                metadata = {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                }
                if parent_id:
                    metadata["parents"] = [parent_id]
                folder = self.service.files().create(
                    body=metadata, fields="id"
                ).execute()
                return folder.get("id")
        except Exception as e:
            raise e

    def get_vestiaire_folder_id(self):
        fcvv_id = self.get_or_create_folder("FCVV")
        return self.get_or_create_folder("vestiaire", parent_id=fcvv_id)

    def upload_uploaded_file_to_drive(self, uploaded_file, parent_folder_id):
        """Remplace Tkinter : Reçoit directement le fichier uploadé depuis Streamlit (`st.file_uploader`)"""
        if not uploaded_file:
            return None, None

        if not self.service:
            self.authenticate()

        folder_name = datetime.now().strftime("%m_%Y")
        month_folder_id = self.get_or_create_folder(
            folder_name, parent_folder_id
        )

        metadata = {"name": uploaded_file.name, "parents": [month_folder_id]}

        media = MediaIoBaseUpload(
            io.BytesIO(uploaded_file.getvalue()),
            mimetype=uploaded_file.type,
            resumable=True,
        )

        file = self.service.files().create(
            body=metadata, media_body=media, fields="id,name"
        ).execute()

        file_id = file["id"]
        self._set_file_public_reader(file_id)

        url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        return file_id, url

    def get_news_folder_id(self):
        fcvv_id = self.get_or_create_folder("FCVV")
        return self.get_or_create_folder("img_actualites", parent_id=fcvv_id)

    def get_orga_folder_id(self):
        fcvv_id = self.get_or_create_folder("FCVV")
        return self.get_or_create_folder("organigramme", parent_id=fcvv_id)

    def get_boutique_folder_id(self):
        fcvv_id = self.get_or_create_folder("FCVV")
        return self.get_or_create_folder("boutique", parent_id=fcvv_id)

    def get_sponsor_folder_id(self):
        fcvv_id = self.get_or_create_folder("FCVV")
        return self.get_or_create_folder("sponsor", parent_id=fcvv_id)

    def get_vestiaire_photo_profil_folder_id(self):
        fcvv_id = self.get_or_create_folder("FCVV")
        vestiaire_id = self.get_or_create_folder("vestiaire", parent_id=fcvv_id)
        return self.get_or_create_folder(
            "photo_profil", parent_id=vestiaire_id
        )