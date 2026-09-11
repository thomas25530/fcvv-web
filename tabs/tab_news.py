import streamlit as st
from datetime import datetime
import re

def render_news_tab(data, config_manager):
    st.subheader("📰 Gestion des Actualités (News)")

    # Initialisation de la liste des news dans st.session_state si elle n'existe pas
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

    # Bouton pour ajouter un nouvel article
    if st.button("➕ PUBLIER UNE NOUVELLE ACTUALITÉ", type="primary"):
        st.session_state.news_list.insert(0, {
            "title": "",
            "date": datetime.now().strftime("%d/%m/%Y"),
            "description": "",
            "images": [""]
        })
        st.rerun()

    st.divider()

    articles_to_delete = []
    
    for idx, article in enumerate(st.session_state.news_list):
        # Correction ici : utilisation de "or" au lieu de "||"
        title_display = article['title'] if article['title'] else 'Sans titre'
        with st.expander(f"Article {idx + 1} : {title_display}", expanded=True):
            
            # 1. Titre et Date
            col1, col2 = st.columns([3, 1])
            with col1:
                article["title"] = st.text_input("Titre", value=article["title"], key=f"news_title_{idx}")
            with col2:
                article["date"] = st.text_input("Date (JJ/MM/AAAA)", value=article["date"], key=f"news_date_{idx}")

            # 2. Gestion dynamique des URL d'images
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

            # 3. Description (Contenu)
            article["description"] = st.text_area(
                "Contenu (supporte le balisage [b], [i], [color=#...])", 
                value=article["description"], 
                height=150, 
                key=f"news_desc_{idx}"
            )

            # 4. Boutons d'action
            col_act1, col_act2, col_space = st.columns([1, 1, 4])
            with col_act1:
                if st.button("🗑 Supprimer", key=f"del_news_{idx}", type="secondary"):
                    articles_to_delete.append(idx)
            
            with col_act2:
                if st.button("👁 Aperçu", key=f"preview_news_{idx}"):
                    st.info(f"**Aperçu rapide :**\n\n**{article['title']}**\n*{article['date']}*\n\n{article['description']}")

    if articles_to_delete:
        for i in sorted(articles_to_delete, reverse=True):
            st.session_state.news_list.pop(i)
        st.rerun()

    # Synchronisation vers le dictionnaire global
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