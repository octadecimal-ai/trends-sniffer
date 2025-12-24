"""
Serwer WWW z dokumentacją
==========================
Serwer FastAPI do wyświetlania dokumentacji Markdown z folderu docs/alternative_data_research/
"""

import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc

# Ścieżka do dokumentacji
DOCS_DIR = Path(__file__).parent / "docs" / "alternative_data_research"
DEFAULT_DOC = "INDEX.md"

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Serwer dokumentacji uruchomiony")
    logger.info(f"Katalog dokumentacji: {DOCS_DIR}")
    logger.info(f"Domyślny dokument: {DEFAULT_DOC}")
    if not DOCS_DIR.exists():
        logger.warning(f"Katalog dokumentacji nie istnieje: {DOCS_DIR}")
    yield
    # Shutdown
    logger.info("Serwer dokumentacji zamykany")


# Utwórz aplikację FastAPI
app = FastAPI(
    title="Trends Sniffer - Dokumentacja",
    description="Serwer dokumentacji Alternative Data Research",
    version="1.0.0",
    lifespan=lifespan
)

# Dodaj CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Konfiguracja Markdown
MD_EXTENSIONS = [
    'codehilite',
    'fenced_code',
    'tables',
    'toc',
    'nl2br',
    'sane_lists'
]

# CSS dla lepszego wyglądu
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Trends Sniffer Docs</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        h4, h5, h6 {{
            color: #666;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        p {{
            margin-bottom: 15px;
        }}
        ul, ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            color: #e74c3c;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        pre code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            color: #666;
            font-style: italic;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ecf0f1;
            margin: 30px 0;
        }}
        .nav {{
            background: #34495e;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .nav a {{
            color: white;
            margin-right: 20px;
        }}
        .nav a:hover {{
            color: #3498db;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ecf0f1;
            text-align: center;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/">🏠 Strona główna</a>
            <a href="/docs/INDEX.md">📚 Indeks</a>
        </div>
        {content}
        <div class="footer">
            <p>Trends Sniffer - Alternative Data Research Documentation</p>
        </div>
    </div>
</body>
</html>
"""


def fix_markdown_links(content: str, current_path: str) -> str:
    """
    Naprawia linki w Markdown, aby wskazywały na endpointy serwera.
    
    Konwertuje:
    - [tekst](01_PROFESJONALNE_FINANSOWE/korelacje_aktywa.md) 
    -> [tekst](/docs/01_PROFESJONALNE_FINANSOWE/korelacje_aktywa.md)
    - [tekst](./INDEX.md) -> [tekst](/docs/INDEX.md)
    - [tekst](../INDEX.md) -> [tekst](/docs/INDEX.md)
    """
    import re
    
    # Wzorzec dla linków Markdown: [tekst](ścieżka)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    
    def replace_link(match):
        text = match.group(1)
        link = match.group(2)
        
        # Jeśli to już link HTTP/HTTPS, zostaw bez zmian
        if link.startswith('http://') or link.startswith('https://'):
            return match.group(0)
        
        # Jeśli to anchor (#), zostaw bez zmian
        if link.startswith('#'):
            return match.group(0)
        
        # Normalizuj ścieżkę
        if link.startswith('./'):
            link = link[2:]
        elif link.startswith('../'):
            # Przejdź do katalogu nadrzędnego
            current_dir = Path(current_path).parent
            link = str(current_dir / link[3:])
        
        # Jeśli link nie zaczyna się od /docs/, dodaj go
        if not link.startswith('/docs/'):
            # Usuń docs/alternative_data_research/ z początku jeśli istnieje
            if link.startswith('docs/alternative_data_research/'):
                link = link[len('docs/alternative_data_research/'):]
            link = f'/docs/{link}'
        
        return f'[{text}]({link})'
    
    return re.sub(pattern, replace_link, content)


@app.get("/")
async def root():
    """Przekierowanie do INDEX.md"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs/INDEX.md")


@app.get("/docs/{file_path:path}")
async def serve_doc(file_path: str):
    """
    Serwuje dokument Markdown jako HTML.
    
    Parametry:
    - file_path: Ścieżka do pliku Markdown względem docs/alternative_data_research/
    """
    # Normalizuj ścieżkę
    if not file_path.endswith('.md'):
        file_path = f"{file_path}.md"
    
    # Bezpieczeństwo - sprawdź czy ścieżka nie wychodzi poza DOCS_DIR
    full_path = (DOCS_DIR / file_path).resolve()
    if not str(full_path).startswith(str(DOCS_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Dostęp zabroniony")
    
    # Sprawdź czy plik istnieje
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"Dokument nie znaleziony: {file_path}")
    
    try:
        # Wczytaj plik Markdown
        with open(full_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Napraw linki
        md_content = fix_markdown_links(md_content, file_path)
        
        # Konwertuj Markdown na HTML
        html_content = markdown.markdown(
            md_content,
            extensions=MD_EXTENSIONS,
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': False
                }
            }
        )
        
        # Pobierz tytuł z pierwszego nagłówka lub nazwy pliku
        title = Path(file_path).stem.replace('_', ' ').title()
        if md_content.startswith('#'):
            first_line = md_content.split('\n')[0]
            title = first_line.replace('#', '').strip()
        
        # Zwróć HTML
        full_html = HTML_TEMPLATE.format(
            title=title,
            content=html_content
        )
        
        return HTMLResponse(content=full_html)
    
    except Exception as e:
        logger.error(f"Błąd podczas renderowania dokumentu {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")


@app.get("/api/list")
async def list_docs():
    """Zwraca listę wszystkich dostępnych dokumentów."""
    docs = []
    
    def scan_directory(directory: Path, prefix: str = ""):
        for item in sorted(directory.iterdir()):
            if item.is_file() and item.suffix == '.md':
                rel_path = str(item.relative_to(DOCS_DIR))
                docs.append({
                    "name": item.stem,
                    "path": f"/docs/{rel_path}",
                    "full_path": rel_path
                })
            elif item.is_dir():
                scan_directory(item, f"{prefix}{item.name}/")
    
    scan_directory(DOCS_DIR)
    
    return {
        "docs": docs,
        "count": len(docs)
    }



