# Plataforma Cripto Multi-Agente 🚀

Aplicación web interactiva que utiliza una arquitectura de **3 Agentes Inteligentes** para monitorizar el mercado de criptomonedas con datos reales, investigar las causas de subidas destacadas y emitir recomendaciones de inversión especializadas.

---

## 🤖 Los 3 Agentes

1. **Agente 1: Monitor de Mercado (Centinela)**
   - Conectado a la API en tiempo real de Binance (datos 100% reales, sin datos simulados).
   - Vigila las variaciones de precio en 24h y el volumen negociado.
   - Detecta automáticamente cuando una moneda supera el umbral fijado (por defecto **+5%**) y dispara la alarma.

2. **Agente 2: Investigador / Detective de Causas**
   - Rastrea noticias y titulares en directo de Google News (en español y global) y medios especializados como Cointelegraph.
   - Averigua el porqué del movimiento: catalizadores fundamentales (actualizaciones de red, adopción, acuerdos), compras institucionales o especulación.
   - Analiza el sentimiento social del mercado.

3. **Agente 3: Especialista en Inversión**
   - Analiza en conjunto los datos técnicos del Agente 1 y el informe del Agente 2.
   - Emite un veredicto claro: **COMPRAR**, **ESPERAR CORRECCIÓN** o **EVITAR POR RIESGO**.
   - Asigna un nivel de riesgo (Bajo, Medio, Alto, Extremo) y detalla pros, contras y una estrategia de entrada sensata explicada sin tecnicismos innecesarios.

---

## 🛠️ Tecnologías Utilizadas

- **Backend:** Python con FastAPI y Uvicorn.
- **Inteligencia Artificial:** SDK oficial de Google Gemini (`google-genai`) con modo heurístico de respaldo automático si aún no se ha configurado la clave.
- **Datos de Mercado:** API pública de Binance (cotizaciones reales al segundo).
- **Rastreo de Noticias:** RSS en tiempo real (Google News España/Global, Cointelegraph).
- **Frontend:** Dashboard moderno con TailwindCSS, diseño oscuro y animaciones en tiempo real.

---

## 🚀 Cómo Poner en Marcha la Aplicación

### 1. Requisitos previos
Tener instalado Python 3.10 o superior.

### 2. Configurar variables de entorno (Opcional pero recomendado para IA completa)
Abre el archivo `.env` en la raíz del proyecto y añade tu clave gratuita de Google Gemini (puedes obtener una en [Google AI Studio](https://aistudio.google.com/)):

```env
GEMINI_API_KEY=tu_clave_de_gemini_aqui
PRICE_ALERT_THRESHOLD=5.0
PORT=8000
```

> **Nota de seguridad:** El archivo `.env` está en `.gitignore` para proteger tus claves y asegurar que nunca se suban a GitHub. Si no pones ninguna clave, la aplicación funcionará de todos modos en modo heurístico estructurado.

### 3. Iniciar el servidor
Ejecuta el siguiente comando en tu terminal:

```bash
python main.py
```

### 4. Abrir la web
Abre tu navegador y entra en:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📁 Estructura del Proyecto

```
proyecto_antigrav/
│
├── main.py                  # Servidor web FastAPI y endpoints de la API
├── requirements.txt         # Dependencias del proyecto
├── .env.example             # Plantilla de variables de entorno seguras
├── .env                     # Variables de entorno locales (no se sube a Git)
├── .gitignore               # Exclusión de archivos sensibles y temporales
├── README.md                # Guía de uso y documentación
│
├── services/                # Módulos de lógica y agentes
│   ├── crypto_data.py       # Conexión con datos en directo de Binance
│   ├── news_fetcher.py      # Rastreador de noticias reales en RSS
│   └── agents.py            # Orquestador de los 3 Agentes (Monitor, Detective, Especialista)
│
└── static/                  # Interfaz de usuario web
    ├── index.html           # Panel de control web
    ├── style.css            # Estilos personalizados y animaciones
    └── app.js               # Lógica interactiva del cliente
```
