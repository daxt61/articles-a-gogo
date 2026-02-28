import os
import time
from google import genai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- RÉCUPÉRATION DES CLÉS (Secrets Github) ---
CLE_API_GEMINI = os.getenv("GEMINI_API_KEY")

client_gemini = genai.Client(api_key=CLE_API_GEMINI)


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
    prompt = (
        f"Rédige un article d'actualité complet en HTML sur le sujet : {sujet}.\n"
        f"Le nom du site est : Articles à Gogo.\n\n"
        f"Tu dois UNIQUEMENT retourner le contenu HTML complet d'une page, en commençant par <!DOCTYPE html>.\n"
        f"Inclus dans le <head> :\n"
        f"- <meta charset='UTF-8'>\n"
        f"- <meta name='viewport' content='width=device-width, initial-scale=1.0'>\n"
        f"- <title> avec le sujet et le nom du site\n"
        f"- <meta name='description' content='...'> avec un résumé de 150-160 caractères\n"
        f"- <meta name='keywords' content='...'> avec des mots-clés pertinents\n"
        f"- <meta name='author' content='Articles à Gogo'>\n"
        f"- <meta name='robots' content='index, follow'>\n"
        f"- <link rel='canonical' href='#'>\n"
        f"- Des balises Open Graph (og:title, og:description, og:type=article, og:site_name)\n"
        f"- Un style CSS intégré moderne et responsive (max-width: 800px, centré, police lisible)\n\n"
        f"Dans le <body>, inclus :\n"
        f"- Un header avec un lien vers l'accueil (index.html) et le nom du site\n"
        f"- L'article avec <h1> pour le titre, <h2> pour les sous-titres, <p> pour les paragraphes\n"
        f"- Un footer avec des liens vers : Accueil (index.html), FAQ (faq.html), "
        f"Politique de confidentialité (politique-de-confidentialite.html)\n"
        f"- Écris en français.\n"
        f"- Ne mets PAS de balises markdown (```html), retourne UNIQUEMENT le HTML brut."
    )
    try:
        response = client_gemini.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        html = response.text
        # Nettoyer les éventuelles balises markdown
        if html.startswith("```html"):
            html = html[7:]
        if html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        return html.strip()
    except Exception:
        return None


def generer_index(dossier, fichiers_articles):
    """Génère la page d'accueil (index.html) avec les liens vers les articles."""
    liens_articles = ""
    for f in fichiers_articles:
        titre = f.replace(".html", "").replace("_", " ").title()
        liens_articles += (
            '                <article class="article-card">\n'
            f'                    <h2><a href="{f}">{titre}</a></h2>\n'
            f'                    <p>Découvrez notre article sur {titre.lower()}. Cliquez pour lire la suite.</p>\n'
            f'                    <a href="{f}" class="lire-suite">Lire l\'article &rarr;</a>\n'
            '                </article>\n'
        )

    contenu_articles = liens_articles if liens_articles else '<div class="no-articles"><p>Aucun article pour le moment. Revenez bientôt !</p></div>'

    html = '''<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Articles à Gogo - Actualités et tendances du moment</title>
    <meta name="description" content="Articles à Gogo : votre source d actualités et d articles sur les sujets tendance du moment en France. Restez informé avec nos articles générés quotidiennement.">
    <meta name="keywords" content="actualités, tendances, articles, news, France, articles à gogo">
    <meta name="author" content="Articles à Gogo">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="Articles à Gogo - Actualités et tendances">
    <meta property="og:description" content="Votre source d actualités et d articles sur les sujets tendance du moment en France.">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Articles à Gogo">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f6f9;
            color: #333;
            line-height: 1.6;
        }
        header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: white;
            padding: 2rem 1rem;
            text-align: center;
        }
        header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        header p { font-size: 1.1rem; opacity: 0.9; }
        nav {
            background-color: #0f3460;
            padding: 0.8rem 1rem;
            text-align: center;
        }
        nav a {
            color: #e0e0e0;
            text-decoration: none;
            margin: 0 1rem;
            font-weight: 500;
            transition: color 0.3s;
        }
        nav a:hover { color: #e94560; }
        main {
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .section-title {
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            color: #1a1a2e;
            border-bottom: 3px solid #e94560;
            padding-bottom: 0.5rem;
        }
        .article-card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .article-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }
        .article-card h2 { margin-bottom: 0.5rem; }
        .article-card h2 a { color: #16213e; text-decoration: none; }
        .article-card h2 a:hover { color: #e94560; }
        .article-card p { color: #666; margin-bottom: 1rem; }
        .lire-suite { color: #e94560; text-decoration: none; font-weight: 600; }
        .lire-suite:hover { text-decoration: underline; }
        .no-articles {
            text-align: center;
            padding: 3rem 1rem;
            color: #888;
            font-size: 1.1rem;
        }
        footer {
            background-color: #1a1a2e;
            color: #ccc;
            text-align: center;
            padding: 2rem 1rem;
            margin-top: 3rem;
        }
        footer a { color: #e94560; text-decoration: none; margin: 0 0.5rem; }
        footer a:hover { text-decoration: underline; }
        footer .footer-links { margin-bottom: 1rem; }
        @media (max-width: 600px) {
            header h1 { font-size: 1.8rem; }
            nav a { margin: 0 0.5rem; font-size: 0.9rem; }
        }
    </style>
</head>
<body>
    <header>
        <h1>Articles à Gogo</h1>
        <p>Votre source d'actualités et de tendances du moment</p>
    </header>
    <nav>
        <a href="index.html">Accueil</a>
        <a href="faq.html">FAQ</a>
        <a href="politique-de-confidentialite.html">Confidentialité</a>
    </nav>
    <main>
        <h2 class="section-title">Derniers Articles</h2>
''' + contenu_articles + '''
    </main>
    <footer>
        <div class="footer-links">
            <a href="index.html">Accueil</a> |
            <a href="faq.html">FAQ</a> |
            <a href="politique-de-confidentialite.html">Politique de confidentialité</a>
        </div>
        <p>&copy; 2025 Articles à Gogo. Tous droits réservés.</p>
    </footer>
</body>
</html>'''
    with open(os.path.join(dossier, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def sauvegarder_et_index():
    dossier = "mon_site_news"
    if not os.path.exists(dossier):
        os.makedirs(dossier)

    tendances = scraper_google_trends()
    for t in tendances:
        nom_f = f"{t.lower().replace(' ', '_')}.html"
        chemin = os.path.join(dossier, nom_f)
        if not os.path.exists(chemin):
            contenu = generer_article(t)
            if contenu:
                with open(chemin, "w", encoding="utf-8") as f:
                    f.write(contenu)

    # Mise à jour de l'index
    fichiers = [f for f in os.listdir(dossier) if f.endswith('.html') and f not in ('index.html', 'faq.html', 'politique-de-confidentialite.html')]
    generer_index(dossier, fichiers)


if __name__ == "__main__":
    sauvegarder_et_index()
