"""Valida carga, entrenamiento y predicción del modelo de Medellín."""

import pytest
from unittest.mock import patch
import pandas as pd
import os

from app.ml.medellin.medellin_ml import MedellinModel


SAMPLE_CSV_ROWS = [
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 1, "Fecha del Sorteo": "14/01/2020",
     "Lotería": "Loteria de Medellin", "Número del Sorteo": 4511,
     "Numero billete ganador": 6368, "Numero serie ganadora": 253, "Tipo de Premio": "Mayor"},
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 1, "Fecha del Sorteo": "08/01/2020",
     "Lotería": "Loteria de Medellin", "Número del Sorteo": 4510,
     "Numero billete ganador": 7207, "Numero serie ganadora": 191, "Tipo de Premio": "Mayor"},
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 2, "Fecha del Sorteo": "04/02/2020",
     "Lotería": "Loteria de Medellin", "Número del Sorteo": 4512,
     "Numero billete ganador": 1234, "Numero serie ganadora": 50, "Tipo de Premio": "Secos"},
]


@pytest.fixture
def sample_df():
    """Construye un DataFrame con filas históricas mínimas de prueba."""
    return pd.DataFrame(SAMPLE_CSV_ROWS)


@pytest.fixture
def model_with_data(sample_df, tmp_path):
    """Entrega un modelo apuntando a un CSV temporal con datos de prueba."""
    csv_path = tmp_path / "medellin_historico.csv"
    sample_df.to_csv(csv_path, index=False)
    return MedellinModel(data_path=str(csv_path))


@pytest.mark.unit
class TestMedellinModelInterface:
    """Pruebas de contrato e inicialización del modelo de Medellín."""

    def test_extends_base_model(self):
        """Verifica que el modelo implemente la interfaz ``BaseModel``."""
        from app.ml.base_model import BaseModel
        assert issubclass(MedellinModel, BaseModel)

    def test_instantiates_with_data_path(self, tmp_path):
        """Verifica que el modelo acepte una ruta de datos explícita."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("")
        model = MedellinModel(data_path=str(csv_path))
        assert model is not None

    def test_default_data_path_contains_medellin(self):
        """Verifica que la ruta por defecto corresponda a Medellín."""
        model = MedellinModel()
        assert "medellin" in model.data_path.lower()
        assert "loteria_medellin" in model.data_path.lower()


@pytest.mark.unit
class TestMedellinModelLoadData:
    """Pruebas de carga y filtrado de datos históricos."""

    def test_load_data_filters_only_mayor(self, model_with_data):
        """Verifica que la carga conserve solo filas de premio mayor."""
        model_with_data.load_data()
        assert len(model_with_data.df) == 2

    def test_load_data_sets_df_attribute(self, model_with_data):
        """Verifica que ``load_data`` inicialice el DataFrame interno."""
        model_with_data.load_data()
        assert hasattr(model_with_data, "df")
        assert isinstance(model_with_data.df, pd.DataFrame)

    def test_load_data_extracts_numero_billete(self, model_with_data):
        """Verifica que el DataFrame conserve la columna del billete ganador."""
        model_with_data.load_data()
        assert "Numero billete ganador" in model_with_data.df.columns

    def test_load_data_raises_if_file_missing(self):
        """Verifica error explícito cuando el CSV histórico no existe."""
        model = MedellinModel(data_path="/no/existe.csv")
        with pytest.raises(FileNotFoundError):
            model.load_data()


@pytest.mark.unit
class TestMedellinModelTrain:
    """Pruebas del entrenamiento y sus distribuciones de frecuencia."""

    def test_train_sets_frecuencias(self, model_with_data):
        """Verifica que ``train`` cree el atributo de frecuencias."""
        model_with_data.load_data()
        model_with_data.train()
        assert hasattr(model_with_data, "frecuencias")

    def test_train_frecuencias_is_dict(self, model_with_data):
        """Verifica que las frecuencias se almacenen como diccionario."""
        model_with_data.load_data()
        model_with_data.train()
        assert isinstance(model_with_data.frecuencias, dict)

    def test_train_frecuencias_keys_are_positions(self, model_with_data):
        """Verifica que haya una distribución por posición del número."""
        model_with_data.load_data()
        model_with_data.train()
        assert set(model_with_data.frecuencias.keys()) == {"miles", "centenas", "decenas", "unidades"}

    def test_train_requires_load_data_first(self):
        """Verifica que entrenar sin cargar datos produzca ``RuntimeError``."""
        model = MedellinModel(data_path="/cualquiera.csv")
        with pytest.raises(RuntimeError):
            model.train()


@pytest.mark.unit
class TestMedellinModelPredict:
    """Pruebas de generación y validación de predicciones."""

    def test_predict_returns_list(self, model_with_data):
        """Verifica que la predicción se devuelva como lista."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        assert isinstance(result, list)

    def test_predict_returns_five_elements(self, model_with_data):
        """[miles, centenas, decenas, unidades, serie] — 5 enteros separados."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        assert len(result) == 5

    def test_predict_digits_are_single_digits(self, model_with_data):
        """Cada posición del número (miles..unidades) es un dígito 0–9."""
        model_with_data.load_data()
        model_with_data.train()
        miles, centenas, decenas, unidades, _ = model_with_data.predict()
        for digit in (miles, centenas, decenas, unidades):
            assert 0 <= digit <= 9

    def test_predict_leading_zero_preserved(self, model_with_data):
        """Los dígitos no se combinan en un entero — leading zeros no se pierden."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict(seed=0)
        assert all(isinstance(d, int) for d in result[:4])
        assert all(0 <= d <= 9 for d in result[:4])

    def test_predict_serie_range_up_to_three_digits(self, model_with_data):
        """La serie puede ser hasta 3 cifras (0–999)."""
        model_with_data.load_data()
        model_with_data.train()
        *_, serie = model_with_data.predict()
        assert 0 <= serie <= 999

    def test_predict_is_deterministic_with_seed(self, model_with_data):
        """Verifica reproducibilidad cuando se usa la misma semilla."""
        model_with_data.load_data()
        model_with_data.train()
        r1 = model_with_data.predict(seed=42)
        r2 = model_with_data.predict(seed=42)
        assert r1 == r2

    def test_predict_requires_train_first(self, model_with_data):
        """Verifica que predecir sin entrenar produzca ``RuntimeError``."""
        model_with_data.load_data()
        with pytest.raises(RuntimeError):
            model_with_data.predict()
