# App Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir la PWA React (App) que consume la API existente del backend FastAPI y sirve desde la misma imagen Docker, sin ningún servidor adicional.

**Architecture:** Vite + React + TypeScript corre en `app/frontend/`. El Dockerfile usa multi-stage build: Node compila el `/dist`, Python lo copia y FastAPI lo sirve como archivos estáticos desde la raíz (`/`). Los endpoints de API (`/api/*`, `/health`) se registran antes del mount estático para que tengan precedencia. El frontend siempre llama rutas relativas (`/api/…`), nunca URLs absolutas.

**Tech Stack:** Vite 5, React 18, TypeScript 5, Tailwind CSS 3, vite-plugin-pwa, Vitest, React Testing Library, aiofiles (FastAPI static files).

---

## Reglas de oro — deben respetarse en cada tarea

| Regla | Detalle |
|---|---|
| **Rutas relativas** | `fetch("/api/predict", …)` — nunca `http://localhost:9002/…` |
| **Selector dinámico** | La lista de loterias viene de `GET /api/lotteries`. Nunca hardcodeada. |
| **Skeleton always** | Cualquier llamada async muestra skeleton/spinner mientras carga. |
| **No emojis como íconos** | Usar SVG inline o Heroicons. |
| **cursor-pointer** | En todo elemento clickeable. |
| **Responsive** | 375px / 768px / 1024px / 1440px. |
| **prefers-reduced-motion** | Respetar en todas las animaciones. |
| **Contraste ≥ 4.5:1** | Validar texto sobre fondo oscuro. |

---

## Paleta de colores App

| Token CSS | Hex | Rol |
|---|---|---|
| `--color-bg` | `#070D1A` | Fondo base (OLED dark) |
| `--color-surface` | `#0F1A2E` | Cards, paneles, widgets |
| `--color-primary` | `#00E5CC` | Teal — acciones principales, datos ML |
| `--color-secondary` | `#7B2FBE` | Purple — azar, número especial |
| `--color-positive` | `#00E676` | Probabilidad alta, resultado destacado |
| `--color-text` | `#F1F5F9` | Texto principal |
| `--color-muted` | `#64748B` | Etiquetas, metadatos |
| `--color-border` | `#1E2D45` | Bordes de cards |

Gradiente de logo/marca: `linear-gradient(135deg, #7B2FBE, #00E5CC)`

---

## Tipografía

- **Headings / números / código:** `Fira Code` — weight 400, 500, 600
- **Body / UI:** `Fira Sans` — weight 400, 500, 600, 700
- Google Fonts: `https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600;700&display=swap`

---

## Contratos de API que consume el frontend

### `GET /api/lotteries` → `LotteriesResponse`
```typescript
interface LotteryItem   { id: string; name: string }
interface LotteriesResponse { lotteries: LotteryItem[] }
```

### `POST /api/predict` → `PredictResponse`
```typescript
interface PredictResponse {
  lottery: string
  prediction: {
    main_numbers: number[]   // [0,4,7,1] para 4 cifras; [5,12,30,36,40] para Baloto
    special_number: number | null
    serie: string | null     // "153" | null
  }
  statistics: {
    even_count: number
    odd_count: number
    even_odd_ratio: string
    sum: number
    sum_in_optimal_range: boolean | null
    optimal_sum_range: { min: number; max: number } | null
    frequency_score: number
    pattern_score: number
  }
  generated_at: string       // ISO 8601 UTC
}
```

### `POST /api/train` → `TrainJobResponse`
```typescript
interface TrainJobResponse { job_id: string; status: string; lottery: string }
```

### `GET /api/train/{job_id}/status` → `TrainStatusResponse`
```typescript
interface TrainStatusResponse {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  lottery: string
  error: string | null
}
```

---

## Estructura de archivos del frontend

```
app/frontend/
├── public/
│   ├── icons/
│   │   ├── icon-192.png       # PWA icon 192×192
│   │   └── icon-512.png       # PWA icon 512×512
│   └── favicon.ico
├── src/
│   ├── api/
│   │   └── client.ts          # Todas las llamadas HTTP tipadas
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx     # Botón primario/secundario con estados
│   │   │   └── Skeleton.tsx   # Bloque skeleton configurable
│   │   ├── LotterySelector.tsx  # Dropdown dinámico desde /api/lotteries
│   │   ├── PredictionCard.tsx   # Muestra digits + serie
│   │   ├── StatisticsPanel.tsx  # Métricas: par/impar, suma, rango
│   │   └── TrainingPanel.tsx    # Dispara entrenamiento + polling de estado
│   ├── hooks/
│   │   ├── useLotteries.ts    # Fetch loterias al montar
│   │   ├── usePredict.ts      # Estado de predicción: idle/loading/success/error
│   │   └── useTrainJob.ts     # Inicia job + polling c/2s hasta completed|failed
│   ├── types/
│   │   └── api.ts             # Todas las interfaces TypeScript de la API
│   ├── App.tsx                # Layout raíz + wiring de componentes
│   ├── main.tsx               # Punto de entrada React + StrictMode
│   └── index.css              # @tailwind directives + CSS custom properties
├── index.html
├── vite.config.ts             # Proxy /api → backend en dev; PWA plugin
├── tailwind.config.ts         # Extiende colores App
├── tsconfig.json
├── tsconfig.app.json
└── package.json
```

---

## Archivos del proyecto raíz que se modifican

| Archivo | Qué cambia |
|---|---|
| `Dockerfile` | Se agrega Stage 1 (Node 20 alpine) que compila el frontend |
| `app/main.py` | Se añade `app.mount("/", StaticFiles(...))` al final, después de todos los routers |
| `requirements.txt` | Se añade `aiofiles` (requerido por `StaticFiles` de FastAPI) |

---

## Task 1: Scaffold del proyecto Vite + React + TypeScript

**Files:**
- Create: `app/frontend/package.json`
- Create: `app/frontend/tsconfig.json`
- Create: `app/frontend/tsconfig.app.json`
- Create: `app/frontend/vite.config.ts`
- Create: `app/frontend/index.html`
- Create: `app/frontend/src/main.tsx`
- Create: `app/frontend/src/App.tsx`
- Create: `app/frontend/src/test-setup.ts`

- [ ] **Step 1: Crear `app/frontend/package.json`**

```json
{
  "name": "App-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "@vitest/coverage-v8": "^2.1.0",
    "autoprefixer": "^10.4.19",
    "jsdom": "^25.0.0",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.5.3",
    "vite": "^5.4.0",
    "vite-plugin-pwa": "^0.20.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.6",
    "@testing-library/user-event": "^14.5.2"
  }
}
```

- [ ] **Step 2: Crear `app/frontend/tsconfig.json`**

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.node.json" },
    { "path": "./tsconfig.app.json" }
  ]
}
```

- [ ] **Step 3: Crear `app/frontend/tsconfig.app.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Crear `app/frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 5: Crear `app/frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'icons/*.png'],
      manifest: {
        name: 'App — Predictor ML de Loterias',
        short_name: 'App',
        description: 'Predicciones estadísticas de loterias colombianas basadas en ML',
        theme_color: '#070D1A',
        background_color: '#070D1A',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^\/api\//,
            handler: 'NetworkFirst',
            options: { cacheName: 'api-cache', networkTimeoutSeconds: 10 }
          }
        ]
      }
    })
  ],
  server: {
    // En desarrollo, redirige /api/* y /health al backend Python en :9002
    proxy: {
      '/api': 'http://localhost:9002',
      '/health': 'http://localhost:9002'
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts']
  }
})
```

- [ ] **Step 6: Crear `app/frontend/index.html`**

```html
<!doctype html>
<html lang="es">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#070D1A" />
    <meta name="description" content="Predicciones estadísticas de loterias colombianas basadas en ML" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <title>App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7: Crear `app/frontend/src/main.tsx`**

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 8: Crear `app/frontend/src/App.tsx` (placeholder)**

```tsx
export default function App() {
  return (
    <main className="min-h-screen bg-bg text-text flex items-center justify-center">
      <p className="font-mono text-primary">App — cargando…</p>
    </main>
  )
}
```

- [ ] **Step 9: Crear `app/frontend/src/test-setup.ts`**

```typescript
import '@testing-library/jest-dom'
```

- [ ] **Step 10: Instalar dependencias**

```bash
cd app/frontend
npm install
```

Expected: `node_modules/` creado, sin errores de peer deps.

- [ ] **Step 11: Verificar compilación TypeScript**

```bash
cd app/frontend
npm run build
```

Expected: `dist/` generado sin errores TypeScript.

- [ ] **Step 12: Commit**

```bash
git add app/frontend/
git commit -m "feat(frontend): scaffold Vite + React + TypeScript + PWA"
```

---

## Task 2: Design system — tokens CSS + Tailwind

**Files:**
- Create: `app/frontend/src/index.css`
- Create: `app/frontend/tailwind.config.ts`
- Create: `app/frontend/postcss.config.js`

- [ ] **Step 1: Crear `app/frontend/tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:        '#070D1A',
        surface:   '#0F1A2E',
        primary:   '#00E5CC',
        secondary: '#7B2FBE',
        positive:  '#00E676',
        text:      '#F1F5F9',
        muted:     '#64748B',
        border:    '#1E2D45',
      },
      fontFamily: {
        mono: ['"Fira Code"', 'monospace'],
        sans: ['"Fira Sans"', 'sans-serif'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #7B2FBE, #00E5CC)',
      },
    },
  },
  plugins: [],
} satisfies Config
```

- [ ] **Step 2: Crear `app/frontend/postcss.config.js`**

```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 3: Crear `app/frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ── Variables CSS globales ───────────────────────────────────────── */
:root {
  --color-bg:        #070D1A;
  --color-surface:   #0F1A2E;
  --color-primary:   #00E5CC;
  --color-secondary: #7B2FBE;
  --color-positive:  #00E676;
  --color-text:      #F1F5F9;
  --color-muted:     #64748B;
  --color-border:    #1E2D45;
}

/* ── Base ─────────────────────────────────────────────────────────── */
html {
  font-family: 'Fira Sans', sans-serif;
  background-color: var(--color-bg);
  color: var(--color-text);
  -webkit-font-smoothing: antialiased;
}

/* ── Reducción de movimiento ──────────────────────────────────────── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* ── Scrollbar oscura ─────────────────────────────────────────────── */
::-webkit-scrollbar        { width: 6px; }
::-webkit-scrollbar-track  { background: var(--color-bg); }
::-webkit-scrollbar-thumb  { background: var(--color-border); border-radius: 3px; }
```

- [ ] **Step 4: Verificar que Tailwind genera clases correctas**

```bash
cd app/frontend
npm run build
```

Expected: `dist/assets/*.css` contiene los colores App, sin errores.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/tailwind.config.ts app/frontend/postcss.config.js app/frontend/src/index.css
git commit -m "feat(frontend): design system — tokens CSS + Tailwind App"
```

---

## Task 3: Tipos TypeScript de la API

**Files:**
- Create: `app/frontend/src/types/api.ts`
- Create: `app/frontend/src/types/api.test.ts`

- [ ] **Step 1: Crear `app/frontend/src/types/api.test.ts`**

```typescript
import { describe, it, expect } from 'vitest'
import type {
  LotteryItem,
  LotteriesResponse,
  PredictResponse,
  TrainJobResponse,
  TrainStatusResponse,
} from './api'

describe('API types — smoke test estructural', () => {
  it('LotteryItem tiene id y name', () => {
    const item: LotteryItem = { id: 'cundinamarca', name: 'Lotería de Cundinamarca' }
    expect(item.id).toBe('cundinamarca')
    expect(item.name).toBeDefined()
  })

  it('LotteriesResponse tiene array de loterias', () => {
    const res: LotteriesResponse = { lotteries: [{ id: 'cundinamarca', name: 'Lotería de Cundinamarca' }] }
    expect(res.lotteries).toHaveLength(1)
  })

  it('PredictResponse acepta lotería de 4 cifras + serie', () => {
    const res: PredictResponse = {
      lottery: 'cundinamarca',
      prediction: { main_numbers: [0, 4, 7, 1], special_number: null, serie: '153' },
      statistics: {
        even_count: 2, odd_count: 2, even_odd_ratio: '2:2',
        sum: 12, sum_in_optimal_range: true,
        optimal_sum_range: { min: 10, max: 26 },
        frequency_score: 0, pattern_score: 0,
      },
      generated_at: '2024-05-27T10:30:00Z',
    }
    expect(res.prediction.main_numbers).toHaveLength(4)
    expect(res.prediction.serie).toBe('153')
    expect(res.prediction.special_number).toBeNull()
  })

  it('PredictResponse acepta lotería de 5 números + especial', () => {
    const res: PredictResponse = {
      lottery: 'baloto',
      prediction: { main_numbers: [5, 12, 30, 36, 40], special_number: 9, serie: null },
      statistics: {
        even_count: 4, odd_count: 1, even_odd_ratio: '4:1',
        sum: 123, sum_in_optimal_range: null,
        optimal_sum_range: null, frequency_score: 0, pattern_score: 0,
      },
      generated_at: '2024-05-27T10:30:00Z',
    }
    expect(res.prediction.special_number).toBe(9)
    expect(res.prediction.serie).toBeNull()
  })

  it('TrainStatusResponse cubre todos los valores de status', () => {
    const statuses: TrainStatusResponse['status'][] = ['queued', 'running', 'completed', 'failed']
    expect(statuses).toHaveLength(4)
  })

  it('TrainJobResponse tiene job_id', () => {
    const res: TrainJobResponse = { job_id: 'abc-123', status: 'queued', lottery: 'cundinamarca' }
    expect(res.job_id).toBe('abc-123')
  })
})
```

- [ ] **Step 2: Ejecutar test — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL — "Cannot find module './api'"

- [ ] **Step 3: Crear `app/frontend/src/types/api.ts`**

```typescript
// Contratos TypeScript que reflejan exactamente la API del backend.
// Fuente de verdad: docs/api-spec.md

export interface LotteryItem {
  id: string
  name: string
}

export interface LotteriesResponse {
  lotteries: LotteryItem[]
}

export interface PredictionResult {
  main_numbers: number[]
  special_number: number | null
  serie: string | null
}

export interface OptimalSumRange {
  min: number
  max: number
}

export interface PredictionStatistics {
  even_count: number
  odd_count: number
  even_odd_ratio: string
  sum: number
  sum_in_optimal_range: boolean | null
  optimal_sum_range: OptimalSumRange | null
  frequency_score: number
  pattern_score: number
}

export interface PredictResponse {
  lottery: string
  prediction: PredictionResult
  statistics: PredictionStatistics
  generated_at: string
}

export interface TrainJobResponse {
  job_id: string
  status: string
  lottery: string
}

export interface TrainStatusResponse {
  job_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  lottery: string
  error: string | null
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS — 6 tests passed.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/types/
git commit -m "feat(frontend): tipos TypeScript — contratos exactos de la API"
```

---

## Task 4: API client — funciones HTTP tipadas

**Files:**
- Create: `app/frontend/src/api/client.ts`
- Create: `app/frontend/src/api/client.test.ts`

- [ ] **Step 1: Crear `app/frontend/src/api/client.test.ts`**

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { getLotteries, predict, trainLottery, getTrainStatus } from './client'

const mockFetch = vi.fn()
beforeEach(() => { vi.stubGlobal('fetch', mockFetch) })
afterEach(() => { vi.unstubAllGlobals() })

function makeResponse(body: unknown, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  })
}

describe('getLotteries', () => {
  it('llama a GET /api/lotteries y retorna la respuesta', async () => {
    const data = { lotteries: [{ id: 'cundinamarca', name: 'Lotería de Cundinamarca' }] }
    mockFetch.mockReturnValueOnce(makeResponse(data))
    const result = await getLotteries()
    expect(mockFetch).toHaveBeenCalledWith('/api/lotteries')
    expect(result.lotteries[0].id).toBe('cundinamarca')
  })

  it('lanza error si la respuesta no es ok', async () => {
    mockFetch.mockReturnValueOnce(makeResponse({}, 500))
    await expect(getLotteries()).rejects.toThrow('HTTP 500')
  })
})

describe('predict', () => {
  it('llama a POST /api/predict con el body correcto', async () => {
    const data = {
      lottery: 'cundinamarca',
      prediction: { main_numbers: [0,4,7,1], special_number: null, serie: '153' },
      statistics: {
        even_count: 2, odd_count: 2, even_odd_ratio: '2:2',
        sum: 12, sum_in_optimal_range: true,
        optimal_sum_range: { min: 10, max: 26 },
        frequency_score: 0, pattern_score: 0,
      },
      generated_at: '2024-05-27T10:30:00Z',
    }
    mockFetch.mockReturnValueOnce(makeResponse(data))
    const result = await predict('cundinamarca')
    expect(mockFetch).toHaveBeenCalledWith('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lottery: 'cundinamarca' }),
    })
    expect(result.prediction.main_numbers).toEqual([0, 4, 7, 1])
  })

  it('lanza error 404 si la lotería no existe', async () => {
    mockFetch.mockReturnValueOnce(makeResponse({ detail: 'not found' }, 404))
    await expect(predict('invalida')).rejects.toThrow('HTTP 404')
  })
})

describe('trainLottery', () => {
  it('llama a POST /api/train y retorna job_id', async () => {
    const data = { job_id: 'abc-123', status: 'queued', lottery: 'cundinamarca' }
    mockFetch.mockReturnValueOnce(makeResponse(data))
    const result = await trainLottery('cundinamarca')
    expect(mockFetch).toHaveBeenCalledWith('/api/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lottery: 'cundinamarca' }),
    })
    expect(result.job_id).toBe('abc-123')
  })
})

describe('getTrainStatus', () => {
  it('llama a GET /api/train/{job_id}/status', async () => {
    const data = { job_id: 'abc-123', status: 'completed', lottery: 'cundinamarca', error: null }
    mockFetch.mockReturnValueOnce(makeResponse(data))
    const result = await getTrainStatus('abc-123')
    expect(mockFetch).toHaveBeenCalledWith('/api/train/abc-123/status')
    expect(result.status).toBe('completed')
  })
})
```

- [ ] **Step 2: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL — "Cannot find module './client'"

- [ ] **Step 3: Crear `app/frontend/src/api/client.ts`**

```typescript
/**
 * Capa de acceso a la API del backend.
 *
 * Todas las llamadas usan rutas relativas (/api/…) para que funcionen
 * tanto en desarrollo (proxy de Vite → :9002) como en producción
 * (misma imagen Docker, mismo origen).
 *
 * Convención de error: cualquier respuesta con status >= 400 lanza
 * un Error con el texto "HTTP <status>".
 */
import type {
  LotteriesResponse,
  PredictResponse,
  TrainJobResponse,
  TrainStatusResponse,
} from '../types/api'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json() as Promise<T>
}

export async function getLotteries(): Promise<LotteriesResponse> {
  const res = await fetch('/api/lotteries')
  return handleResponse<LotteriesResponse>(res)
}

export async function predict(lottery: string): Promise<PredictResponse> {
  const res = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lottery }),
  })
  return handleResponse<PredictResponse>(res)
}

export async function trainLottery(lottery: string): Promise<TrainJobResponse> {
  const res = await fetch('/api/train', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lottery }),
  })
  return handleResponse<TrainJobResponse>(res)
}

export async function getTrainStatus(jobId: string): Promise<TrainStatusResponse> {
  const res = await fetch(`/api/train/${jobId}/status`)
  return handleResponse<TrainStatusResponse>(res)
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS — 7 tests passed.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/api/
git commit -m "feat(frontend): API client tipado — getLotteries, predict, train"
```

---

## Task 5: Custom hooks

**Files:**
- Create: `app/frontend/src/hooks/useLotteries.ts`
- Create: `app/frontend/src/hooks/usePredict.ts`
- Create: `app/frontend/src/hooks/useTrainJob.ts`
- Create: `app/frontend/src/hooks/useLotteries.test.ts`
- Create: `app/frontend/src/hooks/usePredict.test.ts`
- Create: `app/frontend/src/hooks/useTrainJob.test.ts`

- [ ] **Step 1: Crear `app/frontend/src/hooks/useLotteries.test.ts`**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useLotteries } from './useLotteries'
import * as client from '../api/client'

vi.mock('../api/client')

describe('useLotteries', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('inicia en estado loading', () => {
    vi.mocked(client.getLotteries).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useLotteries())
    expect(result.current.loading).toBe(true)
    expect(result.current.lotteries).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('carga las loterias correctamente', async () => {
    vi.mocked(client.getLotteries).mockResolvedValueOnce({
      lotteries: [{ id: 'cundinamarca', name: 'Lotería de Cundinamarca' }]
    })
    const { result } = renderHook(() => useLotteries())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.lotteries).toHaveLength(1)
    expect(result.current.error).toBeNull()
  })

  it('captura error si la API falla', async () => {
    vi.mocked(client.getLotteries).mockRejectedValueOnce(new Error('HTTP 500'))
    const { result } = renderHook(() => useLotteries())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('HTTP 500')
    expect(result.current.lotteries).toEqual([])
  })
})
```

- [ ] **Step 2: Crear `app/frontend/src/hooks/usePredict.test.ts`**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePredict } from './usePredict'
import * as client from '../api/client'

vi.mock('../api/client')

const mockPrediction = {
  lottery: 'cundinamarca',
  prediction: { main_numbers: [0,4,7,1], special_number: null, serie: '153' },
  statistics: {
    even_count: 2, odd_count: 2, even_odd_ratio: '2:2',
    sum: 12, sum_in_optimal_range: true,
    optimal_sum_range: { min: 10, max: 26 },
    frequency_score: 0, pattern_score: 0,
  },
  generated_at: '2024-05-27T10:30:00Z',
}

describe('usePredict', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('estado inicial es idle', () => {
    const { result } = renderHook(() => usePredict())
    expect(result.current.loading).toBe(false)
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('execute() pone loading y guarda resultado', async () => {
    vi.mocked(client.predict).mockResolvedValueOnce(mockPrediction)
    const { result } = renderHook(() => usePredict())
    await act(async () => { await result.current.execute('cundinamarca') })
    expect(result.current.loading).toBe(false)
    expect(result.current.result).toEqual(mockPrediction)
    expect(result.current.error).toBeNull()
  })

  it('captura error de predict()', async () => {
    vi.mocked(client.predict).mockRejectedValueOnce(new Error('HTTP 404'))
    const { result } = renderHook(() => usePredict())
    await act(async () => { await result.current.execute('invalida') })
    expect(result.current.error).toBe('HTTP 404')
    expect(result.current.result).toBeNull()
  })
})
```

- [ ] **Step 3: Crear `app/frontend/src/hooks/useTrainJob.test.ts`**

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useTrainJob } from './useTrainJob'
import * as client from '../api/client'

vi.mock('../api/client')

describe('useTrainJob', () => {
  beforeEach(() => { vi.clearAllMocks(); vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('estado inicial es idle', () => {
    const { result } = renderHook(() => useTrainJob())
    expect(result.current.status).toBe('idle')
    expect(result.current.error).toBeNull()
  })

  it('start() hace polling hasta completed', async () => {
    vi.mocked(client.trainLottery).mockResolvedValueOnce({
      job_id: 'abc-123', status: 'queued', lottery: 'cundinamarca'
    })
    vi.mocked(client.getTrainStatus)
      .mockResolvedValueOnce({ job_id: 'abc-123', status: 'running', lottery: 'cundinamarca', error: null })
      .mockResolvedValueOnce({ job_id: 'abc-123', status: 'completed', lottery: 'cundinamarca', error: null })

    const { result } = renderHook(() => useTrainJob())
    await act(async () => { await result.current.start('cundinamarca') })
    await act(async () => { vi.advanceTimersByTime(2000) })
    await act(async () => { vi.advanceTimersByTime(2000) })
    await waitFor(() => expect(result.current.status).toBe('completed'))
  })

  it('registra error si el job falla', async () => {
    vi.mocked(client.trainLottery).mockResolvedValueOnce({
      job_id: 'abc-123', status: 'queued', lottery: 'cundinamarca'
    })
    vi.mocked(client.getTrainStatus).mockResolvedValueOnce({
      job_id: 'abc-123', status: 'failed', lottery: 'cundinamarca', error: 'Archivo no encontrado'
    })
    const { result } = renderHook(() => useTrainJob())
    await act(async () => { await result.current.start('cundinamarca') })
    await act(async () => { vi.advanceTimersByTime(2000) })
    await waitFor(() => expect(result.current.status).toBe('failed'))
    expect(result.current.error).toBe('Archivo no encontrado')
  })
})
```

- [ ] **Step 4: Ejecutar — deben fallar los 3**

```bash
cd app/frontend
npm test
```

Expected: FAIL — los tres módulos no existen.

- [ ] **Step 5: Crear `app/frontend/src/hooks/useLotteries.ts`**

```typescript
import { useState, useEffect } from 'react'
import type { LotteryItem } from '../types/api'
import { getLotteries } from '../api/client'

interface UseLotteriesState {
  lotteries: LotteryItem[]
  loading: boolean
  error: string | null
}

export function useLotteries(): UseLotteriesState {
  const [lotteries, setLotteries] = useState<LotteryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    getLotteries()
      .then(data => { if (!cancelled) setLotteries(data.lotteries) })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Error desconocido')
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  return { lotteries, loading, error }
}
```

- [ ] **Step 6: Crear `app/frontend/src/hooks/usePredict.ts`**

```typescript
import { useState, useCallback } from 'react'
import type { PredictResponse } from '../types/api'
import { predict } from '../api/client'

interface UsePredictState {
  result: PredictResponse | null
  loading: boolean
  error: string | null
  execute: (lottery: string) => Promise<void>
}

export function usePredict(): UsePredictState {
  const [result, setResult] = useState<PredictResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const execute = useCallback(async (lottery: string) => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await predict(lottery)
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }, [])

  return { result, loading, error, execute }
}
```

- [ ] **Step 7: Crear `app/frontend/src/hooks/useTrainJob.ts`**

```typescript
import { useState, useCallback, useRef } from 'react'
import type { TrainStatusResponse } from '../types/api'
import { trainLottery, getTrainStatus } from '../api/client'

type JobStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed'

interface UseTrainJobState {
  status: JobStatus
  error: string | null
  start: (lottery: string) => Promise<void>
}

const POLL_INTERVAL_MS = 2000
const TERMINAL_STATES = new Set<TrainStatusResponse['status']>(['completed', 'failed'])

export function useTrainJob(): UseTrainJobState {
  const [status, setStatus] = useState<JobStatus>('idle')
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const stopPolling = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
  }

  const poll = useCallback((jobId: string) => {
    timerRef.current = setTimeout(async () => {
      try {
        const data = await getTrainStatus(jobId)
        setStatus(data.status as JobStatus)
        if (data.status === 'failed') setError(data.error)
        if (!TERMINAL_STATES.has(data.status)) poll(jobId)
      } catch (err: unknown) {
        setStatus('failed')
        setError(err instanceof Error ? err.message : 'Error de red')
      }
    }, POLL_INTERVAL_MS)
  }, [])

  const start = useCallback(async (lottery: string) => {
    stopPolling()
    setError(null)
    setStatus('queued')
    try {
      const job = await trainLottery(lottery)
      poll(job.job_id)
    } catch (err: unknown) {
      setStatus('failed')
      setError(err instanceof Error ? err.message : 'Error iniciando entrenamiento')
    }
  }, [poll])

  return { status, error, start }
}
```

- [ ] **Step 8: Ejecutar — todos deben pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add app/frontend/src/hooks/
git commit -m "feat(frontend): hooks — useLotteries, usePredict, useTrainJob"
```

---

## Task 6: Componentes UI primitivos

**Files:**
- Create: `app/frontend/src/components/ui/Button.tsx`
- Create: `app/frontend/src/components/ui/Skeleton.tsx`
- Create: `app/frontend/src/components/ui/Button.test.tsx`
- Create: `app/frontend/src/components/ui/Skeleton.test.tsx`

- [ ] **Step 1: Crear `app/frontend/src/components/ui/Button.test.tsx`**

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from './Button'

describe('Button', () => {
  it('renderiza el texto del children', () => {
    render(<Button>Predecir</Button>)
    expect(screen.getByRole('button', { name: 'Predecir' })).toBeInTheDocument()
  })

  it('llama onClick al hacer click', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Click</Button>)
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('está deshabilitado y no dispara onClick cuando loading=true', async () => {
    const onClick = vi.fn()
    render(<Button loading onClick={onClick}>Cargando</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
    await userEvent.click(screen.getByRole('button'))
    expect(onClick).not.toHaveBeenCalled()
  })

  it('está deshabilitado cuando disabled=true', () => {
    render(<Button disabled>Deshabilitado</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })
})
```

- [ ] **Step 2: Crear `app/frontend/src/components/ui/Skeleton.test.tsx`**

```tsx
import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import { Skeleton } from './Skeleton'

describe('Skeleton', () => {
  it('renderiza con aria-label por defecto', () => {
    const { container } = render(<Skeleton />)
    const el = container.firstChild as HTMLElement
    expect(el.getAttribute('aria-label')).toBe('Cargando…')
  })

  it('aplica className adicional', () => {
    const { container } = render(<Skeleton className="h-8 w-32" />)
    const el = container.firstChild as HTMLElement
    expect(el.className).toContain('h-8')
    expect(el.className).toContain('w-32')
  })
})
```

- [ ] **Step 3: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL.

- [ ] **Step 4: Crear `app/frontend/src/components/ui/Button.tsx`**

```tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
  variant?: 'primary' | 'secondary'
  children: React.ReactNode
}

export function Button({
  loading = false,
  variant = 'primary',
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  const base =
    'cursor-pointer font-sans font-semibold rounded-lg px-5 py-2.5 text-sm transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2'
  const variants = {
    primary:
      'bg-primary text-bg hover:bg-primary/90 focus-visible:ring-primary disabled:opacity-50 disabled:cursor-not-allowed',
    secondary:
      'bg-surface border border-border text-text hover:border-primary focus-visible:ring-primary disabled:opacity-50 disabled:cursor-not-allowed',
  }

  return (
    <button
      disabled={disabled || loading}
      aria-busy={loading}
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <span
            className="h-4 w-4 rounded-full border-2 border-current border-t-transparent animate-spin"
            aria-hidden
          />
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  )
}
```

- [ ] **Step 5: Crear `app/frontend/src/components/ui/Skeleton.tsx`**

```tsx
interface SkeletonProps {
  className?: string
  label?: string
}

export function Skeleton({ className = '', label = 'Cargando…' }: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label={label}
      className={`animate-pulse rounded-md bg-surface ${className}`}
    />
  )
}
```

- [ ] **Step 6: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add app/frontend/src/components/ui/
git commit -m "feat(frontend): UI primitivos — Button + Skeleton"
```

---

## Task 7: LotterySelector

**Files:**
- Create: `app/frontend/src/components/LotterySelector.tsx`
- Create: `app/frontend/src/components/LotterySelector.test.tsx`

- [ ] **Step 1: Crear `app/frontend/src/components/LotterySelector.test.tsx`**

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LotterySelector } from './LotterySelector'
import * as client from '../api/client'

vi.mock('../api/client')

const lotteries = [{ id: 'cundinamarca', name: 'Lotería de Cundinamarca' }]

describe('LotterySelector', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('muestra skeleton mientras carga', () => {
    vi.mocked(client.getLotteries).mockReturnValue(new Promise(() => {}))
    render(<LotterySelector selected={null} onChange={vi.fn()} />)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('renderiza las loterias como opciones del select', async () => {
    vi.mocked(client.getLotteries).mockResolvedValueOnce({ lotteries })
    render(<LotterySelector selected={null} onChange={vi.fn()} />)
    await waitFor(() => expect(screen.getByRole('combobox')).toBeInTheDocument())
    expect(screen.getByText('Lotería de Cundinamarca')).toBeInTheDocument()
  })

  it('llama onChange con el id al seleccionar una opción', async () => {
    vi.mocked(client.getLotteries).mockResolvedValueOnce({ lotteries })
    const onChange = vi.fn()
    render(<LotterySelector selected={null} onChange={onChange} />)
    await waitFor(() => screen.getByRole('combobox'))
    await userEvent.selectOptions(screen.getByRole('combobox'), 'cundinamarca')
    expect(onChange).toHaveBeenCalledWith('cundinamarca')
  })

  it('muestra alerta de error si la API falla', async () => {
    vi.mocked(client.getLotteries).mockRejectedValueOnce(new Error('HTTP 500'))
    render(<LotterySelector selected={null} onChange={vi.fn()} />)
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
  })
})
```

- [ ] **Step 2: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL.

- [ ] **Step 3: Crear `app/frontend/src/components/LotterySelector.tsx`**

```tsx
import { Skeleton } from './ui/Skeleton'
import { useLotteries } from '../hooks/useLotteries'

interface LotterySelectorProps {
  selected: string | null
  onChange: (lottery: string) => void
}

export function LotterySelector({ selected, onChange }: LotterySelectorProps) {
  const { lotteries, loading, error } = useLotteries()

  if (loading) {
    return <Skeleton className="h-10 w-full" label="Cargando loterias…" />
  }

  if (error) {
    return (
      <div role="alert" className="text-sm text-red-400 font-sans">
        No se pudieron cargar las loterias: {error}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="lottery-select" className="text-xs font-sans text-muted uppercase tracking-wider">
        Lotería
      </label>
      <select
        id="lottery-select"
        value={selected ?? ''}
        onChange={e => onChange(e.target.value)}
        className="cursor-pointer rounded-lg border border-border bg-surface px-3 py-2.5 text-sm text-text focus:outline-none focus:border-primary transition-colors"
      >
        <option value="" disabled>Selecciona una lotería</option>
        {lotteries.map(l => (
          <option key={l.id} value={l.id}>{l.name}</option>
        ))}
      </select>
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/components/LotterySelector.tsx app/frontend/src/components/LotterySelector.test.tsx
git commit -m "feat(frontend): LotterySelector — dinámico desde API"
```

---

## Task 8: PredictionCard

**Files:**
- Create: `app/frontend/src/components/PredictionCard.tsx`
- Create: `app/frontend/src/components/PredictionCard.test.tsx`

- [ ] **Step 1: Crear `app/frontend/src/components/PredictionCard.test.tsx`**

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PredictionCard } from './PredictionCard'
import type { PredictResponse } from '../types/api'

const cundinamarca: PredictResponse = {
  lottery: 'cundinamarca',
  prediction: { main_numbers: [0, 4, 7, 1], special_number: null, serie: '153' },
  statistics: {
    even_count: 2, odd_count: 2, even_odd_ratio: '2:2',
    sum: 12, sum_in_optimal_range: true,
    optimal_sum_range: { min: 10, max: 26 },
    frequency_score: 0, pattern_score: 0,
  },
  generated_at: '2024-05-27T10:30:00Z',
}

const baloto: PredictResponse = {
  lottery: 'baloto',
  prediction: { main_numbers: [5, 12, 30, 36, 40], special_number: 9, serie: null },
  statistics: {
    even_count: 4, odd_count: 1, even_odd_ratio: '4:1',
    sum: 123, sum_in_optimal_range: null,
    optimal_sum_range: null, frequency_score: 0, pattern_score: 0,
  },
  generated_at: '2024-05-27T10:30:00Z',
}

describe('PredictionCard', () => {
  it('muestra los 4 dígitos de Cundinamarca individualmente', () => {
    render(<PredictionCard data={cundinamarca} />)
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(screen.getByText('7')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('muestra la serie con zero-padding', () => {
    render(<PredictionCard data={cundinamarca} />)
    expect(screen.getByText('153')).toBeInTheDocument()
  })

  it('muestra el número especial para Baloto', () => {
    render(<PredictionCard data={baloto} />)
    expect(screen.getByText('9')).toBeInTheDocument()
  })

  it('no muestra sección de serie cuando es null', () => {
    render(<PredictionCard data={baloto} />)
    expect(screen.queryByText(/^Serie$/i)).not.toBeInTheDocument()
  })

  it('muestra el año en el timestamp', () => {
    render(<PredictionCard data={cundinamarca} />)
    expect(screen.getByText(/2024/)).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL.

- [ ] **Step 3: Crear `app/frontend/src/components/PredictionCard.tsx`**

```tsx
import type { PredictResponse } from '../types/api'

interface PredictionCardProps {
  data: PredictResponse
}

export function PredictionCard({ data }: PredictionCardProps) {
  const { prediction, generated_at } = data
  const date = new Date(generated_at).toLocaleString('es-CO', {
    timeZone: 'America/Bogota',
    dateStyle: 'medium',
    timeStyle: 'short',
  })

  return (
    <article
      aria-label="Resultado de la predicción"
      className="rounded-xl border border-border bg-surface p-6 flex flex-col gap-6"
    >
      {/* Números principales */}
      <div className="flex flex-col gap-2">
        <span className="text-xs font-sans text-muted uppercase tracking-wider">Números</span>
        <div className="flex flex-wrap gap-3">
          {prediction.main_numbers.map((n, i) => (
            <div
              key={i}
              className="flex h-14 w-14 items-center justify-center rounded-lg border border-primary/30 bg-bg font-mono text-2xl font-semibold text-primary"
            >
              {n}
            </div>
          ))}
        </div>
      </div>

      {/* Número especial */}
      {prediction.special_number !== null && (
        <div className="flex flex-col gap-2">
          <span className="text-xs font-sans text-muted uppercase tracking-wider">Especial</span>
          <div className="flex h-14 w-14 items-center justify-center rounded-lg border border-secondary/50 bg-bg font-mono text-2xl font-semibold text-secondary">
            {prediction.special_number}
          </div>
        </div>
      )}

      {/* Serie */}
      {prediction.serie !== null && (
        <div className="flex flex-col gap-1">
          <span className="text-xs font-sans text-muted uppercase tracking-wider">Serie</span>
          <span className="font-mono text-3xl font-semibold text-text tracking-widest">
            {prediction.serie}
          </span>
        </div>
      )}

      <p className="text-xs text-muted font-sans">Generado: {date}</p>
    </article>
  )
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/components/PredictionCard.tsx app/frontend/src/components/PredictionCard.test.tsx
git commit -m "feat(frontend): PredictionCard — dígitos + serie + especial"
```

---

## Task 9: StatisticsPanel

**Files:**
- Create: `app/frontend/src/components/StatisticsPanel.tsx`
- Create: `app/frontend/src/components/StatisticsPanel.test.tsx`

- [ ] **Step 1: Crear `app/frontend/src/components/StatisticsPanel.test.tsx`**

```tsx
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatisticsPanel } from './StatisticsPanel'
import type { PredictionStatistics } from '../types/api'

const stats: PredictionStatistics = {
  even_count: 2, odd_count: 2, even_odd_ratio: '2:2',
  sum: 12, sum_in_optimal_range: true,
  optimal_sum_range: { min: 10, max: 26 },
  frequency_score: 0, pattern_score: 0,
}

describe('StatisticsPanel', () => {
  it('muestra la relación par/impar', () => {
    render(<StatisticsPanel stats={stats} />)
    expect(screen.getByText('2:2')).toBeInTheDocument()
  })

  it('muestra la suma total', () => {
    render(<StatisticsPanel stats={stats} />)
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('muestra badge verde cuando la suma está en rango óptimo', () => {
    render(<StatisticsPanel stats={stats} />)
    expect(screen.getByText(/rango óptimo/i)).toBeInTheDocument()
  })

  it('no muestra rango si sum_in_optimal_range es null', () => {
    const noRange: PredictionStatistics = { ...stats, sum_in_optimal_range: null, optimal_sum_range: null }
    render(<StatisticsPanel stats={noRange} />)
    expect(screen.queryByText(/rango óptimo/i)).not.toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL.

- [ ] **Step 3: Crear `app/frontend/src/components/StatisticsPanel.tsx`**

```tsx
import type { PredictionStatistics } from '../types/api'

interface StatisticsPanelProps {
  stats: PredictionStatistics
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-sans text-muted uppercase tracking-wider">{label}</span>
      <span className="font-mono text-xl font-semibold text-text">{value}</span>
    </div>
  )
}

export function StatisticsPanel({ stats }: StatisticsPanelProps) {
  return (
    <section
      aria-label="Estadísticas de la predicción"
      className="rounded-xl border border-border bg-surface p-6 flex flex-col gap-5"
    >
      <h2 className="text-sm font-sans font-semibold text-muted uppercase tracking-wider">
        Estadísticas
      </h2>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Relación Par / Impar" value={stats.even_odd_ratio} />
        <Stat label="Pares" value={stats.even_count} />
        <Stat label="Impares" value={stats.odd_count} />
        <Stat label="Suma total" value={stats.sum} />
      </div>

      {stats.sum_in_optimal_range !== null && stats.optimal_sum_range && (
        <div
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-sans ${
            stats.sum_in_optimal_range
              ? 'bg-positive/10 text-positive'
              : 'bg-red-500/10 text-red-400'
          }`}
        >
          <span aria-hidden>{stats.sum_in_optimal_range ? '✔' : '✖'}</span>
          <span>
            {stats.sum_in_optimal_range ? 'En' : 'Fuera del'} rango óptimo
            {' '}({stats.optimal_sum_range.min}–{stats.optimal_sum_range.max})
          </span>
        </div>
      )}
    </section>
  )
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/components/StatisticsPanel.tsx app/frontend/src/components/StatisticsPanel.test.tsx
git commit -m "feat(frontend): StatisticsPanel — par/impar, suma, rango óptimo"
```

---

## Task 10: TrainingPanel

**Files:**
- Create: `app/frontend/src/components/TrainingPanel.tsx`
- Create: `app/frontend/src/components/TrainingPanel.test.tsx`

- [ ] **Step 1: Crear `app/frontend/src/components/TrainingPanel.test.tsx`**

```tsx
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TrainingPanel } from './TrainingPanel'
import * as client from '../api/client'

vi.mock('../api/client')

describe('TrainingPanel', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('el botón está deshabilitado si no hay lotería seleccionada', () => {
    render(<TrainingPanel lottery={null} />)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('el botón está habilitado cuando hay una lotería seleccionada', () => {
    render(<TrainingPanel lottery="cundinamarca" />)
    expect(screen.getByRole('button')).not.toBeDisabled()
  })

  it('muestra texto "Entrenando" mientras el job corre', async () => {
    vi.mocked(client.trainLottery).mockResolvedValueOnce({
      job_id: 'abc', status: 'queued', lottery: 'cundinamarca'
    })
    vi.mocked(client.getTrainStatus).mockReturnValue(new Promise(() => {}))

    render(<TrainingPanel lottery="cundinamarca" />)
    await act(async () => { await userEvent.click(screen.getByRole('button')) })

    expect(screen.getByText(/entrenando/i)).toBeInTheDocument()
  })

  it('muestra "Completado" cuando el job termina', async () => {
    vi.useFakeTimers()
    vi.mocked(client.trainLottery).mockResolvedValueOnce({
      job_id: 'abc', status: 'queued', lottery: 'cundinamarca'
    })
    vi.mocked(client.getTrainStatus).mockResolvedValueOnce({
      job_id: 'abc', status: 'completed', lottery: 'cundinamarca', error: null
    })

    render(<TrainingPanel lottery="cundinamarca" />)
    await act(async () => { await userEvent.click(screen.getByRole('button')) })
    await act(async () => { vi.advanceTimersByTime(2100) })

    expect(screen.getByText(/completado/i)).toBeInTheDocument()
    vi.useRealTimers()
  })
})
```

- [ ] **Step 2: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL.

- [ ] **Step 3: Crear `app/frontend/src/components/TrainingPanel.tsx`**

```tsx
import { Button } from './ui/Button'
import { useTrainJob } from '../hooks/useTrainJob'

interface TrainingPanelProps {
  lottery: string | null
}

const STATUS_LABELS: Record<string, string> = {
  idle:      'Entrenar modelo',
  queued:    'Entrenando…',
  running:   'Entrenando…',
  completed: 'Completado ✔',
  failed:    'Error — reintentar',
}

export function TrainingPanel({ lottery }: TrainingPanelProps) {
  const { status, error, start } = useTrainJob()
  const isActive = status === 'queued' || status === 'running'

  return (
    <section
      aria-label="Panel de entrenamiento"
      className="rounded-xl border border-border bg-surface p-6 flex flex-col gap-4"
    >
      <h2 className="text-sm font-sans font-semibold text-muted uppercase tracking-wider">
        Entrenamiento del modelo
      </h2>
      <p className="text-xs font-sans text-muted">
        El entrenamiento puede tardar varios segundos. El estado se actualiza automáticamente.
      </p>
      <Button
        disabled={!lottery || isActive}
        loading={isActive}
        variant="secondary"
        onClick={() => lottery && start(lottery)}
      >
        {STATUS_LABELS[status] ?? 'Entrenar modelo'}
      </Button>

      {status === 'completed' && (
        <div role="status" className="text-sm text-positive font-sans">
          Modelo entrenado exitosamente. Ahora puedes generar predicciones.
        </div>
      )}

      {status === 'failed' && error && (
        <div role="alert" className="text-sm text-red-400 font-sans">
          Error: {error}
        </div>
      )}
    </section>
  )
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/components/TrainingPanel.tsx app/frontend/src/components/TrainingPanel.test.tsx
git commit -m "feat(frontend): TrainingPanel — start job + polling de estado"
```

---

## Task 11: App layout — Dashboard completo

**Files:**
- Modify: `app/frontend/src/App.tsx`
- Create: `app/frontend/src/App.test.tsx`

- [ ] **Step 1: Crear `app/frontend/src/App.test.tsx`**

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import * as client from './api/client'

vi.mock('./api/client')

const mockLotteries = { lotteries: [{ id: 'cundinamarca', name: 'Lotería de Cundinamarca' }] }
const mockPrediction = {
  lottery: 'cundinamarca',
  prediction: { main_numbers: [0, 4, 7, 1], special_number: null, serie: '153' },
  statistics: {
    even_count: 2, odd_count: 2, even_odd_ratio: '2:2',
    sum: 12, sum_in_optimal_range: true,
    optimal_sum_range: { min: 10, max: 26 },
    frequency_score: 0, pattern_score: 0,
  },
  generated_at: '2024-05-27T10:30:00Z',
}

describe('App', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('muestra el nombre de la app App', async () => {
    vi.mocked(client.getLotteries).mockResolvedValueOnce(mockLotteries)
    render(<App />)
    expect(screen.getByText(/App/i)).toBeInTheDocument()
  })

  it('carga el selector de loterias dinámicamente', async () => {
    vi.mocked(client.getLotteries).mockResolvedValueOnce(mockLotteries)
    render(<App />)
    await waitFor(() => screen.getByRole('combobox'))
    expect(screen.getByText('Lotería de Cundinamarca')).toBeInTheDocument()
  })

  it('genera una predicción al seleccionar lotería y hacer click en Predecir', async () => {
    vi.mocked(client.getLotteries).mockResolvedValueOnce(mockLotteries)
    vi.mocked(client.predict).mockResolvedValueOnce(mockPrediction)

    render(<App />)
    await waitFor(() => screen.getByRole('combobox'))
    await userEvent.selectOptions(screen.getByRole('combobox'), 'cundinamarca')
    await userEvent.click(screen.getByRole('button', { name: /predecir/i }))
    await waitFor(() => expect(screen.getByText('153')).toBeInTheDocument())
  })
})
```

- [ ] **Step 2: Ejecutar — debe fallar**

```bash
cd app/frontend
npm test
```

Expected: FAIL.

- [ ] **Step 3: Reemplazar `app/frontend/src/App.tsx` con el layout completo**

```tsx
import { useState } from 'react'
import { LotterySelector } from './components/LotterySelector'
import { PredictionCard } from './components/PredictionCard'
import { StatisticsPanel } from './components/StatisticsPanel'
import { TrainingPanel } from './components/TrainingPanel'
import { Button } from './components/ui/Button'
import { Skeleton } from './components/ui/Skeleton'
import { usePredict } from './hooks/usePredict'

export default function App() {
  const [selected, setSelected] = useState<string | null>(null)
  const { result, loading, error, execute } = usePredict()

  return (
    <div className="min-h-screen bg-bg text-text font-sans">
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="border-b border-border px-4 py-4 sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div>
            <span className="bg-brand-gradient bg-clip-text font-mono text-2xl font-semibold text-transparent">
              App
            </span>
            <p className="text-xs text-muted font-sans mt-0.5">Predictor ML de Loterias</p>
          </div>
          <span className="rounded-full border border-border px-2.5 py-1 font-mono text-xs text-muted">
            v1.0.0
          </span>
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────────────── */}
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">

          {/* Panel izquierdo: controles */}
          <div className="flex flex-col gap-6 lg:col-span-1">
            <section className="rounded-xl border border-border bg-surface p-6 flex flex-col gap-4">
              <h2 className="text-sm font-sans font-semibold text-muted uppercase tracking-wider">
                Configuración
              </h2>
              <LotterySelector selected={selected} onChange={setSelected} />
              <Button
                disabled={!selected}
                loading={loading}
                onClick={() => selected && execute(selected)}
              >
                Predecir
              </Button>
              {error && (
                <div role="alert" className="text-sm text-red-400 font-sans">
                  Error: {error}
                </div>
              )}
            </section>

            <TrainingPanel lottery={selected} />
          </div>

          {/* Panel derecho: resultados */}
          <div className="flex flex-col gap-6 lg:col-span-2">
            {loading && (
              <>
                <Skeleton className="h-52 w-full" label="Generando predicción…" />
                <Skeleton className="h-40 w-full" label="Cargando estadísticas…" />
              </>
            )}

            {result && !loading && (
              <>
                <PredictionCard data={result} />
                <StatisticsPanel stats={result.statistics} />
              </>
            )}

            {!result && !loading && (
              <div className="flex h-52 flex-col items-center justify-center rounded-xl border border-dashed border-border text-muted">
                <p className="font-sans text-sm">
                  Selecciona una lotería y haz clic en Predecir
                </p>
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 4: Ejecutar — debe pasar**

```bash
cd app/frontend
npm test
```

Expected: PASS — todos los tests.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/App.tsx app/frontend/src/App.test.tsx
git commit -m "feat(frontend): dashboard completo — LotterySelector + PredictionCard + Stats + Training"
```

---

## Task 12: Iconos PWA

**Files:**
- Create: `app/frontend/public/icons/icon-192.png`
- Create: `app/frontend/public/icons/icon-512.png`
- Create: `app/frontend/public/favicon.ico`

> Los iconos deben generarse con la paleta App: fondo `#070D1A`, texto con gradiente `#7B2FBE → #00E5CC`. Dimensiones obligatorias: 192×192 y 512×512 px.
>
> Herramientas sugeridas: Figma, Adobe Illustrator, o el script Node con `canvas` (requiere `npm install canvas`).

- [ ] **Step 1: Generar iconos con script Node**

```bash
cd app/frontend
npm install canvas --save-dev

node -e "
const { createCanvas } = require('canvas');
const fs = require('fs');

function makeIcon(size, path) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');
  // Fondo
  ctx.fillStyle = '#070D1A';
  ctx.fillRect(0, 0, size, size);
  // Gradiente del texto
  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, '#7B2FBE');
  grad.addColorStop(1, '#00E5CC');
  ctx.fillStyle = grad;
  ctx.font = 'bold ' + Math.floor(size * 0.35) + 'px monospace';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('NX', size / 2, size / 2);
  fs.writeFileSync(path, canvas.toBuffer('image/png'));
  console.log('Generado:', path);
}

fs.mkdirSync('public/icons', { recursive: true });
makeIcon(192, 'public/icons/icon-192.png');
makeIcon(512, 'public/icons/icon-512.png');
"
```

- [ ] **Step 2: Verificar que vite-plugin-pwa incluye los iconos**

```bash
cd app/frontend
npm run build
```

Expected: `dist/manifest.webmanifest` referencia a `icons/icon-192.png` y `icons/icon-512.png`. Sin errores.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/public/
git commit -m "feat(frontend): iconos PWA + favicon App"
```

---

## Task 13: FastAPI sirve archivos estáticos del frontend

**Files:**
- Modify: `requirements.txt` — añadir `aiofiles`
- Modify: `app/main.py` — añadir `StaticFiles` mount

- [ ] **Step 1: Añadir `aiofiles` a `requirements.txt`**

Abrir `requirements.txt` y añadir al final:

```
aiofiles>=23.0.0
```

- [ ] **Step 2: Actualizar `app/main.py`**

El mount va **después** de todos los `include_router` para que `/api/*` y `/health` tengan precedencia. El condicional `os.path.isdir` permite que el backend funcione en desarrollo (sin `dist/`) y en producción (con `dist/`):

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from app.backend.api.health import router as health_router
from app.backend.api.lotteries import router as lotteries_router
from app.backend.api.predict import router as predict_router
from app.backend.api.train import router as train_router
from app.config import ENV, PORT

app = FastAPI(
    docs_url="/docs" if ENV == "development" else None,
    redoc_url=None,
)

app.include_router(health_router)
app.include_router(lotteries_router)
app.include_router(predict_router)
app.include_router(train_router)

# ── Archivos estáticos del frontend ──────────────────────────────────
# El mount va después de los routers de API para no enmascarar
# /api/* ni /health. Solo se activa si el directorio dist existe
# (en tests y desarrollo puro con `vite dev` no existe).
_dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_dist_dir):
    app.mount("/", StaticFiles(directory=_dist_dir, html=True), name="frontend")

# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=ENV == "development",
    )
```

- [ ] **Step 3: Verificar que los tests del backend siguen pasando**

```bash
.venv/bin/pytest tests/ -v --tb=short
```

Expected: 71 passed (el `StaticFiles` no se monta porque `dist/` no existe en el entorno de test).

- [ ] **Step 4: Commit**

```bash
git add app/main.py requirements.txt
git commit -m "feat(backend): FastAPI sirve el frontend React como archivos estáticos"
```

---

## Task 14: Dockerfile multi-stage

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Reescribir `Dockerfile`**

```dockerfile
# ── Stage 1: Build del frontend ───────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copiar manifests primero para aprovechar cache de capas de Docker
COPY app/frontend/package*.json ./
RUN npm ci

# Copiar código fuente y compilar
COPY app/frontend/ ./
RUN npm run build
# Output en /frontend/dist

# ── Stage 2: Backend Python ───────────────────────────────────────────
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Copiar el dist compilado del frontend al lugar donde main.py lo busca
COPY --from=frontend-builder /frontend/dist ./app/frontend/dist

RUN chown -R appuser:appuser /code

USER appuser

ENV PYTHONPATH=/code

EXPOSE 9002

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:9002/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9002"]
```

- [ ] **Step 2: Build de Docker**

```bash
docker build -t App:test .
```

Expected: imagen construida sin errores. Stage 1 corre `npm run build`, Stage 2 copia el `dist/`.

- [ ] **Step 3: Probar el contenedor completo**

```bash
docker run --rm -p 9002:9002 \
  -v ./app/bd/historical:/code/app/bd/historical \
  --env ENV=production \
  App:test
```

En otro terminal:

```bash
# Backend responde
curl http://localhost:9002/health
# → {"status":"ok","version":"1.0.0"}

curl http://localhost:9002/api/lotteries
# → {"lotteries":[{"id":"cundinamarca","name":"Lotería de Cundinamarca"}]}
```

Abrir `http://localhost:9002` — debe mostrar el dashboard App.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "feat(docker): multi-stage build — Node compila frontend, Python lo sirve"
```

---

## Task 15: Verificación final

- [ ] **Step 1: Suite completa de tests del frontend**

```bash
cd app/frontend
npm run test:coverage
```

Expected: cobertura ≥ 80% en `src/api/`, `src/hooks/`, `src/components/`.

- [ ] **Step 2: Suite completa de tests del backend**

```bash
.venv/bin/pytest tests/ -v --tb=short
```

Expected: 71 passed.

- [ ] **Step 3: Build y smoke test final de Docker**

```bash
docker build -t App:latest .

docker run --rm -p 9002:9002 \
  -v ./app/bd/historical:/code/app/bd/historical \
  --env ENV=production \
  App:latest &

sleep 5

curl -f http://localhost:9002/health
curl -f http://localhost:9002/api/lotteries
curl -f -X POST http://localhost:9002/api/predict \
  -H "Content-Type: application/json" \
  -d '{"lottery":"cundinamarca"}'
```

- [ ] **Step 4: Checklist de accesibilidad (manual en navegador)**

- [ ] El `<select>` de loterias tiene `<label>` asociado con `htmlFor`
- [ ] Los botones tienen nombre accesible
- [ ] El spinner tiene `aria-hidden`
- [ ] Los skeletons tienen `role="status"` y `aria-label`
- [ ] Las alertas de error tienen `role="alert"`
- [ ] La app es navegable con Tab sin trampa de foco

- [ ] **Step 5: Verificar PWA con Lighthouse**

1. Abrir `http://localhost:9002` en Chrome.
2. DevTools → Lighthouse → Progressive Web App.
3. Expected: score ≥ 90.

- [ ] **Step 6: Commit de cierre**

```bash
git add .
git commit -m "feat: frontend App completo — PWA + dashboard + Docker multi-stage"
```

---

## Checklist de aceptación global

- [ ] `npm test` en `app/frontend/` pasa sin errores
- [ ] `pytest` en el proyecto raíz pasa 71 tests
- [ ] `docker build` sin errores
- [ ] `GET /health` → `{"status":"ok","version":"1.0.0"}`
- [ ] `GET /api/lotteries` → lista con al menos `cundinamarca`
- [ ] `POST /api/predict {"lottery":"cundinamarca"}` → predicción con 4 dígitos + serie de 3 caracteres
- [ ] `http://localhost:9002` sirve el dashboard React
- [ ] Lighthouse PWA ≥ 90
- [ ] No hay URLs absolutas `http://localhost:9002` en el código del frontend
- [ ] No hay listas de loterias hardcodeadas en el frontend
- [ ] Responsive verificado en 375px, 768px, 1024px, 1440px
