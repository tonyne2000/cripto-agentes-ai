"""
Servicio de datos de mercado en tiempo real.
Conecta con la API pública de Binance para obtener cotizaciones reales y sin costes.
"""

from typing import Dict, List, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

# Diccionario de nombres populares para enriquecer las fichas
CRYPTO_NAMES: Dict[str, str] = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "BNB": "BNB",
    "XRP": "XRP (Ripple)",
    "DOGE": "Dogecoin",
    "ADA": "Cardano",
    "AVAX": "Avalanche",
    "LINK": "Chainlink",
    "SUI": "Sui Network",
    "NEAR": "NEAR Protocol",
    "APT": "Aptos",
    "PEPE": "Pepe",
    "SHIB": "Shiba Inu",
    "DOT": "Polkadot",
    "POL": "Polygon",
    "MATIC": "Polygon",
    "RENDER": "Render",
    "FET": "Artificial Superintelligence Alliance",
    "TAO": "Bittensor",
    "INJ": "Injective",
    "TIA": "Celestia",
    "SEI": "Sei",
    "KAS": "Kaspa",
    "LTC": "Litecoin",
    "BCH": "Bitcoin Cash",
    "UNI": "Uniswap",
    "AAVE": "Aave",
    "ARB": "Arbitrum",
    "OP": "Optimism",
    "FIL": "Filecoin",
    "ATOM": "Cosmos",
    "ICP": "Internet Computer",
    "TRX": "TRON",
    "XLM": "Stellar",
    "TON": "Toncoin",
    "WIF": "dogwifhat",
    "BONK": "Bonk",
    "FLOKI": "Floki",
    "JUP": "Jupiter",
    "ENA": "Ethena",
    "WLD": "Worldcoin",
    "ONDO": "Ondo Finance",
    "RUNE": "THORChain",
    "STX": "Stacks",
}

# Monedas estables o pares fiduciarios a ignorar en las alertas
EXCLUDED_SYMBOLS = {
    "USDT", "USDC", "FDUSD", "TUSD", "BUSD", "DAI", "EUR", "GBP",
    "AEUR", "USDP", "WBTC", "BTCUP", "BTCDOWN", "ETHUP", "ETHDOWN",
    "USD1", "USDE", "PYUSD", "EURI", "EURR"
}

BINANCE_24HR_URL = "https://api.binance.com/api/v3/ticker/24hr"


async def fetch_all_tickers() -> List[dict]:
    """Descarga todas las cotizaciones de 24h directamente de Binance."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(BINANCE_24HR_URL)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error al obtener tickers de Binance: {e}")
        return []


def format_ticker(item: dict) -> Optional[dict]:
    """Parsea y limpia la información de un par de Binance."""
    symbol = item.get("symbol", "")
    if not symbol.endswith("USDT"):
        return None

    base_asset = symbol[:-4]
    if base_asset in EXCLUDED_SYMBOLS:
        return None
    # Excluir tokens apalancados tipo BTCUP, BTCDOWN, etc.
    if base_asset.endswith("UP") or base_asset.endswith("DOWN") or base_asset.endswith("BEAR") or base_asset.endswith("BULL"):
        return None

    try:
        last_price = float(item.get("lastPrice", 0))
        price_change_percent = float(item.get("priceChangePercent", 0))
        high_price = float(item.get("highPrice", 0))
        low_price = float(item.get("lowPrice", 0))
        quote_volume = float(item.get("quoteVolume", 0))  # Volumen en USDT
        volume = float(item.get("volume", 0))
        count = int(item.get("count", 0))

        # Formatear el precio según su tamaño
        if last_price >= 1:
            price_formatted = f"${last_price:,.2f}"
        elif last_price >= 0.01:
            price_formatted = f"${last_price:,.4f}"
        else:
            price_formatted = f"${last_price:,.8f}"

        name = CRYPTO_NAMES.get(base_asset, base_asset)

        return {
            "symbol": base_asset,
            "pair": symbol,
            "name": name,
            "price": last_price,
            "price_formatted": price_formatted,
            "change_24h": round(price_change_percent, 2),
            "high_24h": high_price,
            "low_24h": low_price,
            "volume_usdt": quote_volume,
            "volume_crypto": volume,
            "trades_count": count,
        }
    except (ValueError, TypeError):
        return None


async def get_market_overview(limit: int = 50) -> List[dict]:
    """
    Obtiene las criptomonedas principales ordenadas por volumen de negociación.
    Garantiza que siempre aparezcan proyectos reales con liquidez.
    """
    raw_tickers = await fetch_all_tickers()
    parsed = []
    for item in raw_tickers:
        formatted = format_ticker(item)
        if formatted and formatted["volume_usdt"] > 100000:  # Mínimo 100k USDT de volumen
            parsed.append(formatted)

    # Ordenar por volumen en USDT descendente
    parsed.sort(key=lambda x: x["volume_usdt"], reverse=True)
    return parsed[:limit]


async def get_surging_cryptos(
    threshold_percent: float = 5.0,
    min_volume_usdt: float = 500000.0,
    limit: int = 20
) -> List[dict]:
    """
    Filtra las criptomonedas que han subido por encima del umbral indicado,
    asegurando que tengan un volumen mínimo para descartar activos manipulados sin liquidez.
    """
    raw_tickers = await fetch_all_tickers()
    surging = []

    for item in raw_tickers:
        formatted = format_ticker(item)
        if not formatted:
            continue

        if (
            formatted["change_24h"] >= threshold_percent
            and formatted["volume_usdt"] >= min_volume_usdt
        ):
            surging.append(formatted)

    # Ordenar por mayor porcentaje de subida
    surging.sort(key=lambda x: x["change_24h"], reverse=True)
    return surging[:limit]


async def get_crypto_detail(symbol: str) -> Optional[dict]:
    """Obtiene los datos en tiempo real de una criptomoneda específica."""
    clean_sym = symbol.upper().replace("USDT", "")
    pair = f"{clean_sym}USDT"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": pair}
            )
            if resp.status_code == 200:
                return format_ticker(resp.json())
    except Exception as e:
        logger.error(f"Error consultando detalle de {symbol}: {e}")

    return None
