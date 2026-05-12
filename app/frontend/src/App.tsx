import { useState, useEffect } from 'react'
import { Dna, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react'

// Definimos la estructura exacta que descubrimos en la telemetría
interface Lottery {
  id: string;
  name: string;
}

function App() {
  const [lotteries, setLotteries] = useState<Lottery[]>([])
  const [selectedLottery, setSelectedLottery] = useState<string>("")
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
      // Llamamos al endpoint indicado en el api-spec.md
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
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4 font-sans relative overflow-hidden">
      
      {/* Background decorations (Hero glowing orbs) */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-cyan-600/20 rounded-full blur-[120px] pointer-events-none"></div>

      {/* TARJETA PRINCIPAL (Glassmorphism) */}
      <div className="bg-slate-900/40 backdrop-blur-2xl rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-700/50 z-10">

        {/* Encabezado Heroico */}
        <div className="p-10 text-center relative overflow-hidden border-b border-slate-800/50">
          <div className="flex justify-center mb-6 relative">
            <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full"></div>
            <Dna className="text-emerald-400 w-16 h-16 relative z-10 drop-shadow-[0_0_15px_rgba(52,211,153,0.5)]" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 mb-2">
            AI Predictor
          </h1>
          <p className="text-slate-400 text-base font-medium uppercase tracking-widest">Motor Cuántico de Lotería</p>
        </div>

        {/* Cuerpo del Formulario */}
        <div className="p-8">

          {/* Alertas de Error */}
          {error && (
            <div className="bg-red-950/50 border border-red-500/50 p-4 mb-8 rounded-xl flex items-start backdrop-blur-sm">
              <AlertCircle className="text-red-400 w-6 h-6 flex-shrink-0 mr-3 mt-0.5 drop-shadow-[0_0_8px_rgba(248,113,113,0.5)]" />
              <p className="text-sm text-red-200 font-medium leading-relaxed">{error}</p>
            </div>
          )}

          <div className="space-y-8">

            {/* Selector de Lotería */}
            <div className="relative">
              <label htmlFor="lottery-select" className="block text-sm font-semibold text-slate-300 mb-3 tracking-wide">
                FUENTE DE DATOS
              </label>

              {isLoading ? (
                <div className="w-full h-14 bg-slate-800/50 rounded-xl animate-pulse flex items-center px-5 border border-slate-700/50">
                  <span className="text-emerald-400/70 text-sm font-medium tracking-wide">Sincronizando red neuronal...</span>
                </div>
              ) : (
                <div className="relative">
                  <select
                    id="lottery-select"
                    className="w-full bg-slate-800/60 border border-slate-600/50 text-slate-100 text-base font-medium rounded-xl focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 block p-4 transition-all appearance-none cursor-pointer hover:bg-slate-800/80"
                    value={selectedLottery}
                    onChange={(e) => setSelectedLottery(e.target.value)}
                  >
                    <option value="" disabled className="bg-slate-900 text-slate-500">Seleccione un modelo...</option>
                    {lotteries.map((loto) => (
                      <option key={loto.id} value={loto.id} className="bg-slate-900 text-slate-100">
                        {loto.name}
                      </option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-emerald-400">
                    <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                  </div>
                </div>
              )}
            </div>

            {/* Botón de Acción Hero */}
            <button
              onClick={handlePredict}
              disabled={isLoading || isPredicting || !selectedLottery}
              className="w-full flex items-center justify-center bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 disabled:border-slate-700 disabled:cursor-not-allowed text-slate-950 font-black text-lg tracking-wide py-4 px-6 rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(16,185,129,0.3)] hover:shadow-[0_0_30px_rgba(16,185,129,0.5)] active:scale-[0.98] border border-emerald-400/50"
            >
              <RefreshCw className={`w-6 h-6 mr-3 ${isPredicting ? 'animate-spin' : ''}`} />
              {isPredicting ? 'PROCESANDO...' : 'INICIAR SECUENCIA'}
            </button>
          </div>
        </div>

        {/* ÁREA DE RESULTADOS HEROICA */}
        {prediction && (
          <div className="bg-slate-900/80 p-8 border-t border-emerald-500/20 backdrop-blur-md">
            <div className="flex items-center justify-center mb-6 text-emerald-400">
              <CheckCircle2 className="w-6 h-6 mr-2 drop-shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
              <span className="font-bold text-sm tracking-widest uppercase">Predicción Lista</span>
            </div>

            {prediction.prediction && prediction.prediction.main_numbers && Array.isArray(prediction.prediction.main_numbers) ? (
              <div className="flex flex-col items-center gap-8">

                {/* Contenedor de Esferas Heroicas */}
                <div className="flex flex-wrap justify-center gap-4">
                  {/* Esferas Principales */}
                  {prediction.prediction.main_numbers.map((num: number, idx: number) => (
                    <div key={idx} className="w-14 h-14 rounded-full bg-gradient-to-b from-slate-700 to-slate-900 text-slate-100 flex items-center justify-center text-2xl font-black shadow-[inset_0_2px_4px_rgba(255,255,255,0.1),0_5px_15px_rgba(0,0,0,0.5)] border border-slate-600/50 transform transition-transform hover:scale-110 hover:border-emerald-500/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                      {num}
                    </div>
                  ))}

                  {/* Esfera Especial */}
                  {prediction.prediction.special_number !== null && prediction.prediction.special_number !== undefined && (
                    <div className="w-14 h-14 rounded-full bg-gradient-to-b from-emerald-400 to-teal-600 text-slate-950 flex items-center justify-center text-2xl font-black shadow-[inset_0_2px_4px_rgba(255,255,255,0.4),0_0_20px_rgba(16,185,129,0.5)] border border-emerald-300 ml-4 transform transition-transform hover:scale-110 hover:shadow-[0_0_30px_rgba(16,185,129,0.8)]">
                      {prediction.prediction.special_number}
                    </div>
                  )}
                </div>

                {/* Píldora de Serie */}
                {prediction.prediction.serie && (
                  <div className="bg-slate-800 text-emerald-400 px-6 py-2 rounded-full text-base font-bold border border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)] uppercase tracking-wider">
                    Serie: {prediction.prediction.serie}
                  </div>
                )}

              </div>
            ) : (
              <pre className="text-xs bg-slate-950 p-4 rounded-xl border border-red-500/30 text-red-400 overflow-x-auto">
                {JSON.stringify(prediction, null, 2)}
              </pre>
            )}

            <p className="text-center text-xs text-slate-500 mt-8 font-medium tracking-wide">
              PROBABILIDAD CUÁNTICA ESTIMADA
            </p>
          </div>
        )}

      </div>
    </div>
  )
}

export default App