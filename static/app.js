/**
 * Lógica de la Plataforma Cripto Multi-Agente
 * Comunicación con la API de FastAPI y orquestación visual de los agentes.
 */

// Estado global en memoria
let marketData = [];
let currentThreshold = 5.0;
let isAnalyzing = false;
let autoRefreshTimer = null;

// Elementos del DOM
const refreshBtn = document.getElementById("refreshBtn");
const refreshIcon = document.getElementById("refreshIcon");
const alertsContainer = document.getElementById("alertsContainer");
const alertsCountBadge = document.getElementById("alertsCountBadge");
const marketTableBody = document.getElementById("marketTableBody");
const searchInput = document.getElementById("searchInput");
const thresholdInput = document.getElementById("thresholdInput");
const saveThresholdBtn = document.getElementById("saveThresholdBtn");
const aiStatusBadge = document.getElementById("aiStatusBadge");
const aiStatusText = document.getElementById("aiStatusText");

// Elementos de la sección de análisis
const analysisSection = document.getElementById("analysisSection");
const reportCryptoIcon = document.getElementById("reportCryptoIcon");
const reportCryptoName = document.getElementById("reportCryptoName");
const reportCryptoSymbol = document.getElementById("reportCryptoSymbol");
const reportCryptoPrice = document.getElementById("reportCryptoPrice");
const reportCryptoChange = document.getElementById("reportCryptoChange");

const a1StatusMsg = document.getElementById("a1StatusMsg");
const a1Volatility = document.getElementById("a1Volatility");
const a1Volume = document.getElementById("a1Volume");

const a2Factor = document.getElementById("a2Factor");
const a2Type = document.getElementById("a2Type");
const a2Sentiment = document.getElementById("a2Sentiment");
const a2Explanation = document.getElementById("a2Explanation");
const newsListContainer = document.getElementById("newsListContainer");

const a3VerdictBadge = document.getElementById("a3VerdictBadge");
const a3RiskLevel = document.getElementById("a3RiskLevel");
const a3Timing = document.getElementById("a3Timing");
const a3FinalAdvice = document.getElementById("a3FinalAdvice");
const a3Strategy = document.getElementById("a3Strategy");
const a3ProsList = document.getElementById("a3ProsList");
const a3ConsList = document.getElementById("a3ConsList");

// =========================================================================
// INICIALIZACIÓN
// =========================================================================
document.addEventListener("DOMContentLoaded", async () => {
  await loadConfig();
  await refreshAllData();

  // Escuchar eventos
  refreshBtn.addEventListener("click", () => refreshAllData(true));
  saveThresholdBtn.addEventListener("click", saveThreshold);
  thresholdInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") saveThreshold();
  });
  searchInput.addEventListener("input", filterMarketTable);

  // Auto-refresco de datos de mercado cada 45 segundos
  autoRefreshTimer = setInterval(() => {
    if (!isAnalyzing) {
      refreshAllData(false);
    }
  }, 45000);
});

// =========================================================================
// GESTIÓN DE CONFIGURACIÓN Y ESTADO
// =========================================================================
async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();
    currentThreshold = data.threshold;
    thresholdInput.value = currentThreshold;

    if (data.has_gemini_key) {
      aiStatusBadge.className = "inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs font-medium text-blue-400";
      aiStatusText.textContent = "Gemini AI Activo";
    } else {
      aiStatusBadge.className = "inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-xs font-medium text-amber-400";
      aiStatusText.textContent = "Modo Heurístico (Añade clave en .env)";
    }
  } catch (err) {
    console.error("Error al cargar configuración:", err);
  }
}

async function setThresholdQuick(val) {
  thresholdInput.value = val;
  await saveThreshold();
}

async function saveThreshold() {
  const val = parseFloat(thresholdInput.value);
  if (isNaN(val) || val <= 0) {
    alert("Por favor introduce un porcentaje válido mayor a 0");
    return;
  }

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ threshold: val })
    });
    const data = await res.json();
    currentThreshold = data.threshold;
    thresholdInput.value = currentThreshold;
    await loadAlerts();
  } catch (err) {
    console.error("Error guardando umbral:", err);
  }
}

// =========================================================================
// CARGA DE DATOS DE MERCADO EN TIEMPO REAL
// =========================================================================
async function refreshAllData(showAnimation = false) {
  if (showAnimation) {
    refreshIcon.classList.add("spin-animation");
  }

  try {
    await Promise.all([loadAlerts(), loadMarket()]);
  } catch (err) {
    console.error("Error actualizando mercado:", err);
  } finally {
    if (showAnimation) {
      setTimeout(() => {
        refreshIcon.classList.remove("spin-animation");
      }, 600);
    }
  }
}

// Cargar monedas en alerta (Agente 1)
async function loadAlerts() {
  try {
    const res = await fetch("/api/alerts");
    const json = await res.json();
    const items = json.data || [];

    alertsCountBadge.textContent = `${items.length} detectadas`;

    if (items.length === 0) {
      alertsContainer.innerHTML = `
        <div class="col-span-full py-10 px-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center">
          <div class="text-3xl mb-2">⚡</div>
          <h3 class="text-sm font-semibold text-slate-200">Ninguna moneda supera el +${currentThreshold}% en 24h</h3>
          <p class="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            El Agente 1 está monitorizando activamente. Puedes reducir el umbral de alerta arriba (ej: a +3%) o seleccionar cualquier criptomoneda de la tabla inferior para investigarla.
          </p>
        </div>
      `;
      return;
    }

    alertsContainer.innerHTML = items.map((coin) => {
      const isExtreme = coin.change_24h >= 15;
      const glowBorder = isExtreme ? "border-emerald-500/60 shadow-lg shadow-emerald-500/10" : "border-slate-800";
      const shortLetter = coin.symbol.slice(0, 2);

      return `
        <div class="crypto-card bg-slate-900/90 rounded-2xl border ${glowBorder} p-4 flex flex-col justify-between space-y-4">
          
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-slate-200 text-sm">
                ${shortLetter}
              </div>
              <div>
                <h4 class="font-bold text-white text-sm leading-tight">${coin.name}</h4>
                <span class="text-xs text-slate-400 font-semibold">${coin.symbol} / USDT</span>
              </div>
            </div>
            <div class="text-right">
              <div class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold text-xs">
                ▲ +${coin.change_24h}%
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2 text-xs py-2 px-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div>
              <span class="text-slate-500 block text-[10px]">Precio Actual</span>
              <span class="font-bold text-white">${coin.price_formatted}</span>
            </div>
            <div class="text-right">
              <span class="text-slate-500 block text-[10px]">Volumen 24h</span>
              <span class="font-semibold text-slate-300">$${formatCompactNumber(coin.volume_usdt)}</span>
            </div>
          </div>

          <button onclick="investigateCoin('${coin.symbol}')"
            class="w-full py-2.5 px-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs transition shadow-md shadow-blue-600/20 flex items-center justify-center gap-2">
            <span>🔎 Investigar con Agentes</span>
          </button>

        </div>
      `;
    }).join("");
  } catch (err) {
    alertsContainer.innerHTML = `
      <div class="col-span-full py-6 text-center text-rose-400 text-xs">
        Error al cargar alertas del Agente 1: ${err.message}
      </div>
    `;
  }
}

// Cargar tabla general de mercado
async function loadMarket() {
  try {
    const res = await fetch("/api/market?limit=60");
    const json = await res.json();
    marketData = json.data || [];
    renderMarketTable(marketData);
  } catch (err) {
    marketTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="py-6 text-center text-rose-400 text-xs">
          Error al cargar cotizaciones de mercado: ${err.message}
        </td>
      </tr>
    `;
  }
}

function renderMarketTable(data) {
  if (data.length === 0) {
    marketTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-slate-500">
          No se encontraron criptomonedas con ese filtro.
        </td>
      </tr>
    `;
    return;
  }

  marketTableBody.innerHTML = data.map((coin, index) => {
    const isPositive = coin.change_24h >= 0;
    const changeClass = isPositive ? "text-emerald-400" : "text-rose-400";
    const changeSign = isPositive ? "+" : "";

    return `
      <tr class="hover:bg-slate-800/40 transition">
        <td class="py-3 px-4 text-slate-500 font-mono">${index + 1}</td>
        <td class="py-3 px-4">
          <div class="flex items-center gap-2.5">
            <span class="w-6 h-6 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-300">
              ${coin.symbol.slice(0, 2)}
            </span>
            <div>
              <span class="font-bold text-white text-xs block">${coin.name}</span>
              <span class="text-[10px] text-slate-400">${coin.symbol}</span>
            </div>
          </div>
        </td>
        <td class="py-3 px-4 text-right font-bold text-slate-100">${coin.price_formatted}</td>
        <td class="py-3 px-4 text-right font-bold ${changeClass}">${changeSign}${coin.change_24h}%</td>
        <td class="py-3 px-4 text-right hidden md:table-cell text-slate-300 font-mono">$${formatCompactNumber(coin.volume_usdt)}</td>
        <td class="py-3 px-4 text-right hidden sm:table-cell text-slate-400 text-[11px]">
          <span>${formatPrice(coin.high_24h)}</span> / <span class="text-slate-500">${formatPrice(coin.low_24h)}</span>
        </td>
        <td class="py-3 px-4 text-center">
          <button onclick="investigateCoin('${coin.symbol}')"
            class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-blue-600 text-slate-300 hover:text-white font-medium text-[11px] transition border border-slate-700 hover:border-blue-500">
            Analizar
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

function filterMarketTable() {
  const query = searchInput.value.toLowerCase().trim();
  if (!query) {
    renderMarketTable(marketData);
    return;
  }

  const filtered = marketData.filter(coin =>
    coin.symbol.toLowerCase().includes(query) ||
    coin.name.toLowerCase().includes(query)
  );
  renderMarketTable(filtered);
}

// =========================================================================
// FLUJO MULTI-AGENTE: INVESTIGACIÓN Y VEREDICTO
// =========================================================================
async function investigateCoin(symbol) {
  isAnalyzing = true;

  // Abrir y enfocar la sección de análisis
  analysisSection.classList.remove("hidden");
  analysisSection.scrollIntoView({ behavior: "smooth", block: "start" });

  // Poner la interfaz en estado de carga activa para los 3 agentes
  reportCryptoIcon.textContent = symbol.slice(0, 2);
  reportCryptoName.textContent = `Consultando ${symbol}...`;
  reportCryptoSymbol.textContent = symbol;
  reportCryptoPrice.textContent = "Obteniendo datos...";
  reportCryptoChange.textContent = "--";

  a1StatusMsg.textContent = "Agente 1 validando métricas en directo...";
  a1Volatility.textContent = "En curso...";
  a1Volume.textContent = "En curso...";

  a2Factor.textContent = "Agente 2 buscando noticias y catalizadores...";
  a2Type.textContent = "En curso...";
  a2Sentiment.textContent = "En curso...";
  a2Explanation.textContent = "Rastreando artículos recientes en medios y redes para descifrar el porqué de la subida...";
  newsListContainer.innerHTML = `
    <div class="py-4 text-center text-slate-400 text-xs flex items-center justify-center gap-2">
      <div class="w-3 h-3 rounded-full border-2 border-purple-500 border-t-transparent animate-spin"></div>
      <span>El Detective está recopilando titulares en tiempo real...</span>
    </div>
  `;

  a3VerdictBadge.className = "text-xs font-bold px-3 py-1 rounded-lg inline-block bg-slate-800 text-slate-300";
  a3VerdictBadge.textContent = "Agente 3 esperando informe del Detective...";
  a3RiskLevel.textContent = "En cálculo...";
  a3Timing.textContent = "En evaluación";
  a3FinalAdvice.textContent = "El Especialista analizará la información en cuanto el Detective termine su investigación...";
  a3Strategy.textContent = "--";
  a3ProsList.innerHTML = "<li>Analizando fortalezas...</li>";
  a3ConsList.innerHTML = "<li>Evaluando riesgos...</li>";

  try {
    const res = await fetch(`/api/analyze/${symbol}`, { method: "POST" });
    if (!res.ok) {
      const errorJson = await res.json().catch(() => ({}));
      throw new Error(errorJson.detail || "Error en el servidor al ejecutar los agentes");
    }

    const data = await res.json();
    renderAnalysisResult(data);
  } catch (err) {
    alert(`No se pudo completar el análisis de ${symbol}: ${err.message}`);
    a1StatusMsg.textContent = "Error durante el análisis";
    a2Explanation.textContent = `Hubo un inconveniente al consultar las fuentes: ${err.message}`;
    a3FinalAdvice.textContent = "Por favor, inténtalo de nuevo o comprueba la conexión a Internet.";
  } finally {
    isAnalyzing = false;
  }
}

function renderAnalysisResult(data) {
  const { symbol, name, price_formatted, change_24h, volume_usdt_formatted, news, agent1_monitor, agent2_investigator, agent3_specialist } = data;

  // Cabecera
  reportCryptoIcon.textContent = symbol.slice(0, 2);
  reportCryptoName.textContent = name;
  reportCryptoSymbol.textContent = `${symbol}/USDT`;
  reportCryptoPrice.textContent = price_formatted;
  reportCryptoChange.textContent = `${change_24h >= 0 ? '+' : ''}${change_24h}%`;

  // AGENTE 1: MONITOR
  a1StatusMsg.textContent = agent1_monitor.summary;
  a1Volatility.textContent = agent1_monitor.volatility_level;
  a1Volume.textContent = agent1_monitor.volume_usdt_formatted;

  // AGENTE 2: DETECTIVE
  a2Factor.textContent = agent2_investigator.factor_principal || "Volumen y tendencia de mercado";
  a2Type.textContent = agent2_investigator.tipo_catalizador || "Técnico";
  a2Sentiment.textContent = agent2_investigator.sentimiento_social || "Optimista";
  a2Explanation.textContent = agent2_investigator.explicacion_causas || "No hay explicación detallada disponible.";

  // Renderizar noticias reales
  if (news && news.length > 0) {
    newsListContainer.innerHTML = news.map(item => `
      <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition">
        <div class="flex items-start justify-between gap-2">
          <a href="${item.link}" target="_blank" rel="noopener noreferrer"
             class="text-xs font-semibold text-blue-400 hover:text-blue-300 hover:underline line-clamp-2">
            ${item.title}
          </a>
        </div>
        <div class="flex items-center gap-2 mt-1.5 text-[10px] text-slate-500">
          <span class="font-medium text-slate-400">${item.source}</span>
          ${item.published ? `<span>•</span><span>${formatDate(item.published)}</span>` : ''}
        </div>
      </div>
    `).join("");
  } else {
    newsListContainer.innerHTML = `
      <div class="py-3 px-4 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400 italic">
        No se han encontrado titulares recientes específicos. La subida se apoya principalmente en entradas de liquidez directa y trading cuantitativo.
      </div>
    `;
  }

  // AGENTE 3: ESPECIALISTA
  const veredicto = agent3_specialist.veredicto || "OBSERVAR";
  const color = agent3_specialist.etiqueta_color || "amarillo";

  let badgeColorClass = "badge-amarillo";
  if (color === "verde" || veredicto.includes("COMPRA")) {
    badgeColorClass = "badge-verde";
  } else if (color === "rojo" || veredicto.includes("EVITAR") || veredicto.includes("ALTO RIESGO")) {
    badgeColorClass = "badge-rojo";
  }

  a3VerdictBadge.className = `text-xs font-extrabold px-3 py-1.5 rounded-lg inline-block ${badgeColorClass}`;
  a3VerdictBadge.textContent = veredicto;

  a3RiskLevel.textContent = agent3_specialist.nivel_riesgo || "Medio";
  a3Timing.textContent = veredicto.includes("COMPRA") ? "Momento actual" : "Esperar calma";
  a3FinalAdvice.textContent = agent3_specialist.consejo_final || "Consulte la estrategia sugerida.";
  a3Strategy.textContent = agent3_specialist.estrategia_sugerida || "Opere con gestión estricta de riesgo.";

  // Pros y contras
  const pros = agent3_specialist.puntos_a_favor || [];
  a3ProsList.innerHTML = pros.length > 0
    ? pros.map(p => `<li>${p}</li>`).join("")
    : "<li>Volumen transaccional confirmado</li>";

  const contras = agent3_specialist.riesgos_principales || [];
  a3ConsList.innerHTML = contras.length > 0
    ? contras.map(c => `<li>${c}</li>`).join("")
    : "<li>Volatilidad natural de criptomonedas</li>";
}

function closeAnalysis() {
  analysisSection.classList.add("hidden");
}

// =========================================================================
// UTILIDADES DE FORMATO
// =========================================================================
function formatCompactNumber(num) {
  if (num >= 1e9) return (num / 1e9).toFixed(2) + "B";
  if (num >= 1e6) return (num / 1e6).toFixed(2) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num ? num.toFixed(0) : "0";
}

function formatPrice(val) {
  if (!val) return "$0";
  if (val >= 1) return `$${val.toFixed(2)}`;
  if (val >= 0.01) return `$${val.toFixed(4)}`;
  return `$${val.toFixed(6)}`;
}

function formatDate(dateStr) {
  try {
    const d = new Date(dateStr);
    if (!isNaN(d.getTime())) {
      return d.toLocaleDateString("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    }
  } catch (e) { }
  return dateStr;
}
