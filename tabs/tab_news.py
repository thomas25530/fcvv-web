import streamlit as st
from datetime import datetime
import re
import requests
import hashlib
from pathlib import Path
from PIL import Image as PILImage
from io import BytesIO

def render_news_tab(data, config_manager):
    st.subheader("📰 Gestion des Actualités (News)")

    if "news_list" not in st.session_state:
        raw_news = data.get("appli", {}).get("news", [])
        formatted_news = []
        for item in raw_news:
            images = item.get("images") or item.get("image") or []
            if isinstance(images, str):
                images = [images]
            formatted_news.append({
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "description": item.get("description", ""),
                "images": images if images else [""]
            })
        st.session_state.news_list = formatted_news

    # Gestion de l'état de l'aperçu modal
    if "preview_article" not in st.session_state:
        st.session_state.preview_article = None

    if st.button("➕ PUBLIER UNE NOUVELLE ACTUALITÉ", type="primary"):
        st.session_state.news_list.insert(0, {
            "title": "",
            "date": datetime.now().strftime("%d/%m/%Y"),
            "description": "",
            "images": [""]
        })
        st.rerun()

    st.divider()

    # --- SECTION APERÇU VISUEL (S'affiche en haut si demandé) ---
    if st.session_state.preview_article:
        art = st.session_state.preview_article
        with st.container(border=True):
            col_prev_head, col_prev_close = st.columns([10, 1])
            with col_prev_head:
                st.markdown("### 👁 Aperçu de l'article (Style Mobile)")
            with col_prev_close:
                if st.button("✖", key="close_preview"):
                    st.session_state.preview_article = None
                    st.rerun()

            # Rendu visuel simulant l'application Kivy
            st.markdown(f"## {art['title'] or 'Sans titre'}")
            st.caption(f"📅 {art['date']}")
            
            # Affichage de la première image avec gestion du cache URL
            valid_images = [img.strip() for img in art["images"] if img.strip()]
            if valid_images:
                first_url = valid_images[0]
                try:
                    # Cache local pour les images distantes
                    cache_dir = Path.home() / "Documents" / "FCVV" / "cache_images_admin"
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    img_path = cache_dir / f"{hashlib.md5(first_url.encode()).hexdigest()}.png"
                    
                    if not img_path.exists():
                        response = requests.get(first_url, timeout=5, verify=False)
                        if response.status_code == 200:
                            with open(img_path, "wb") as f:
                                f.write(response.content)
                    
                    if img_path.exists():
                        pil_img = PILImage.open(img_path)
                        st.image(pil_img, caption=f"Image 1 sur {len(valid_images)}" if len(valid_images) > 1 else "Image", width=350)
                except Exception:
                    st.warning("⚠️ Impossible de charger l'image depuis l'URL fournie.")
            else:
                st.info("Aucune image renseignée pour cet article.")

            st.markdown("---")
            # Description textuelle
            st.markdown(art['description'])
        st.divider()

    # --- LISTE DES ARTICLES ---
    articles_to_delete = []
    
    for idx, article in enumerate(st.session_state.news_list):
        title_display = article['title'] if article['title'] else 'Sans titre'
        with st.expander(f"Article {idx + 1} : {title_display}", expanded=True):
            
            col1, col2 = st.columns([3, 1])
            with col1:
                article["title"] = st.text_input("Titre", value=article["title"], key=f"news_title_{idx}")
            with col2:
                article["date"] = st.text_input("Date (JJ/MM/AAAA)", value=article["date"], key=f"news_date_{idx}")

            st.markdown("**Images de l'article :**")
            images_to_remove = []
            
            for img_idx, img_url in enumerate(article["images"]):
                col_img, col_btn_del = st.columns([5, 1])
                with col_img:
                    article["images"][img_idx] = st.text_input(
                        f"URL Image {img_idx + 1}", 
                        value=img_url, 
                        key=f"news_img_{idx}_{img_idx}",
                        label_visibility="collapsed"
                    )
                with col_btn_del:
                    if st.button("❌", key=f"del_img_{idx}_{img_idx}"):
                        images_to_remove.append(img_idx)

            if images_to_remove:
                for i in sorted(images_to_remove, reverse=True):
                    article["images"].pop(i)
                if not article["images"]:
                    article["images"].append("")
                st.rerun()

            if st.button("➕ Ajouter un champ image", key=f"add_img_{idx}"):
                article["images"].append("")
                st.rerun()

            article["description"] = st.text_area(
                "Contenu (supporte le balisage [b], [i], [color=#...])", 
                value=article["description"], 
                height=150, 
                key=f"news_desc_{idx}"
            )

            col_act1, col_act2, col_space = st.columns([1, 1, 4])
            with col_act1:
                if st.button("🗑 Supprimer", key=f"del_news_{idx}", type="secondary"):
                    articles_to_delete.append(idx)
            
            with col_act2:
                if st.button("👁 Aperçu", key=f"preview_news_{idx}"):
                    st.session_state.preview_article = article
                    st.rerun()

    if articles_to_delete:
        for i in sorted(articles_to_delete, reverse=True):
            st.session_state.news_list.pop(i)
        st.rerun()

    validated_list = []
    for art in st.session_state.news_list:
        title = art["title"].strip()
        date_str = art["date"].strip()
        
        if title:
            if not re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
                st.error(f"L'article '{title}' possède une date invalide (Format requis : JJ/MM/AAAA).")
            try:
                datetime.strptime(date_str, "%d/%m/%Y")
            except ValueError:
                st.error(f"La date '{date_str}' de l'article '{title}' n'existe pas.")

            clean_images = [img.strip() for img in art["images"] if img.strip()]
            validated_list.append({
                "title": title,
                "date": date_str,
                "description": art["description"],
                "images": clean_images
            })

    data["appli"]["news"] = validated_list