"""
Módulo de agentes de Inteligencia Artificial para el análisis de criptomonedas.

Agente 1: Monitor de Mercado (Valida subidas y métricas reales)
Agente 2: Investigador / Detective (Averigua por qué ha subido con noticias y contexto)
Agente 3: Especialista en Inversión (Emite veredicto y recomendación de compra)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


def get_gemini_client():
    """Inicializa el cliente de Gemini si la clave está disponible."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.error(f"Error al inicializar el cliente de Gemini: {e}")
        return None


def generate_with_gemini(client, prompt: str) -> Optional[dict]:
    """
    Ejecuta la generación con Gemini probando modelos modernos con tolerancia a fallos.
    """
    models_to_try = ["gemini-3.8-flash", "gemini-3.5-flash", "gemini-2.5-flash-lite"]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            text_resp = response.text.strip()
            if text_resp.startswith("```"):
                text_resp = text_resp.split("```")[1]
                if text_resp.startswith("json"):
                    text_resp = text_resp[4:]
            return json.loads(text_resp)
        except Exception as err:
            logger.warning(f"Intento con modelo {model_name} falló: {err}")
            continue
    return None


# =========================================================================
# AGENTE 1: MONITOR DE MERCADO (CENTINELA)
# =========================================================================
def run_agent_1_monitor(ticker_data: Dict[str, Any], threshold: float = 5.0) -> Dict[str, Any]:
    """
    Agente 1 analiza las métricas frías y reales del mercado para determinar si
    la subida es relevante y qué características técnicas presenta.
    """
    symbol = ticker_data.get("symbol", "")
    name = ticker_data.get("name", symbol)
    change_24h = ticker_data.get("change_24h", 0.0)
    current_price = ticker_data.get("price", 0.0)
    high_24h = ticker_data.get("high_24h", 0.0)
    low_24h = ticker_data.get("low_24h", 0.0)
    volume_usdt = ticker_data.get("volume_usdt", 0.0)

    # Calcular distancia al máximo del día
    if high_24h > 0:
        distance_to_high = round(((high_24h - current_price) / high_24h) * 100, 2)
    else:
        distance_to_high = 0.0

    # Rango de oscilación del día
    range_percent = 0.0
    if low_24h > 0:
        range_percent = round(((high_24h - low_24h) / low_24h) * 100, 2)

    is_alert = change_24h >= threshold

    # Diagnóstico del vigilante
    if change_24h >= 20:
        volatility_level = "Extrema"
        status_msg = f"¡Subida parabólica del +{change_24h}%! Movimiento con alta fuerza compradora."
    elif change_24h >= 10:
        volatility_level = "Alta"
        status_msg = f"Fuerte repunte del +{change_24h}%. Ruptura de rango confirmada."
    elif change_24h >= threshold:
        volatility_level = "Moderada"
        status_msg = f"Crecimiento sólido del +{change_24h}%, superando el umbral del {threshold}%."
    else:
        volatility_level = "Normal"
        status_msg = f"Comportamiento estándar ({change_24h}%). No supera el filtro de alarma."

    return {
        "agent": "Agente 1: Monitor de Mercado",
        "symbol": symbol,
        "name": name,
        "is_alert": is_alert,
        "change_24h": change_24h,
        "price_formatted": ticker_data.get("price_formatted", f"${current_price}"),
        "volume_usdt_formatted": f"${volume_usdt:,.0f}",
        "distance_to_high_percent": distance_to_high,
        "daily_range_percent": range_percent,
        "volatility_level": volatility_level,
        "summary": status_msg,
    }


# =========================================================================
# AGENTE 2: INVESTIGADOR / DETECTIVE DE CAUSAS
# =========================================================================
async def run_agent_2_investigator(
    crypto_info: Dict[str, Any],
    news_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Agente 2 investiga las noticias y catalizadores del repunte de la criptomoneda.
    """
    symbol = crypto_info.get("symbol", "")
    name = crypto_info.get("name", symbol)
    change_24h = crypto_info.get("change_24h", 0.0)

    client = get_gemini_client()

    # Si hay clave de Gemini disponible, consultamos la IA para el análisis profundo
    if client:
        try:
            noticias_texto = ""
            for i, n in enumerate(news_items, 1):
                noticias_texto += f"{i}. [{n.get('source')}] {n.get('title')}: {n.get('snippet')}\n"

            prompt = f"""
Eres el "Agente Detective de Criptomonedas", especializado en investigar las causas reales de los movimientos del mercado cripto.
Habla en español de España, de forma clara y sin tecnicismos innecesarios.

DATOS DE LA MONEDA:
- Criptomoneda: {name} ({symbol})
- Subida en 24 horas: +{change_24h}%
- Precio actual: {crypto_info.get('price_formatted')}
- Volumen negociado hoy: {crypto_info.get('volume_usdt_formatted')}

NOTICIAS Y TITULARES RECIENTES DETECTADOS:
{noticias_texto if noticias_texto else "No se han detectado noticias explícitas en los últimos minutos (posible movimiento puramente especulativo o en redes sociales)."}

TU MISIÓN:
1. Explica el motivo principal de por qué ha subido esta criptomoneda.
2. Identifica si es por noticias fundamentales (adopción, actualizaciones, alianzas), compras de grandes inversores (ballenas), o especulación pura / memecoins.
3. Evalúa el estado del sentimiento social.

Devuelve ÚNICAMENTE un objeto JSON válido con este formato exacto:
{{
  "factor_principal": "Breve frase resumen del motivo principal (ej: Actualización de red y adopción institucional)",
  "explicacion_causas": "Explicación en 2 párrafos fáciles de entender sobre qué ha pasado y por qué sube el precio.",
  "sentimiento_social": "Eufórico / Muy Positivo / Optimista Moderado / Especulativo",
  "tipo_catalizador": "Fundamental / Técnico / Especulativo / Regulatorio",
  "fuentes_consultadas": ["Nombre de fuente 1", "Nombre de fuente 2"]
}}
"""
            data = generate_with_gemini(client, prompt)
            if data:
                data["agent"] = "Agente 2: Investigador de Noticias y Causas"
                data["ai_powered"] = True
                return data
        except Exception as e:
            logger.warning(f"Fallo en llamada a Gemini para Agente 2 ({e}), usando motor heurístico.")

    # Motor heurístico si no hay clave de Gemini o si falló la API
    top_news_titles = [n.get("title", "") for n in news_items[:3]]
    noticias_str = ", ".join(top_news_titles) if top_news_titles else "flujo de liquidez directo en exchanges"

    factor = "Fuerte entrada de volumen de compra y actividad reciente"
    tipo = "Técnico / Especulativo"
    sentimiento = "Muy Optimista"

    if any("etf" in t.lower() or "fondo" in t.lower() for t in top_news_titles):
        factor = "Interés institucional y noticias sobre fondos cotizados / ETFs"
        tipo = "Fundamental"
        sentimiento = "Eufórico"
    elif any("actualiz" in t.lower() or "upgrade" in t.lower() or "mainnet" in t.lower() for t in top_news_titles):
        factor = "Avances tecnológicos y novedades en el ecosistema de la red"
        tipo = "Fundamental"
        sentimiento = "Muy Positivo"

    return {
        "agent": "Agente 2: Investigador de Noticias y Causas",
        "factor_principal": factor,
        "explicacion_causas": (
            f"El proyecto {name} ({symbol}) ha experimentado un fuerte impulso alcista del +{change_24h}% en las últimas 24 horas. "
            f"Este movimiento coincide con una intensa actividad en el mercado y las siguientes noticias destacadas: {noticias_str}. "
            "El volumen de negociación ha respaldado la subida, atrayendo a nuevos compradores que buscan aprovechar el impulso."
        ),
        "sentimiento_social": sentimiento,
        "tipo_catalizador": tipo,
        "fuentes_consultadas": [n.get("source", "Google News") for n in news_items[:3]],
        "ai_powered": False,
        "note": "Análisis preliminar heurístico. Puedes añadir tu GEMINI_API_KEY en el archivo .env para habilitar el análisis de IA profunda."
    }


# =========================================================================
# AGENTE 3: ESPECIALISTA EN INVERSIÓN (VEREDICTO FINAL)
# =========================================================================
async def run_agent_3_specialist(
    crypto_info: Dict[str, Any],
    agent1_data: Dict[str, Any],
    agent2_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agente 3 combina las métricas de mercado y las conclusiones del detective
    para emitir un veredicto de inversión profesional y comprensible.
    """
    symbol = crypto_info.get("symbol", "")
    name = crypto_info.get("name", symbol)
    change_24h = crypto_info.get("change_24h", 0.0)
    distance_to_high = agent1_data.get("distance_to_high_percent", 0.0)
    factor = agent2_data.get("factor_principal", "")
    explicacion = agent2_data.get("explicacion_causas", "")

    client = get_gemini_client()

    if client:
        try:
            prompt = f"""
Eres un "Asesor Especialista en Criptomonedas".
Tu objetivo es dar un veredicto honesto, profesional y claro a un usuario que se pregunta: "¿Debería invertir o comprar esta moneda ahora mismo?".
Habla en español de España, de forma clara, directa y sin tecnicismos innecesarios.

INFORMACIÓN DISPONIBLE:
- Criptomoneda: {name} ({symbol})
- Precio actual: {crypto_info.get('price_formatted')}
- Subida en 24h: +{change_24h}%
- Distancia al máximo del día: {distance_to_high}% por debajo del máximo
- Causa identificada por el Detective: {factor}
- Contexto de las noticias: {explicacion}

CRITERIOS DE JUICIO:
- Si ya ha subido demasiado (por ejemplo más de un 15-20%) sin descanso, entrar ahora puede ser peligroso (riesgo de FOMO y corrección).
- Si la subida tiene una base fundamental sólida y aún no está hiper-extendida, puede ser buena oportunidad.
- Da un veredicto tajante y una estrategia de entrada sensata.

Devuelve ÚNICAMENTE un objeto JSON válido con este formato:
{{
  "veredicto": "COMPRA RECOMENDADA" | "COMPRAR CON CAUTELA" | "ESPERAR CORRECCIÓN" | "EVITAR POR ALTO RIESGO",
  "nivel_riesgo": "Bajo" | "Medio" | "Alto" | "Extremo",
  "etiqueta_color": "verde" | "amarillo" | "rojo",
  "puntos_a_favor": ["Razón a favor 1", "Razón a favor 2"],
  "riesgos_principales": ["Riesgo 1", "Riesgo 2"],
  "estrategia_sugerida": "Consejo práctico sobre cómo proceder (por ejemplo: esperar a que baje a X nivel o entrar en pequeñas fracciones).",
  "consejo_final": "Conclusión en tono cercano explicando de forma transparente si merece la pena entrar hoy o no."
}}
"""
            data = generate_with_gemini(client, prompt)
            if data:
                data["agent"] = "Agente 3: Especialista en Inversión"
                data["ai_powered"] = True
                return data
        except Exception as e:
            logger.warning(f"Fallo en llamada a Gemini para Agente 3 ({e}), usando motor estructurado.")

    # Heurística estructurada si no hay clave de IA
    if change_24h > 18:
        veredicto = "ESPERAR CORRECCIÓN"
        riesgo = "Alto"
        color = "amarillo"
        estrategia = "No compres con prisas. Tras una subida superior al 18%, lo más probable es una toma de beneficios a corto plazo. Es mejor esperar un retroceso de un 5-8% antes de entrar."
        consejo = f"{name} tiene mucha fuerza compradora hoy, pero entrar en pleno pico alcista suele provocar pérdidas por impaciencia. Espera a que el precio descanse."
    elif change_24h >= 5 and distance_to_high < 3.0:
        veredicto = "COMPRAR CON CAUTELA"
        riesgo = "Medio"
        color = "verde"
        estrategia = "Puedes abrir una posición pequeña fraccionada (no inviertas todo de golpe) colocando un límite de pérdida (stop-loss) protector."
        consejo = f"El movimiento alcista de {name} parece sano y bien acompañado de volumen. Si decides comprar, hazlo con prudencia y en varias compras pequeñas."
    else:
        veredicto = "MANTENER OBSERVACIÓN"
        riesgo = "Medio"
        color = "amarillo"
        estrategia = "Vigilar si el precio consolida por encima del precio actual antes de tomar una decisión de compra."
        consejo = "El activo muestra interés, pero todavía es pronto para asegurar una tendencia sostenida a largo plazo."

    return {
        "agent": "Agente 3: Especialista en Inversión",
        "veredicto": veredicto,
        "nivel_riesgo": riesgo,
        "etiqueta_color": color,
        "puntos_a_favor": [
            f"Fuerte liquidez y volumen diario (${crypto_info.get('volume_usdt_formatted', 'Alto')})",
            f"Impulso alcista claro del +{change_24h}% en 24 horas",
            f"Interés activo del mercado identificado por el Agente 2"
        ],
        "riesgos_principales": [
            "Volatilidad propia del mercado de criptomonedas",
            "Posible recogida de beneficios por parte de quienes compraron antes"
        ],
        "estrategia_sugerida": estrategia,
        "consejo_final": consejo,
        "ai_powered": False,
    }


# =========================================================================
# ORQUESTADOR DEL PIPELINE MULTI-AGENTE
# =========================================================================
async def run_full_agent_pipeline(
    ticker_data: Dict[str, Any],
    news_items: List[Dict[str, Any]],
    threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Ejecuta en cadena los tres agentes:
    1. Agente Monitor analiza datos técnicos.
    2. Agente Investigador analiza noticias y catalizadores.
    3. Agente Especialista pondera ambos informes y da veredicto.
    """
    agent1_res = run_agent_1_monitor(ticker_data, threshold=threshold)
    agent2_res = await run_agent_2_investigator(ticker_data, news_items)
    agent3_res = await run_agent_3_specialist(ticker_data, agent1_res, agent2_res)

    return {
        "symbol": ticker_data.get("symbol"),
        "name": ticker_data.get("name"),
        "price": ticker_data.get("price"),
        "price_formatted": ticker_data.get("price_formatted"),
        "change_24h": ticker_data.get("change_24h"),
        "volume_usdt_formatted": ticker_data.get("volume_usdt_formatted"),
        "news": news_items,
        "agent1_monitor": agent1_res,
        "agent2_investigator": agent2_res,
        "agent3_specialist": agent3_res,
        "pipeline_completed": True
    }
