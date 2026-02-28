import os
import time
from google import genai
import anthropic
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- RÉCUPÉRATION DES CLÉS (Secrets Github) ---
CLE_API_GEMINI = os.getenv("GEMINI_API_KEY")
CLE_API_CLAUDE = os.getenv("CLAUDE_API_KEY")

client_gemini = genai.Client(api_key=CLE_API_GEMINI)
client_claude = anthropic.Anthropic(api_key=CLE_API_CLAUDE)

def scraper_google_trends():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://trends.google.com/trends/trendingsearches/daily?geo=FR&hl=fr")
        time.sleep(15)
        lignes = driver.find_element(By.TAG_NAME, "body").text.split('\n')
        
        blacklist = ['trends', 'accueil', 'explorer', 'démarrée', 'volume', 'composition', 'actif', 'il y a', 'heures', 'france']
        
        mots_cles = []
        for ligne in lignes[25:]:
            ligne = ligne.strip()
            if 5 < len(ligne) < 35 and not any(w in ligne.lower() for w in blacklist) and not any(c.isdigit() for c in ligne):
                if ligne not in mots_cles:
                    mots_cles.append(ligne)
        return mots_cles[:3]
    finally:
        driver.quit()

def generer_article(sujet):
    prompt = f"Rédige un article d'actualité en HTML (<h1>, <h2>, <p>) sur : {sujet}. Nom du site : Articles à Gogo."
    try:
        response = client_gemini.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except:
        return None # Fallback Claude possible ici si tu configures les crédits

def sauvegarder_et_index():
    dossier = "mon_site_news"
    if not os.path.exists(dossier): os.makedirs(dossier)
    
    tendances = scraper_google_trends()
    for t in tendances:
        nom_f = f"{t.lower().replace(' ', '_')}.html"
        chemin = os.path.join(dossier, nom_f)
        if not os.path.exists(chemin):
            contenu = generer_article(t)
            if contenu:
                with open(chemin, "w", encoding="utf-8") as f:
                    f.write(f"<html><head><meta charset='UTF-8'><title>{t}</title></head><body>{contenu}</body></html>")
    
    # Mise à jour de l'index
    fichiers = [f for f in os.listdir(dossier) if f.endswith('.html') and f != 'index.html']
    liens = "".join([f'<li><a href="{f}">{f.replace(".html","").upper()}</a></li>' for f in fichiers])
    with open(os.path.join(dossier, "index.html"), "w", encoding="utf-8") as f:
        f.write(f"<html><body><h1>Articles à Gogo</h1><ul>{liens}</ul></body></html>")

if __name__ == "__main__":
    sauvegarder_et_index()
