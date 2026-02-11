import streamlit as st
from PIL import Image
import requests
import re

st.set_page_config(page_title="SDXL Ultimate Inspector", layout="wide")
st.title("🕵️ SDXL Inspector : Pony, Illustrious & Co.")

# --- BASE DE CONNAISSANCE (Signatures) ---
KNOWN_SIGNATURES = {
    "PONY": {
        "keywords": ["score_99", "score_97", "score_96", "source_pony", "pony v6"],
        "hashes": ["67ab2fd8", "c356f932"], # Hashes connus de Pony V6
        "label": "🐴 PONY DIFFUSION",
        "desc": "Détecté via les tags de score (score_99...) obligatoires sur Pony.",
        "color": "red"
    },
    "ILLUSTRIOUS": {
        "keywords": ["illustrious", "illustration", "noobai"], # Illustrious est plus subtil
        "hashes": ["08719f9e", "a5180017"],
        "label": "🖌️ ILLUSTRIOUS XL",
        "desc": "Détecté via le nom ou les tags spécifiques.",
        "color": "blue"
    },
    "ANIMAGINE": {
        "keywords": ["animagine", "censor_nipples"],
        "hashes": ["e3c47aed"],
        "label": "🦜 ANIMAGINE XL",
        "desc": "Style anime spécifique.",
        "color": "green"
    }
}

# --- FONCTIONS ---
def analyze_model_signature(text_params, full_info):
    """Analyse le texte pour trouver Pony ou Illustrious"""
    detected = []
    
    text_lower = text_params.lower() if text_params else ""
    
    # 1. On cherche dans le texte (Prompt)
    for key, data in KNOWN_SIGNATURES.items():
        # Vérif mots clés
        for kw in data["keywords"]:
            if kw in text_lower:
                detected.append(data)
                break # On a trouvé une preuve pour ce modèle, on passe au suivant
    
    # 2. On cherche dans le Hash (plus fiable)
    current_hash = ""
    if "Model hash:" in text_params:
        parts = text_params.split("Model hash:")
        if len(parts) > 1:
            current_hash = parts[1].strip().split(",")[0][:8] # On prend les 8 premiers caractères
    
    for key, data in KNOWN_SIGNATURES.items():
        if current_hash in data["hashes"]:
            # On vérifie qu'on ne l'a pas déjà ajouté via les mots clés
            if data not in detected:
                detected.append(data)

    return detected, current_hash

# --- INTERFACE ---
uploaded_file = st.file_uploader("Chargez une image (PNG avec métadonnées)", type=["png", "jpg", "jpeg", "webp"])

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert('RGB')
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.image(image, caption="Image analysée", use_container_width=True)

    with col2:
        st.subheader("🔍 Analyse Approfondie")
        
        # Récupération des paramètres
        params = ""
        if image.info and 'parameters' in image.info:
            params = image.info['parameters']
        
        if params:
            # --- LE DÉTECTEUR PONY / ILLUSTRIOUS ---
            signatures, found_hash = analyze_model_signature(params, image.info)
            
            if signatures:
                for sig in signatures:
                    if sig["color"] == "red":
                        st.error(f"### {sig['label']}") # Rouge pour Pony
                    elif sig["color"] == "blue":
                        st.info(f"### {sig['label']}") # Bleu pour Illustrious
                    else:
                        st.success(f"### {sig['label']}")
                    
                    st.write(f"*{sig['desc']}*")
            else:
                st.warning("Type de modèle spécifique non détecté (Standard SDXL ou inconnu).")
                if "score_" in params:
                    st.write("Note: J'ai vu des 'score_', ça ressemble beaucoup à du Pony/NovelAI !")

            st.divider()
            
            # --- INFOS TECHNIQUES ---
            st.write(f"**Hash détecté :** `{found_hash if found_hash else 'Inconnu'}`")
            
            # Bouton pour voir le prompt brut
            with st.expander("Voir le prompt complet"):
                st.text(params)

        else:
            st.error("❌ Pas de métadonnées.")
            st.info("Sans le texte caché, impossible de distinguer Pony d'Illustrious (visuellement trop proches).")

        st.divider()
        
        # --- PARTIE IA VISUELLE (Pour confirmer si c'est de l'anime) ---
        if st.button("Vérification visuelle (IA)"):
            try:
                from transformers import pipeline
                with st.spinner("Analyse visuelle..."):
                    classifier = pipeline("image-classification", model="Organika/sdxl-detector", device=-1)
                    results = classifier(image)
                    
                    # On affiche juste le top 1
                    top = results[0]
                    st.metric(label="Style Visuel", value=top['label'], delta=f"{top['score']*100:.1f}%")
                    
            except Exception as e:
                st.error("Erreur IA (voir logs)")

