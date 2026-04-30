"""Valida carga, entrenamiento y predicción del modelo de Cruz Roja."""

import pytest
import pandas as pd

from app.ml.cruz_roja.cruz_roja_ml import CruzRojaModel


SAMPLE_CSV_ROWS = [
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 1, "Fecha del Sorteo": "29/01/2020",
     "Lotería": "Loteria de la Cruz Roja", "Número del Sorteo": 2832,
     "Numero billete ganador": 2773, "Numero serie ganadora": 184, "Tipo de Premio": "Mayor"},
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 1, "Fecha del Sorteo": "15/01/2020",
     "Lotería": "Loteria de la Cruz Roja", "Número del Sorteo": 2830,
     "Numero billete ganador": 5872, "Numero serie ganadora": 175, "Tipo de Premio": "Mayor"},
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 2, "Fecha del Sorteo": "19/02/2020",
     "Lotería": "Loteria de la Cruz Roja", "Número del Sorteo": 2835,
     "Numero billete ganador": 9854, "Numero serie ganadora": 256, "Tipo de Premio": "Segundo"},
]


@pytest.fixture
def sample_df():
    """Construye un DataFrame con filas históricas mínimas de prueba."""
    return pd.DataFrame(SAMPLE_CSV_ROWS)


@pytest.fixture
def model_with_data(sample_df, tmp_path):
    """Entrega un modelo apuntando a un CSV temporal con datos de prueba."""
    csv_path = tmp_path / "cruz_roja_historico.csv"
    sample_df.to_csv(csv_path, index=False)
    return CruzRojaModel(data_path=str(csv_path))


@pytest.mark.unit
class TestCruzRojaModelInterface:
    """Pruebas de contrato e inicialización del modelo de Cruz Roja."""

    def test_extends_base_model(self):
        """Verifica que el modelo implemente la interfaz ``BaseModel``."""
        from app.ml.base_model import BaseModel
        assert issubclass(CruzRojaModel, BaseModel)

    def test_instantiates_with_data_path(self, tmp_path):
        """Verifica que el modelo acepte una ruta de datos explícita."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("")
        model = CruzRojaModel(data_path=str(csv_path))
        assert model is not None

    def test_default_data_path_contains_cruz_roja(self):
        """Verifica que la ruta por defecto corresponda a Cruz Roja."""
        model = CruzRojaModel()
        assert "cruz_roja" in model.data_path.lower()


@pytest.mark.unit
class TestCruzRojaModelLoadData:
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
        model = CruzRojaModel(data_path="/no/existe.csv")
        with pytest.raises(FileNotFoundError):
            model.load_data()


@pytest.mark.unit
class TestCruzRojaModelTrain:
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
        model = CruzRojaModel(data_path="/cualquiera.csv")
        with pytest.raises(RuntimeError):
            model.train()


@pytest.mark.unit
class TestCruzRojaModelPredict:
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
        """La serie puede tener hasta 3 dígitos (0–999)."""
        model_with_data.load_data()
        model_with_data.train()
        _, _, _, _, serie = model_with_data.predict()
        assert 0 <= serie <= 999

    def test_predict_requires_train_first(self, model_with_data):
        """Verifica que predecir sin entrenar produzca ``RuntimeError``."""
        model_with_data.load_data()
        with pytest.raises(RuntimeError):
            model_with_data.predict()

    def test_predict_is_reproducible_with_seed(self, model_with_data):
        """La misma semilla produce la misma predicción."""
        model_with_data.load_data()
        model_with_data.train()
        result1 = model_with_data.predict(seed=123)
        result2 = model_with_data.predict(seed=123)
        assert result1 == result2