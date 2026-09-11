# -*- coding: utf-8 -*-
import os
import yaml
import io
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from googleapiclient.http import MediaFileUpload
from tkinter import filedialog
from datetime import datetime


def get_path(relative_path):
    """ Gestion des chemins compatible PyInstaller _internal """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class ConfigManager:
    def __init__(self, file_id):
        self.file_id = file_id
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.creds = None
        self.service = None
        self.data = {}
        self.is_offline = False  # <--- Ajouté pour indiquer le mode à main.py

        # Définition des chemins vers les Documents
        self.base_dir = Path.home() / "Documents" / "FCVV"
        self.cache_path = self.base_dir / "config_cache.yaml"

    def authenticate(self):
        # Ta méthode exacte d'origine sans aucune modification de logique interne
        token_dir = self.base_dir / "credentials"
        token_dir.mkdir(parents=True, exist_ok=True)
        token_path = token_dir / "token.json"
        cred_path = get_path("credentials/credentials.json")

        if token_path.exists():
            self.creds = Credentials.from_authorized_user_file(str(token_path), self.scopes)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Impossible de rafraîchir le jeton : {e}. Re-connexion nécessaire.")
                    self.creds = None 
            
            if not self.creds:
                if not os.path.exists(cred_path):
                    raise FileNotFoundError(f"Fichier credentials.json introuvable : {cred_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(cred_path, self.scopes)
                self.creds = flow.run_local_server(
                    port=0, 
                    access_type='offline', 
                    prompt='consent'
                )
            
            with open(token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('drive', 'v3', credentials=self.creds, static_discovery=True)

    def load_config(self):
        """Télécharge le fichier YAML depuis Drive, sinon bascule sur le cache local"""
        try:
            # Si pas d'internet ou pas de token au 1er lancement, authenticate() va lever une exception
            if not self.service: 
                self.authenticate()
        
            print("Tentative de téléchargement depuis Google Drive...")
            request = self.service.files().get_media(fileId=self.file_id)
            content = request.execute()
            
            yaml_text = content.decode('utf-8')
            self.data = yaml.safe_load(yaml_text) or {}
            
            # --- Sauvegarde locale de sécurité pour les prochains démarrages hors-ligne ---
            try:
                self.base_dir.mkdir(parents=True, exist_ok=True)
                with open(self.cache_path, "w", encoding="utf-8") as f:
                    yaml.dump(self.data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            except Exception as cache_err:
                print(f"Impossible de mettre à jour le cache local : {cache_err}")

            self.is_offline = False
            return self.data
            
        except Exception as e:
            # Si quoi que ce soit échoue (Réseau, Authentification, API Google...), on attrape l'erreur ici
            print(f"Mode en ligne indisponible ({e}). Tentative de chargement du cache...")
            self.is_offline = True
            return self._load_local_cache()

    def _load_local_cache(self):
        """Charge le fichier local si disponible, sinon laisse self.data vide"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.data = yaml.safe_load(f) or {}
                print("Données chargées depuis le cache local avec succès.")
                return self.data
            except Exception as e:
                print(f"Erreur de lecture du cache local : {e}")
        
        # Si aucun cache n'existe (1er lancement sans réseau), on s'assure de retourner un dico vide
        self.data = {}
        return self.data

    def save_config(self, new_data):
        """Enregistre d'abord localement par sécurité, puis tente d'envoyer sur Google Drive"""
        self.data = new_data
        
        # 1. Sauvegarde de sécurité locale (Fonctionne toujours, même sans réseau)
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w", encoding="utf-8") as f:
                yaml.dump(self.data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
            print("Données sauvegardées en local (Cache mis à jour).")
        except Exception as local_err:
            print(f"Erreur d'écriture du cache local : {local_err}")

        # 2. Envoi sur Google Drive
        try:
            if not self.service:
                self.authenticate()

            yaml_content = yaml.dump(
                new_data, 
                allow_unicode=True, 
                sort_keys=False, 
                default_flow_style=False
            )
            
            fh = io.BytesIO(yaml_content.encode('utf-8'))
            media = MediaIoBaseUpload(fh, mimetype='text/yaml', resumable=True)
            
            self.service.files().update(
                fileId=self.file_id, 
                media_body=media
            ).execute()
            
            self.is_offline = False
            print("Sauvegarde réussie sur Google Drive.")
            
        except Exception as e:
            self.is_offline = True
            print(f"Erreur lors de la mise à jour sur Google Drive : {e}")
            # On relance une erreur propre pour que l'interface Tkinter sache qu'elle doit afficher une alerte
            raise ConnectionError("Modifications enregistrées UNIQUEMENT en local (Échec de la synchronisation Cloud).")
        
        
    def load_yaml_from_drive(self, file_id):
        """Charge un fichier YAML spécifique depuis Drive via son file_id"""
        try:
            if not self.service:
                self.authenticate()
            
            # Téléchargement
            request = self.service.files().get_media(fileId=file_id)
            content = request.execute()
            
            return yaml.safe_load(content.decode('utf-8')) or {}
            
        except Exception as e:
            print(f"Erreur lors du chargement du fichier {file_id} : {e}")
            raise e

    def update_file_on_drive(self, file_id, data):
        """Met à jour un fichier YAML spécifique sur Drive"""
        try:
            if not self.service:
                self.authenticate()
                
            yaml_content = yaml.dump(
                data, 
                allow_unicode=True, 
                sort_keys=False, 
                default_flow_style=False
            )
            
            fh = io.BytesIO(yaml_content.encode('utf-8'))
            media = MediaIoBaseUpload(fh, mimetype='text/yaml', resumable=True)
            
            self.service.files().update(
                fileId=file_id, 
                media_body=media
            ).execute()
            
            print(f"Fichier {file_id} mis à jour avec succès.")
            
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier {file_id} : {e}")
            raise e
        
    def create_file_on_drive(self, title, data, parent_folder_id=None):
        """
        Crée un nouveau fichier YAML dans FCVV/vestiaire sur Google Drive
        et retourne son file_id.
        """
        try:
            if not self.service:
                self.authenticate()
    
            # 1. Déterminer l'emplacement
            # Priorité au parent_folder_id passé, sinon FCVV/vestiaire
            if not parent_folder_id:
                parent_folder_id = self.get_vestiaire_folder_id()
    
            # 2. Sécuriser et normaliser la structure des données
            # Cela évite qu'une valeur None produise :
            # groupes:
            # au lieu de :
            # groupes: {}
    
            if data is None:
                data = {}
    
            if not isinstance(data, dict):
                raise ValueError(
                    "Les données du fichier YAML doivent être un dictionnaire."
                )
    
            # Valeurs par défaut obligatoires
            if data.get("chat_admin_only") is None:
                data["chat_admin_only"] = False
    
            if data.get("calendrier_saison") is None:
                data["calendrier_saison"] = {}
    
            if data.get("documents") is None:
                data["documents"] = []
    
            if data.get("tous_les_joueurs") is None:
                data["tous_les_joueurs"] = []
    
            if data.get("groupes") is None:
                data["groupes"] = {}
    
            # 3. Conversion des données en YAML
            yaml_content = yaml.safe_dump(
                data,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
    
            # 4. Préparation du fichier à envoyer sur Google Drive
            fh = io.BytesIO(yaml_content.encode("utf-8"))
    
            media = MediaIoBaseUpload(
                fh,
                mimetype="text/yaml",
                resumable=True
            )
    
            # 5. Métadonnées du fichier avec le dossier parent
            file_metadata = {
                "name": title,
                "parents": [parent_folder_id],
            }
    
            # 6. Création du fichier sur Google Drive
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id",
            ).execute()
    
            file_id = file.get("id")
    
            print(
                f"Fichier '{title}' créé avec succès "
                f"dans le dossier {parent_folder_id} "
                f"(ID: {file_id})."
            )
    
            # 7. Rendre le fichier accessible à toute personne ayant le lien
            # (lecture uniquement)
            self._set_file_public_reader(file_id)
    
            return file_id
    
        except Exception as e:
            print(
                f"Erreur lors de la création du fichier sur Drive : {e}"
            )
            raise

    def _set_file_public_reader(self, file_id):
        """Donne un accès en lecture à 'tout le monde avec le lien' (nécessaire pour le partage)"""
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader',
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id',
            ).execute()
            print(f"Permission publique accordée pour le fichier {file_id}.")
        except Exception as e:
            print(f"Impossible de rendre le fichier public : {e}")
    
    def get_or_create_folder(self, folder_name, parent_id=None):
        """Cherche ou crée un dossier et retourne son ID."""
        try:
            # 1. Vérification de l'authentification
            if not self.service:
                self.authenticate()

            # 2. Construction de la requête de recherche
            # On ajoute explicitement 'trashed = false' pour ne pas récupérer des dossiers supprimés
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            else:
                # Si aucun parent n'est spécifié, on limite la recherche à la racine
                query += " and 'root' in parents"

            results = self.service.files().list(
                q=query, 
                spaces='drive', 
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])

            if files:
                return files[0]['id']
            else:
                # 3. Création du dossier
                metadata = {
                    'name': folder_name, 
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    metadata['parents'] = [parent_id]
                
                folder = self.service.files().create(
                    body=metadata, 
                    fields='id'
                ).execute()
                
                print(f"Dossier '{folder_name}' créé avec succès.")
                return folder.get('id')

        except Exception as e:
            print(f"Erreur lors de la récupération ou création du dossier '{folder_name}': {e}")
            raise e

    def get_vestiaire_folder_id(self):
        """Retourne l'ID du dossier FCVV/vestiaire"""
        # 1. Dossier FCVV racine
        fcvv_id = self.get_or_create_folder("FCVV")
        # 2. Dossier vestiaire dans FCVV
        vestiaire_id = self.get_or_create_folder("vestiaire", parent_id=fcvv_id)
        return vestiaire_id
    
    def upload_image_and_get_url(self, parent_folder_id):
        """
        Ouvre l'explorateur Windows,
        upload une image dans le dossier Google Drive indiqué,
        crée automatiquement MM_YYYY si besoin,
        rend l'image publique,
        retourne (file_id, url).
        """
    
        filepath = filedialog.askopenfilename(
            title="Choisir une image",
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.gif *.webp"),
                ("Tous les fichiers", "*.*")
            ]
        )
    
        if not filepath:
            return None, None
    
        if not self.service:
            self.authenticate()
    
        folder_name = datetime.now().strftime("%m_%Y")
    
        month_folder_id = self.get_or_create_folder(
            folder_name,
            parent_folder_id
        )
    
        filename = os.path.basename(filepath)
    
        metadata = {
            "name": filename,
            "parents": [month_folder_id]
        }
    
        media = MediaFileUpload(
            filepath,
            resumable=True
        )
    
        file = self.service.files().create(
            body=metadata,
            media_body=media,
            fields="id,name"
        ).execute()
    
        file_id = file["id"]
    
        self._set_file_public_reader(file_id)
    
        url = (
            f"https://drive.usercontent.google.com/"
            f"download?id={file_id}&export=download"
        )
    
        return file_id, url
        
    def upload_image_to_entry(
        self,
        parent_folder_id,
        target_var,
        store_file_id_only=False
    ):
        try:
    
            file_id, url = self.upload_image_and_get_url(
                parent_folder_id
            )
    
            if not file_id:
                return
    
            if store_file_id_only:
                target_var.set(file_id)
            else:
                target_var.set(url)
    
        except Exception as e:
            print(e)
    
    def get_news_folder_id(self):

        fcvv_id = self.get_or_create_folder("FCVV")
    
        return self.get_or_create_folder(
            "img_actualites",
            parent_id=fcvv_id
        )
        
    def get_orga_folder_id(self):

        fcvv_id = self.get_or_create_folder("FCVV")
    
        return self.get_or_create_folder(
            "organigramme",
            parent_id=fcvv_id
        )
        
    def upload_orga_photo(self, target_entry):

        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp")
            ]
        )
    
        if not file_path:
            return
    
        file_id = self.upload_file_to_drive(
            file_path=file_path,
            parent_folder_id=self.get_orga_folder_id()
        )
    
        if file_id:
    
            target_entry.delete(0, tk.END)
            target_entry.insert(0, file_id)
    
            return file_id
    
        return None
    
    def get_boutique_folder_id(self):
    
        fcvv_id = self.get_or_create_folder("FCVV")
    
        return self.get_or_create_folder(
            "boutique",
            parent_id=fcvv_id
        )
        
    def get_sponsor_folder_id(self):

        fcvv_id = self.get_or_create_folder("FCVV")
    
        return self.get_or_create_folder(
            "sponsor",
            parent_id=fcvv_id
        )
        
    def get_vestiaire_photo_profil_folder_id(self):

        fcvv_id = self.get_or_create_folder("FCVV")
    
        vestiaire_id = self.get_or_create_folder(
            "vestiaire",
            parent_id=fcvv_id
        )
    
        return self.get_or_create_folder(
            "photo_profil",
            parent_id=vestiaire_id
        )
