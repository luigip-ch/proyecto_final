"""Valida el parsing, scraping y persistencia CSV del scraper de Baloto."""

import csv
import pytest
from unittest.mock import MagicMock, patch

from app.backend.scrapper import (
    extraer_resultados,
    guardar_csv,
    obtener_pagina,
    parse_resultado,
)

SAMPLE_HTML = """
<html><body><table>
  <tr>
    <td>1</td>
    <td>06/01/2024</td>
    <td>3 - 14 - 21 - 33 - 40 - 07</td>
  </tr>
  <tr>
    <td>2</td>
    <td>10/01/2024</td>
    <td>5 - 11 - 22 - 31 - 45 - 09</td>
  </tr>
  <tr><td>solo una columna</td></tr>
</table></body></html>
"""

CSV_FIELDS = ["fecha", "n1", "n2", "n3", "n4", "n5", "superbalota"]


@pytest.mark.unit
class TestParseResultado:
    """Pruebas para convertir texto de resultados en listas numéricas."""

    def test_returns_list_of_ints(self):
        """Verifica que el parser devuelva enteros en el orden original."""
        result = parse_resultado("3 - 14 - 21 - 33 - 40 - 07")
        assert result == [3, 14, 21, 33, 40, 7]

    def test_handles_single_digit_numbers(self):
        """Verifica que el parser acepte números de un solo dígito."""
        result = parse_resultado("1 - 2 - 3 - 4 - 5 - 6")
        assert result == [1, 2, 3, 4, 5, 6]

    def test_returns_empty_for_no_numbers(self):
        """Verifica que el parser retorne vacío si no hay números."""
        result = parse_resultado("sin numeros aqui")
        assert result == []


@pytest.mark.unit
class TestObtenerPagina:
    """Pruebas para la descarga y parseo de páginas HTML."""

    def test_returns_soup_on_200(self):
        """Verifica que una respuesta HTTP 200 produzca un objeto soup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        with patch(
            "app.backend.scrapper.requests.get",
            return_value=mock_response,
        ):
            result = obtener_pagina(1)
        assert result is not None

    def test_returns_none_on_error(self):
        """Verifica que una respuesta no exitosa retorne ``None``."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        with patch(
            "app.backend.scrapper.requests.get",
            return_value=mock_response,
        ):
            result = obtener_pagina(1)
        assert result is None


@pytest.mark.unit
class TestExtraerResultados:
    """Pruebas para extraer filas válidas desde HTML de resultados."""

    def test_extracts_rows_with_six_numbers(self):
        """Verifica que se extraigan solo filas con seis números."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        result = extraer_resultados(soup)
        assert len(result) == 2

    def test_extracted_row_has_all_fields(self):
        """Verifica que cada fila extraída tenga las columnas CSV esperadas."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
        result = extraer_resultados(soup)
        assert set(result[0].keys()) == set(CSV_FIELDS)

    def test_skips_rows_with_fewer_than_six_numbers(self):
        """Verifica que se omitan filas con resultados incompletos."""
        from bs4 import BeautifulSoup

        html = (
            "<html><body><table>"
            "<tr><td>1</td><td>fecha</td><td>1 - 2 - 3</td></tr>"
            "</table></body></html>"
        )
        soup = BeautifulSoup(html, "html.parser")
        result = extraer_resultados(soup)
        assert result == []


@pytest.mark.unit
class TestGuardarCsv:
    """Pruebas para la persistencia de resultados en CSV."""

    def test_creates_file(self, tmp_path):
        """Verifica que ``guardar_csv`` cree el archivo de salida."""
        output = str(tmp_path / "baloto_test.csv")
        guardar_csv(
            [{"fecha": "06/01/2024",
              "n1": 3, "n2": 14, "n3": 21,
              "n4": 33, "n5": 40, "superbalota": 7}],
            filename=output,
        )
        assert (tmp_path / "baloto_test.csv").exists()

    def test_csv_has_correct_headers(self, tmp_path):
        """Verifica que el CSV escrito conserve los encabezados esperados."""
        output = str(tmp_path / "baloto_test.csv")
        guardar_csv(
            [{"fecha": "06/01/2024",
              "n1": 3, "n2": 14, "n3": 21,
              "n4": 33, "n5": 40, "superbalota": 7}],
            filename=output,
        )
        with open(output, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CSV_FIELDS
