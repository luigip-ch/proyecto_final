# Proyecto Final App  - ML Junior

## Participantes

- Denis Monsalve Naranjo
- Giovanni Galeano
- Luigi Piedrahita
- Daniel Rios Oquendo
- Ivan Rodriguez
- Andres Hincapie Vasquez
- Pedro Turriago Sanchez

## Objetivo General

Desarrollar e implementar modelos de Machine Learning orientados al análisis de series históricas, con el fin de generar combinaciones que cumplan criterios de distribución estadística, optimizando la proporción entre valores pares e impares y la frecuencia de sumas totales dentro de rangos probabilísticamente relevantes.

## Objetivos Específicos

1. Diseñar y entrenar modelos de Machine Learning capaces de identificar patrones, regularidades y comportamientos probabilísticos en series históricas, considerando variables como frecuencia, dispersión y distribución de datos.
2. Establecer e integrar reglas de optimización basadas en principios estadísticos (balance par/impar y rangos de suma total), que permitan validar y mejorar la calidad de las combinaciones generadas por los modelos, asegurando coherencia con tendencias históricas observadas.

## Alcance

Modelos de Machine Learning para analizar series históricas y generar combinaciones que cumplan reglas de oro de distribución estadística. Optimiza balances entre pares e impares y sumas totales frecuentes.

## Beneficios Esperados

Los beneficios del proyecto se pueden entender en tres niveles:

**Analítico:** Se logra una comprensión más profunda de los patrones subyacentes en los datos históricos. El modelo permite identificar regularidades, frecuencias y comportamientos que no son evidentes mediante análisis tradicionales, lo que incrementa la calidad del análisis estadístico y reduce la dependencia de supuestos intuitivos.

**Operativo:** Se optimiza la generación de combinaciones al incorporar reglas objetivas como el balance entre pares e impares y rangos de suma total frecuentes. Esto permite automatizar procesos que usualmente serían manuales, disminuyendo tiempos de análisis y aumentando la consistencia en los resultados.

**Toma de decisiones:** El proyecto aporta un enfoque basado en datos que mejora la coherencia y trazabilidad de las elecciones realizadas. Las combinaciones generadas no son aleatorias, sino sustentadas en criterios probabilísticos y evidencia histórica, lo que fortalece la justificación técnica del proceso.

Adicionalmente, el modelo es escalable y adaptable, permitiendo su actualización con nuevos datos y su aplicación en contextos similares. Contribuye también a la reducción de sesgos humanos en la selección de combinaciones, promoviendo decisiones más objetivas y alineadas con comportamientos observados en los datos.

## Arquitectura

La aplicación **ML Predictora de Números de Loterias** está estructurada en cuatro capas principales:

### 1. **Frontend (React)**
- Interfaz de usuario responsable de la selección de loterias
- Visualización de resultados y predicciones
- Comunicación con el backend mediante API REST

### 2. **Backend (Python)**
- **Selector:** Componente que gestiona la selección de loterias y coordina las predicciones
- **Entrenar Modelos:** Módulo responsable del entrenamiento de los modelos de ML con datos históricos
- **Scraper:** Herramienta para la recopilación automática de datos históricos de las loterias

### 3. **ML Layer (Python)**
- Modelos de Machine Learning especializados para cada loteria
- Análisis de series históricas y generación de predicciones
- Implementación de reglas de optimización estadística (balance par/impar, rangos de suma)

### 4. **BD Layer**
- Almacenamiento de datos históricos por loteria (Loteria 1, Loteria 2, ..., Loteria n)
- Gestión de archivos de datos para lectura y entrenamiento

**Flujos principales:**
- **Predicción:** Usuario → Frontend → Selector → Modelos ML → Resultados
- **Entrenamiento:** Scraper → Backend → Entrenar Modelos → ML Layer
- **Datos:** Archivos históricos ← Scraper (actualización automática)

![Arquitectura de la APP](./images/architecture.png)

## Stakeholders

- Lina Paola Soto Montes

## Referencias

- [Definición del Proyecto en Miro](https://miro.com/app/board/uXjVHec2Ol0=/?moveToWidget=3458764668982159419&cot=14)