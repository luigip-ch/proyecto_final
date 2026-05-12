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
        <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center p-4 font-sans">

            {/* TARJETA PRINCIPAL */}
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">

                {/* Encabezado Corporativo */}
                <div className="bg-slate-900 p-6 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-cyan-500"></div>
                    <div className="flex justify-center mb-4">
                        <Dna className="text-emerald-400 w-12 h-12" />
                    </div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">AI Lottery Predictor</h1>
                    <p className="text-slate-400 text-sm mt-2">Motor de Análisis Estadístico</p>
                </div>

                {/* Cuerpo del Formulario */}
                <div className="p-6">

                    {/* Alertas de Error */}
                    {error && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r flex items-start">
                            <AlertCircle className="text-red-500 w-5 h-5 flex-shrink-0 mr-3 mt-0.5" />
                            <p className="text-sm text-red-700 font-medium">{error}</p>
                        </div>
                    )}

                    <div className="space-y-6">

                        {/* Selector de Lotería */}
                        <div>
                            <label htmlFor="lottery-select" className="block text-sm font-semibold text-slate-700 mb-2">
                                Seleccione la Lotería (Dataset)
                            </label>

                            {isLoading ? (
                                <div className="w-full h-12 bg-slate-100 rounded-lg animate-pulse flex items-center px-4">
                                    <span className="text-slate-400 text-sm">Cargando base de datos...</span>
                                </div>
                            ) : (
                                <select
                                    id="lottery-select"
                                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block p-3 transition-colors"
                                    value={selectedLottery}
                                    onChange={(e) => setSelectedLottery(e.target.value)}
                                >
                                    <option value="" disabled>Seleccionar lotería...</option>
                                    {lotteries.map((loto) => (
                                        <option key={loto.id} value={loto.id}>
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
                            className="w-full flex items-center justify-center bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-all active:scale-95"
                        >
                            <RefreshCw className={`w-5 h-5 mr-2 ${isPredicting ? 'animate-spin' : ''}`} />
                            {isPredicting ? 'Calculando Probabilidades...' : 'Generar Predicción'}
                        </button>
                    </div>
                </div>

                {/* ÁREA DE RESULTADOS (Se muestra solo si hay predicción) */}
                {prediction && (
                    <div className="bg-emerald-50 p-6 border-t border-emerald-100">
                        <div className="flex items-center justify-center mb-4 text-emerald-700">
                            <CheckCircle2 className="w-5 h-5 mr-2" />
                            <span className="font-semibold text-sm">Predicción Exitosa</span>
                        </div>

                        {/* Si la API devuelve un array de 'main_numbers', los pintamos como esferas */}
                        {prediction.main_numbers && Array.isArray(prediction.main_numbers) ? (
                            <div className="flex flex-wrap justify-center gap-3">
                                {prediction.main_numbers.map((num: number, idx: number) => (
                                    <div key={idx} className="w-12 h-12 rounded-full bg-slate-900 text-white flex items-center justify-center text-lg font-bold shadow-md border-2 border-emerald-400">
                                        {num}
                                    </div>
                                ))}
                                {/* Si hay Super Balota, la pintamos de otro color */}
                                {prediction.super_ball !== null && prediction.super_ball !== undefined && (
                                    <div className="w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center text-lg font-bold shadow-md border-2 border-emerald-600 ml-2">
                                        {prediction.super_ball}
                                    </div>
                                )}
                            </div>
                        ) : (
                            /* Fallback: Si no devuelve 'main_numbers', mostramos el texto crudo */
                            <pre className="text-xs bg-white p-3 rounded border border-emerald-200 text-emerald-800 overflow-x-auto">
                                {JSON.stringify(prediction, null, 2)}
                            </pre>
                        )}

                        <p className="text-center text-xs text-emerald-600 mt-4 opacity-70">
                            Basado en patrones estadísticos e IA.
                        </p>
                    </div>
                )}

            </div>
        </div>
    )
}

export default App