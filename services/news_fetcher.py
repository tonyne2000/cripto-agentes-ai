"""
Servicio de obtención de noticias y contexto en tiempo real.
Consulta fuentes reales como Google News RSS y medios especializados de criptomonedas.
"""

from typing import List, Dict
import urllib.parse
import feedparser
import asyncio
import logging

logger = logging.getLogger(__name__)


def clean_news_item(entry: dict, source_label: str) -> dict:
    """Normaliza una entrada de noticias de RSS."""
    title = entry.get("title", "Sin título").strip()
    link = entry.get("link", "")
    published = entry.get("published", entry.get("updated", ""))
    summary = entry.get("summary", "")

    # Limpiar posibles etiquetas HTML del resumen si existen
    if summary:
        import re
        summary = re.sub(r"<[^>]+>", "", summary).strip()
        # Limitar longitud para no saturar el prompt
        if len(summary) > 280:
            summary = summary[:277] + "..."

    return {
        "title": title,
        "source": source_label,
        "link": link,
        "published": published,
        "snippet": summary or title,
    }


def fetch_google_news_sync(query: str, lang: str = "es") -> List[dict]:
    """Descarga noticias de Google News mediante RSS de forma sincrónica."""
    encoded_query = urllib.parse.quote(query)
    if lang == "es":
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=es&gl=ES&ceid=ES:es"
    else:
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:6]:
            results.append(clean_news_item(entry, "Google Noticias"))
        return results
    except Exception as e:
        logger.warning(f"Error consultando Google News ({query}): {e}")
        return []


def fetch_crypto_rss_sync(feed_url: str, source_label: str, keywords: List[str]) -> List[dict]:
    """Descarga un feed de medios cripto y filtra por palabras clave."""
    try:
        feed = feedparser.parse(feed_url)
        results = []
        lower_keywords = [k.lower() for k in keywords]

        for entry in feed.entries:
            text_to_check = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
            if any(k in text_to_check for k in lower_keywords):
                results.append(clean_news_item(entry, source_label))
                if len(results) >= 4:
                    break
        return results
    except Exception as e:
        logger.warning(f"Error consultando {source_label}: {e}")
        return []


async def get_crypto_news(symbol: str, name: str) -> List[Dict]:
    """
    Obtiene noticias frescas relevantes para una criptomoneda específica,
    combinando búsqueda en español y medios internacionales.
    """
    loop = asyncio.get_event_loop()

    # Búsqueda en Google News en español y en inglés
    query_es = f"{name} {symbol} criptomoneda"
    query_en = f"{name} {symbol} crypto news"

    # Ejecutar consultas en hilos para no bloquear el bucle de eventos
    task_gnews_es = loop.run_in_executor(None, fetch_google_news_sync, query_es, "es")
    task_gnews_en = loop.run_in_executor(None, fetch_google_news_sync, query_en, "en")
    task_cointelegraph = loop.run_in_executor(
        None,
        fetch_crypto_rss_sync,
        "https://cointelegraph.com/rss",
        "Cointelegraph",
        [symbol, name]
    )

    results = await asyncio.gather(
        task_gnews_es,
        task_gnews_en,
        task_cointelegraph,
        return_exceptions=True
    )

    combined_news = []
    seen_titles = set()

    for item_list in results:
        if isinstance(item_list, list):
            for news in item_list:
                # Deduplicar por similitud de título
                normalized_title = news["title"].lower()[:40]
                if normalized_title not in seen_titles:
                    seen_titles.add(normalized_title)
                    combined_news.append(news)

    # Devolver las 6 noticias más relevantes
    return combined_news[:6]
