"""Extrae, transforma y guarda resultados históricos públicos de Baloto."""

import requests
from bs4 import BeautifulSoup
import re
import time
import csv

BASE_URL = "https://baloto.com/resultados"


def parse_resultado(texto):
    """
    Convierte:
    '25 - 33 - 37 - 39 - 41 - 11'
    -> [25, 33, 37, 39, 41, 11]
    """
    nums = re.findall(r'\d+', texto)
    return list(map(int, nums))


def obtener_pagina(page):
    """
    Descarga y parsea una página de resultados históricos de Baloto.

    Args:
        page: Número de página del paginador público de resultados.

    Returns:
        Objeto ``BeautifulSoup`` si la respuesta HTTP fue exitosa; de lo
        contrario ``None``.
    """
    url = f"{BASE_URL}?page={page}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        return None

    return BeautifulSoup(res.text, "html.parser")


def extraer_resultados(soup):
    """
    Extrae registros de sorteo desde una tabla HTML de resultados.

    Args:
        soup: Documento HTML parseado con ``BeautifulSoup``.

    Returns:
        Lista de diccionarios con fecha, cinco números principales y
        superbalota.
    """
    data = []

    filas = soup.find_all("tr")

    for fila in filas:
        columnas = fila.find_all("td")

        if len(columnas) < 3:
            continue

        fecha = columnas[1].get_text(strip=True)
        resultado_texto = columnas[2].get_text(strip=True)

        numeros = parse_resultado(resultado_texto)

        if len(numeros) == 6:
            data.append({
                "fecha": fecha,
                "n1": numeros[0],
                "n2": numeros[1],
                "n3": numeros[2],
                "n4": numeros[3],
                "n5": numeros[4],
                "superbalota": numeros[5]
            })

    return data


def scrapear_historico(max_paginas=200):
    """
    Recorre páginas de resultados hasta construir el histórico disponible.

    Args:
        max_paginas: Límite superior de páginas a consultar.

    Returns:
        Lista acumulada de resultados extraídos desde el sitio de Baloto.
    """
    dataset = []

    for page in range(1, max_paginas + 1):
        print(f"Página {page}")

        soup = obtener_pagina(page)

        if not soup:
            break

        resultados = extraer_resultados(soup)

        if not resultados:
            print("Fin del histórico")
            break

        dataset.extend(resultados)

        time.sleep(1)  # evitar bloqueo

    return dataset


def guardar_csv(data, filename="baloto_historico.csv"):
    """
    Persiste los resultados históricos de Baloto en un archivo CSV.

    Args:
        data: Iterable de diccionarios con las claves esperadas por el CSV.
        filename: Ruta o nombre del archivo de salida.
    """
    keys = ["fecha", "n1", "n2", "n3", "n4", "n5", "superbalota"]

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()

        for row in data:
            writer.writerow(row)

    print(f"CSV guardado en: {filename}")


if __name__ == "__main__":
    data = scrapear_historico(max_paginas=150)

    print(f"Total registros: {len(data)}")

    guardar_csv(data)
