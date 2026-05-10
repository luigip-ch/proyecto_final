import { useState, useEffect } from 'react'
import { Dna, RefreshCw, AlertCircle, Terminal } from 'lucide-react'

function App() {
    const [lotteries, setLotteries] = useState<any[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [debugData, setDebugData] = useState<string>("")

    useEffect(() => {
        const fetchLotteries = async () => {
            try {
                setIsLoading(true);
                const response = await fetch('/api/lotteries')

                if (!response.ok) {
                    throw new Error(`Error HTTP del Backend: Código ${response.status}`)
                }

                const data = await response.json()

                // Guardamos exactamente lo que mandó la cocina para mostrarlo en nuestra mini-terminal
                setDebugData(JSON.stringify(data, null, 2))

                // LÓGICA DE EXTRACCIÓN INFALIBLE
                if (Array.isArray(data)) {
                    setLotteries(data)
                } else if (data && typeof data === 'object') {
                    // Si es un objeto, busca si adentro hay una lista
                    const possibleArray = Object.values(data).find(val => Array.isArray(val))
                    if (possibleArray) {
                        setLotteries(possibleArray as any[])
                    } else {
                        // Si es un objeto puro, tomamos sus llaves para no colapsar
                        setLotteries(Object.keys(data))
                    }
                } else {
                    // Si manda cualquier otra cosa rara, lo forzamos a texto
                    setLotteries([String(data)])
                }

            } catch (err: any) {
                setError(err.message || 'Fallo de conexión con el Backend. ¿Está encendida la API?')
            } finally {
                setIsLoading(false)
            }
        }

        fetchLotteries()
    }, [])

    return (
        <div className="min-h-screen bg-slate-100 flex flex-col items-center justify-center p-4">

            {/* TARJETA PRINCIPAL B2B */}
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">

                {/* Encabezado */}
                <div className="bg-slate-900 p-6 text-center relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-400 to-cyan-500"></div>
                    <div className="flex justify-center mb-4">
                        <Dna className="text-emerald-400 w-12 h-12" />
                    </div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">AI Lottery Predictor</h1>
                    <p className="text-slate-400 text-sm mt-2">Motor de Análisis Estadístico</p>
                </div>

                {/* Cuerpo */}
                <div className="p-6">

                    {/* Alerta de Error */}
                    {error && (
                        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded-r flex items-start">
                            <AlertCircle className="text-red-500 w-5 h-5 flex-shrink-0 mr-3 mt-0.5" />
                            <p className="text-sm text-red-700 font-medium break-words">{error}</p>
                        </div>
                    )}

                    {/* Formulario */}
                    <div className="space-y-6">
                        <div>
                            <label htmlFor="lottery-select" className="block text-sm font-semibold text-slate-700 mb-2">
                                Seleccione la Lotería (Dataset)
                            </label>

                            {isLoading ? (
                                <div className="w-full h-12 bg-slate-100 rounded-lg animate-pulse flex items-center px-4">
                                    <span className="text-slate-400 text-sm">Conectando con Backend...</span>
                                </div>
                            ) : (
                                <select
                                    id="lottery-select"
                                    className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-emerald-500 focus:border-emerald-500 block p-3"
                                    defaultValue=""
                                >
                                    <option value="" disabled>Seleccionar lotería...</option>

                                    {/* Renderizado Seguro: Pase lo que pase, esto no colapsará la pantalla */}
                                    {Array.isArray(lotteries) && lotteries.length > 0 ? (
                                        lotteries.map((loto, index) => {
                                            let value = "";
                                            let label = "";

                                            if (typeof loto === 'string') {
                                                value = loto;
                                                label = loto.charAt(0).toUpperCase() + loto.slice(1);
                                            } else if (loto && typeof loto === 'object') {
                                                value = loto.id || loto.name || String(index);
                                                label = loto.name || JSON.stringify(loto).substring(0, 30);
                                            } else {
                                                value = String(loto);
                                                label = String(loto);
                                            }

                                            return (
                                                <option key={index} value={value}>
                                                    {label}
                                                </option>
                                            )
                                        })
                                    ) : (
                                        <option value="" disabled>No se encontraron datos</option>
                                    )}
                                </select>
                            )}
                        </div>

                        <button
                            disabled={isLoading || !lotteries || lotteries.length === 0}
                            className="w-full flex items-center justify-center bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-3 px-4 rounded-lg transition-colors"
                        >
                            <RefreshCw className={`w-5 h-5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                            Generar Predicción
                        </button>
                    </div>
                </div>
            </div>

            {/* MINI-TERMINAL DE DIAGNÓSTICO INCORPORADA */}
            <div className="w-full max-w-md mt-6">
                <div className="bg-slate-900 rounded-lg shadow-lg overflow-hidden border border-slate-700">
                    <div className="bg-slate-800 px-4 py-2 flex items-center border-b border-slate-700">
                        <Terminal className="w-4 h-4 text-emerald-400 mr-2" />
                        <span className="text-xs font-mono text-slate-300 font-semibold tracking-wider">📡 SEÑAL RAW DEL BACKEND</span>
                    </div>
                    <div className="p-4 max-h-48 overflow-y-auto">
                        {debugData ? (
                            <pre className="text-[11px] font-mono text-emerald-400 whitespace-pre-wrap break-all">
                                {debugData}
                            </pre>
                        ) : (
                            <p className="text-xs font-mono text-slate-500">Esperando comunicación con el puerto 9002...</p>
                        )}
                    </div>
                </div>
            </div>

        </div>
    )
}

export default App