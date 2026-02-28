import os
import re
import time
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- RÉCUPÉRATION DES CLÉS (Secrets Github) ---
CLE_API_GEMINI = os.getenv("GEMINI_API_KEY")

if CLE_API_GEMINI:
    client_gemini = genai.Client(api_key=CLE_API_GEMINI)
else:
    client_gemini = None


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
        for i in range(len(lignes) - 1):
            ligne = lignes[i].strip()
            suivante = lignes[i+1].strip()

            # Heuristique : Un terme de recherche est souvent suivi par son volume (ex: 500 k+, 1 M+)
            if ("k+" in suivante or "M+" in suivante) and 2 < len(ligne) < 50:
                if not any(w in ligne.lower() for w in blacklist):
                    if ligne not in mots_cles:
                        mots_cles.append(ligne)

        return mots_cles[:10]
    finally:
        driver.quit()


def generer_article(sujet):
    prompt = (
        f"Rédige un article d'actualité complet en HTML sur le sujet : {sujet}.\n"
        f"Le nom du site est : Articles à Gogo.\n\n"
        f"Tu dois retourner une réponse structurée exactement comme suit :\n"
        f"[DESCRIPTION] Une meta-description de 150 caractères maximum.\n"
        f"[KEYWORDS] Liste de 5-10 mots-clés séparés par des virgules.\n"
        f"[BODY]\n"
        f"Le contenu HTML de l'article (le corps), sans les balises <!DOCTYPE html>, <html>, <head> ou <body>.\n\n"
        f"L'article doit être structuré avec :\n"
        f"- <h1> pour le titre principal\n"
        f"- Une introduction captivante\n"
        f"- <h2> pour les sections principales\n"
        f"- <p> pour les paragraphes bien fournis\n"
        f"- Écris en français.\n"
        f"- Ne mets PAS de balises markdown (```html), retourne UNIQUEMENT le texte brut avec les marqueurs."
    )
    try:
        response = client_gemini.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        html = response.text
        # Nettoyer les éventuelles balises markdown
        if html.startswith("```"):
            first_newline = html.find("\n")
            if first_newline != -1:
                html = html[first_newline + 1:]
            else:
                html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        return html.strip()
    except Exception:
        return None


def generer_index(dossier, fichiers_articles):
    """Génère la page d'accueil (index.html) avec les liens vers les articles."""
    liens_articles = ""
    # On s'assure que le lien pointe vers mon_site_news/ si on est à la racine
    prefixe = "mon_site_news/" if dossier == "." else ""

    for f in fichiers_articles:
        if f in ['faq.html', 'politique-de-confidentialite.html', 'index.html']:
            continue

        titre = f.replace(".html", "").replace("_", " ").title()
        liens_articles += (
            '                <article class="article-card">\n'
            f'                    <div class="card-content">\n'
            f'                        <h2><a href="{prefixe}{f}">{titre}</a></h2>\n'
            f'                        <p>Découvrez notre analyse complète sur les dernières tendances concernant {titre.lower()}.</p>\n'
            f'                        <a href="{prefixe}{f}" class="lire-suite">Lire la suite &rarr;</a>\n'
            '                    </div>\n'
            '                </article>\n'
        )

    contenu_articles = liens_articles if liens_articles else '<div class="no-articles"><p>Aucun article pour le moment. Revenez bientôt !</p></div>'

    html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Articles à Gogo - Tendances & Actualités</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #e94560;
            --text-main: #f1f5f9;
            --text-dim: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            line-height: 1.6;
        }}
        header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 4rem 1rem;
            text-align: center;
            border-bottom: 1px solid #334155;
        }}
        header h1 {{ font-size: 3rem; color: #fff; margin-bottom: 1rem; letter-spacing: -1px; }}
        header p {{ color: var(--text-dim); font-size: 1.2rem; }}
        nav {{
            background-color: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(8px);
            position: sticky;
            top: 0;
            padding: 1rem;
            text-align: center;
            z-index: 100;
            border-bottom: 1px solid #334155;
        }}
        nav a {{ color: var(--text-main); text-decoration: none; margin: 0 1.5rem; font-weight: 600; transition: 0.3s; }}
        nav a:hover {{ color: var(--accent); }}
        main {{ max-width: 1200px; margin: 3rem auto; padding: 0 2rem; }}
        .section-title {{ font-size: 2rem; margin-bottom: 2.5rem; color: #fff; display: flex; align-items: center; gap: 1rem; }}
        .section-title::after {{ content: ""; height: 2px; background: var(--accent); flex-grow: 1; }}
        .article-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
        }}
        .article-card {{
            background: var(--card-bg);
            border-radius: 12px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
            border: 1px solid #334155;
        }}
        .article-card:hover {{ transform: translateY(-8px); box-shadow: 0 12px 24px rgba(0,0,0,0.3); border-color: var(--accent); }}
        .card-content {{ padding: 1.5rem; }}
        .article-card h2 {{ margin-bottom: 1rem; font-size: 1.4rem; }}
        .article-card h2 a {{ color: #fff; text-decoration: none; transition: 0.2s; }}
        .article-card h2 a:hover {{ color: var(--accent); }}
        .article-card p {{ color: var(--text-dim); margin-bottom: 1.5rem; font-size: 0.95rem; }}
        .lire-suite {{
            display: inline-block;
            color: var(--accent);
            text-decoration: none;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 1px;
        }}
        footer {{ background: #0b1120; padding: 4rem 1rem; text-align: center; border-top: 1px solid #334155; margin-top: 5rem; }}
        footer a {{ color: var(--text-dim); text-decoration: none; margin: 0 1rem; transition: 0.3s; }}
        footer a:hover {{ color: var(--accent); }}
        .no-articles {{ text-align: center; grid-column: 1/-1; padding: 5rem; color: var(--text-dim); }}
    </style>
    <script>
        window.va = window.va || function () {{ (window.vaq = window.vaq || []).push(arguments); }};
    </script>
    <script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
    <header>
        <h1>Articles à Gogo</h1>
        <p>Décryptage des tendances & actualités en temps réel</p>
    </header>
    <nav>
        <a href="index.html">Accueil</a>
        <a href="{prefixe}faq.html">FAQ</a>
        <a href="{prefixe}politique-de-confidentialite.html">Confidentialité</a>
    </nav>
    <main>
        <h2 class="section-title">À la Une aujourd'hui</h2>
        <div class="article-grid">
            {contenu_articles}
        </div>
    </main>
    <footer>
        <div class="footer-links">
            <a href="index.html">Accueil</a>
            <a href="{prefixe}faq.html">FAQ</a>
            <a href="{prefixe}politique-de-confidentialite.html">Confidentialité</a>
        </div>
        <p style="margin-top: 2rem; color: #475569;">&copy; 2025 Articles à Gogo. Propulsé par l'IA.</p>
    </footer>
</body>
</html>'''
    with open(os.path.join(dossier, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def sauvegarder_et_index():
    # 1. On garde les articles dans le dossier pour l'organisation
    dossier = "mon_site_news"
    if not os.path.exists(dossier): os.makedirs(dossier)
    
    tendances = scraper_google_trends()
    for t in tendances:
        nom_f = f"{t.lower().replace(' ', '_')}.html"
        chemin = os.path.join(dossier, nom_f)
        if not os.path.exists(chemin):
            reponse = generer_article(t)
            if reponse:
                # Parsing simple de la réponse structurée
                description = "Découvrez notre article sur " + t
                keywords = t + ", actualités, tendances"
                corps = reponse

                if "[DESCRIPTION]" in reponse and "[BODY]" in reponse:
                    try:
                        parts = reponse.split("[DESCRIPTION]")[1].split("[KEYWORDS]")
                        description = parts[0].strip()
                        parts = parts[1].split("[BODY]")
                        keywords = parts[0].strip()
                        corps = parts[1].strip()
                    except:
                        pass

                html_complet = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t.title()} - Articles à Gogo</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <meta property="og:title" content="{t.title()} - Articles à Gogo">
    <meta property="og:description" content="{description}">
    <meta property="og:type" content="article">
    <style>
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            line-height: 1.8;
            color: #e0e0e0;
            background-color: #0f172a;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }}
        h1 {{ color: #ffffff; font-size: 2.5rem; border-bottom: 2px solid #e94560; padding-bottom: 1rem; }}
        h2 {{ color: #e94560; margin-top: 2rem; }}
        p {{ margin-bottom: 1.5rem; text-align: justify; }}
        .nav-back {{ margin-bottom: 2rem; display: block; color: #e94560; text-decoration: none; font-weight: bold; }}
        footer {{ margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #334155; text-align: center; color: #94a3b8; }}
    </style>
    <script>
        window.va = window.va || function () {{ (window.vaq = window.vaq || []).push(arguments); }};
    </script>
    <script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
    <a href="../index.html" class="nav-back">← Retour à l'accueil</a>
    <article>
        {corps}
    </article>
    <footer>
        <p>&copy; 2025 Articles à Gogo - Tous droits réservés.</p>
    </footer>
</body>
</html>"""
                with open(chemin, "w", encoding="utf-8") as f:
                    f.write(html_complet)
    
    # 2. MISE À JOUR DE L'INDEX À LA RACINE
    fichiers = [f for f in os.listdir(dossier) if f.endswith('.html')]
    # Utiliser generer_index pour créer un bel index à la racine
    generer_index(".", fichiers)

if __name__ == "__main__":
    sauvegarder_et_index()
