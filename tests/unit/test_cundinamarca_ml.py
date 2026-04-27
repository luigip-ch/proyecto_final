import pytest
from unittest.mock import patch
import pandas as pd
import os

from app.ml.cundinamarca.cundinamarca_ml import CundinamarcaModel


SAMPLE_CSV_ROWS = [
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 1, "Fecha del Sorteo": "14/01/2020",
     "Lotería": "Loteria de Cundinamarca", "Número del Sorteo": 4479,
     "Numero billete ganador": 6368, "Numero serie ganadora": 173, "Tipo de Premio": "Mayor"},
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 1, "Fecha del Sorteo": "08/01/2020",
     "Lotería": "Loteria de Cundinamarca", "Número del Sorteo": 4478,
     "Numero billete ganador": 7207, "Numero serie ganadora": 115, "Tipo de Premio": "Mayor"},
    {"Año del Sorteo": "2,020", "Mes del Sorteo": 2, "Fecha del Sorteo": "04/02/2020",
     "Lotería": "Loteria de Cundinamarca", "Número del Sorteo": 4482,
     "Numero billete ganador": 1234, "Numero serie ganadora": 50, "Tipo de Premio": "Segundo"},
]


@pytest.fixture
def sample_df():
    return pd.DataFrame(SAMPLE_CSV_ROWS)


@pytest.fixture
def model_with_data(sample_df, tmp_path):
    csv_path = tmp_path / "cundinamarca_historico.csv"
    sample_df.to_csv(csv_path, index=False)
    return CundinamarcaModel(data_path=str(csv_path))


@pytest.mark.unit
class TestCundinamarcaModelInterface:
    def test_extends_base_model(self):
        from app.ml.base_model import BaseModel
        assert issubclass(CundinamarcaModel, BaseModel)

    def test_instantiates_with_data_path(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("")
        model = CundinamarcaModel(data_path=str(csv_path))
        assert model is not None

    def test_default_data_path_contains_cundinamarca(self):
        model = CundinamarcaModel()
        assert "cundinamarca" in model.data_path.lower()


@pytest.mark.unit
class TestCundinamarcaModelLoadData:
    def test_load_data_filters_only_mayor(self, model_with_data):
        model_with_data.load_data()
        assert len(model_with_data.df) == 2

    def test_load_data_sets_df_attribute(self, model_with_data):
        model_with_data.load_data()
        assert hasattr(model_with_data, "df")
        assert isinstance(model_with_data.df, pd.DataFrame)

    def test_load_data_extracts_numero_billete(self, model_with_data):
        model_with_data.load_data()
        assert "Numero billete ganador" in model_with_data.df.columns

    def test_load_data_raises_if_file_missing(self):
        model = CundinamarcaModel(data_path="/no/existe.csv")
        with pytest.raises(FileNotFoundError):
            model.load_data()


@pytest.mark.unit
class TestCundinamarcaModelTrain:
    def test_train_sets_frecuencias(self, model_with_data):
        model_with_data.load_data()
        model_with_data.train()
        assert hasattr(model_with_data, "frecuencias")

    def test_train_frecuencias_is_dict(self, model_with_data):
        model_with_data.load_data()
        model_with_data.train()
        assert isinstance(model_with_data.frecuencias, dict)

    def test_train_frecuencias_keys_are_positions(self, model_with_data):
        model_with_data.load_data()
        model_with_data.train()
        assert set(model_with_data.frecuencias.keys()) == {"miles", "centenas", "decenas", "unidades"}

    def test_train_requires_load_data_first(self):
        model = CundinamarcaModel(data_path="/cualquiera.csv")
        with pytest.raises(RuntimeError):
            model.train()


@pytest.mark.unit
class TestCundinamarcaModelPredict:
    def test_predict_returns_list(self, model_with_data):
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
        model_with_data.load_data()
        model_with_data.train()
        r1 = model_with_data.predict(seed=42)
        r2 = model_with_data.predict(seed=42)
        assert r1 == r2

    def test_predict_requires_train_first(self, model_with_data):
        model_with_data.load_data()
        with pytest.raises(RuntimeError):
            model_with_data.predict()
