"""
Servidor principal de la aplicación Web Cripto Multi-Agente.
Desarrollado con FastAPI y Uvicorn.
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from services.crypto_data import (
    get_market_overview,
    get_surging_cryptos,
    get_crypto_detail,
)
from services.news_fetcher import get_crypto_news
from services.agents import run_full_agent_pipeline

# Cargar variables de entorno
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("crypto_app")

app = FastAPI(
    title="Plataforma Cripto Multi-Agente",
    description="Monitorización en tiempo real y asesoría con agentes inteligentes",
    version="1.0.0"
)

# Configuración en memoria con respaldo de variables de entorno
CURRENT_THRESHOLD = float(os.getenv("PRICE_ALERT_THRESHOLD", 5.0))


class ConfigUpdate(BaseModel):
    threshold: Optional[float] = None


@app.get("/api/config")
async def get_config():
    """Devuelve la configuración actual del sistema."""
    has_gemini_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return {
        "threshold": CURRENT_THRESHOLD,
        "has_gemini_key": has_gemini_key,
        "mode": "IA Gemini Activa" if has_gemini_key else "Modo Heurístico (Añade GEMINI_API_KEY para IA completa)"
    }


@app.post("/api/config")
async def update_config(data: ConfigUpdate):
    """Permite actualizar el umbral de subida dinámicamente desde el panel web."""
    global CURRENT_THRESHOLD
    if data.threshold is not None:
        if data.threshold < 0.1 or data.threshold > 100:
            raise HTTPException(status_code=400, detail="El umbral debe estar entre 0.1% y 100%")
        CURRENT_THRESHOLD = round(data.threshold, 2)
    return {"status": "ok", "threshold": CURRENT_THRESHOLD}


@app.get("/api/market")
async def api_market(limit: int = Query(default=40, ge=5, le=100)):
    """Devuelve la lista general de criptomonedas reales del mercado."""
    data = await get_market_overview(limit=limit)
    return {"count": len(data), "data": data}


@app.get("/api/alerts")
async def api_alerts():
    """Devuelve las criptomonedas que han superado el umbral porcentual fijado."""
    alerts = await get_surging_cryptos(threshold_percent=CURRENT_THRESHOLD)
    return {
        "threshold": CURRENT_THRESHOLD,
        "count": len(alerts),
        "data": alerts
    }


@app.get("/api/crypto/{symbol}")
async def api_crypto_detail(symbol: str):
    """Obtiene información detallada de una moneda en tiempo real."""
    detail = await get_crypto_detail(symbol)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Criptomoneda {symbol} no encontrada")
    return detail


@app.post("/api/analyze/{symbol}")
async def api_analyze_crypto(symbol: str):
    """
    Ejecuta el flujo completo de los 3 agentes para una criptomoneda:
    1. Agente 1 (Monitor): analiza la métrica técnica real.
    2. Agente 2 (Detective): investiga las noticias y causas de la subida.
    3. Agente 3 (Especialista): emite el veredicto de inversión.
    """
    clean_sym = symbol.upper().replace("USDT", "")

    # 1. Obtener datos reales de mercado
    detail = await get_crypto_detail(clean_sym)
    if not detail:
        raise HTTPException(
            status_code=404,
            detail=f"No se pudieron obtener datos de mercado en tiempo real para {clean_sym}"
        )

    # 2. Obtener noticias reales relevantes
    crypto_name = detail.get("name", clean_sym)
    news_items = await get_crypto_news(clean_sym, crypto_name)

    # 3. Orquestar el análisis de los 3 agentes
    result = await run_full_agent_pipeline(
        ticker_data=detail,
        news_items=news_items,
        threshold=CURRENT_THRESHOLD
    )

    return result


# Montar archivos estáticos para la interfaz web
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Sirve la página principal de la aplicación web."""
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"message": "La interfaz web se está preparando..."})


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Iniciando servidor en http://localhost:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
