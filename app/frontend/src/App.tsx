import { useState, useEffect } from 'react'
import { RefreshCw, AlertCircle, CheckCircle2, Sparkles } from 'lucide-react'

// Definimos la estructura exacta que descubrimos en la telemetría
interface Lottery {
  id: string;
  name: string;
}

function App() {
  const [lotteries, setLotteries] = useState<Lottery[]>([])
  const [selectedLottery, setSelectedLottery] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isPredicting, setIsPredicting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [prediction, setPrediction] = useState<any | null>(null)

  // 1. CARGAR LOTERÍAS AL INICIAR
  useEffect(() => {
    const fetchLotteries = async () => {
      try {
        const response = await fetch('/api/lotteries')
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`)

        const data = await response.json()

        // Ahora vamos directo a la llave exacta que descubrimos
        if (data && data.lotteries) {
          setLotteries(data.lotteries)
        } else {
          throw new Error('Estructura JSON no reconocida')
        }
      } catch (err: any) {
        setError(err.message || 'Fallo de conexión con el Backend.')
      } finally {
        setIsLoading(false)
      }
    }
    fetchLotteries()
  }, [])

  // 2. LA ACCIÓN: GENERAR PREDICCIÓN
  const handlePredict = async () => {
    if (!selectedLottery) return;

    setIsPredicting(true);
    setError(null);
    setPrediction(null);

    try {
      // Llamamos al endpoint indicado en la API
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ lottery: selectedLottery })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Fallo en predicción: ${response.status}`);
      }

      const result = await response.json();
      setPrediction(result);

    } catch (err: any) {
      setError(err.message || 'Ocurrió un error al predecir los números.');
    } finally {
      setIsPredicting(false);
    }
  }

  return (
    // AÑADIDO pb-24 y overflow-y-auto para evitar cortes en el borde inferior
    <div className="min-h-screen flex flex-col items-center py-12 pb-24 px-4 overflow-y-auto relative">

      {/* Background Pattern */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        }}
      ></div>

      {/* Hero Content */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 py-8 lg:py-12">
        <div className="text-center">

          {/* LA INYECCIÓN DEL LOGO SVG OFICIAL */}
          <div className="flex justify-center mb-8 mt-4 px-4">
            {/* 
              LA MAGIA ESTÁ AQUÍ: 
              Quitamos el 'inline-block' y ponemos 'w-full max-w-[600px]'.
              Esto obliga a la caja a medir exactamente 600px en PC, 
              pero le permite encogerse fluidamente en celulares.
            */}
            <div className="relative w-full max-w-[600px]">
              {/* Resplandor tecnológico de fondo adaptado a tu logo */}
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-cyan-500 rounded-full blur-3xl opacity-15 animate-pulse"></div>

              {/* La imagen simplemente ocupa el 100% de la caja de 600px */}
              <img
                src="/loterias_logo.svg"
                alt="LOTERIAS Logo Oficial"
                className="relative z-10 w-full h-auto object-contain drop-shadow-[0_0_20px_rgba(34,211,238,0.15)]"
              />
            </div>
          </div>

          {/* Subtitle */}
          <p className="text-lg lg:text-xl text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed mt-6">
            Tecnología de IA avanzada para analizar patrones estadísticos y generar combinaciones optimizadas basadas en datos históricos reales.
          </p>

          {/* Main Content Card */}
          <div className="max-w-2xl mx-auto">
            <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-8 lg:p-12 shadow-2xl border border-white/20">

              {/* Alertas de Error */}
              {error && (
                <div className="bg-red-500/20 border border-red-400/50 p-4 mb-8 rounded-xl flex items-start backdrop-blur-sm">
                  <AlertCircle className="text-red-400 w-6 h-6 flex-shrink-0 mr-3 mt-0.5" />
                  <p className="text-red-200 font-medium">{error}</p>
                </div>
              )}

              <div className="space-y-8">
                {/* Selector de Lotería */}
                <div>
                  <label htmlFor="lottery-select" className="block text-lg font-semibold text-white mb-4">
                    <Sparkles className="inline w-5 h-5 mr-2" />
                    Selecciona tu Lotería
                  </label>

                  {isLoading ? (
                    <div className="w-full h-14 bg-white/10 rounded-xl animate-pulse flex items-center px-6 backdrop-blur-sm">
                      <span className="text-white/70">Cargando loterías disponibles...</span>
                    </div>
                  ) : (
                    <select
                      id="lottery-select"
                      className="w-full bg-white/10 border border-white/20 text-white text-lg rounded-xl focus:ring-emerald-400 focus:border-emerald-400 block p-4 backdrop-blur-sm transition-all hover:bg-white/15"
                      value={selectedLottery}
                      onChange={(e) => setSelectedLottery(e.target.value)}
                    >
                      <option value="" className="bg-slate-800">Seleccionar lotería...</option>
                      {lotteries.map((loto) => (
                        <option key={loto.id} value={loto.id} className="bg-slate-800">
                          {loto.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Botón de Acción */}
                <button
                  onClick={handlePredict}
                  disabled={isLoading || isPredicting || !selectedLottery}
                  className="w-full flex items-center justify-center bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 disabled:from-slate-500 disabled:to-slate-600 disabled:cursor-not-allowed text-white font-bold py-4 px-8 rounded-xl transition-all active:scale-95 shadow-lg hover:shadow-xl disabled:shadow-none text-lg"
                >
                  <RefreshCw className={`w-6 h-6 mr-3 ${isPredicting ? 'animate-spin' : ''}`} />
                  {isPredicting ? 'Analizando Datos...' : 'Generar Predicción'}
                </button>
              </div>
            </div>

            {/* ÁREA DE RESULTADOS */}
            {prediction && (
              <div className="mt-12 bg-white/10 backdrop-blur-lg rounded-3xl p-8 lg:p-12 shadow-2xl border border-white/20">
                <div className="flex items-center justify-center mb-8 text-emerald-300">
                  <CheckCircle2 className="w-8 h-8 mr-3" />
                  <span className="font-bold text-xl">¡Predicción Generada!</span>
                </div>

                {/* CANVAS DE BALOTAS */}
                {prediction.prediction && prediction.prediction.main_numbers && Array.isArray(prediction.prediction.main_numbers) ? (
                  <div className="flex flex-col items-center gap-8">

                    {/* Contenedor de Esferas */}
                    <div className="flex flex-wrap justify-center gap-4">
                      {prediction.prediction.main_numbers.map((num: number, idx: number) => (
                        <div key={idx} className="w-16 h-16 rounded-full bg-gradient-to-br from-slate-800 to-slate-900 text-white flex items-center justify-center text-2xl font-bold shadow-2xl border-2 border-slate-600 transform transition-all hover:scale-110 hover:shadow-emerald-500/25">
                          {num}
                        </div>
                      ))}

                      {/* Esfera Esmeralda (Super Balota) */}
                      {prediction.prediction.special_number !== null && prediction.prediction.special_number !== undefined && (
                        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 text-white flex items-center justify-center text-2xl font-bold shadow-2xl border-2 border-emerald-400 ml-4 transform transition-all hover:scale-110 hover:shadow-emerald-400/50">
                          {prediction.prediction.special_number}
                        </div>
                      )}
                    </div>

                    {/* Píldora de Serie */}
                    {prediction.prediction.serie && (
                      <div className="bg-gradient-to-r from-slate-700 to-slate-800 text-white px-6 py-3 rounded-full text-lg font-bold border border-slate-600 shadow-lg">
                        Serie: {prediction.prediction.serie}
                      </div>
                    )}

                  </div>
                ) : (
                  <pre className="text-sm bg-slate-800/50 p-4 rounded-xl border border-slate-600 text-slate-300 overflow-x-auto">
                    {JSON.stringify(prediction, null, 2)}
                  </pre>
                )}

                <p className="text-center text-sm text-slate-400 mt-8 opacity-80 font-medium">
                  Resultados basados en análisis estadístico avanzado e inteligencia artificial.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App