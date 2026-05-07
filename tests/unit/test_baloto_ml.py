"""Valida carga, entrenamiento y predicción del modelo de Baloto."""

import pytest
import pandas as pd
import os

from app.ml.baloto.baloto_ml import BalotoModel

SAMPLE_CSV_ROWS = [
    {"fecha": "22 de Abril de 2026", "n1": 5, "n2": 12, "n3": 30, "n4": 36, "n5": 40, "superbalota": 9},
    {"fecha": "20 de Abril de 2026", "n1": 13, "n2": 33, "n3": 38, "n4": 40, "n5": 41, "superbalota": 8},
    {"fecha": "18 de Abril de 2026", "n1": 9, "n2": 16, "n3": 29, "n4": 32, "n5": 33, "superbalota": 10},
    {"fecha": "15 de Abril de 2026", "n1": 7, "n2": 11, "n3": 16, "n4": 27, "n5": 28, "superbalota": 14},
    {"fecha": "13 de Abril de 2026", "n1": 4, "n2": 11, "n3": 12, "n4": 21, "n5": 26, "superbalota": 6},
]

@pytest.fixture
def sample_df():
    """Construye un DataFrame con filas históricas mínimas de prueba."""
    return pd.DataFrame(SAMPLE_CSV_ROWS)


@pytest.fixture
def model_with_data(sample_df, tmp_path):
    """Entrega un modelo apuntando a un CSV temporal con datos de prueba."""
    csv_path = tmp_path / "baloto_historico.csv"
    sample_df.to_csv(csv_path, index=False)
    return BalotoModel(data_path=str(csv_path))


@pytest.mark.unit
class TestBalotoModelInterface:
    """Pruebas de contrato e inicialización del modelo de Baloto."""

    def test_extends_base_model(self):
        from app.ml.base_model import BaseModel
        assert issubclass(BalotoModel, BaseModel)

    def test_instantiates_with_data_path(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("fecha,n1,n2,n3,n4,n5,superbalota\n22 de Abril de 2026,5,12,30,36,40,9")
        model = BalotoModel(data_path=str(csv_path))
        assert model is not None

    def test_default_data_path_contains_baloto(self):
        model = BalotoModel()
        assert "baloto" in model.data_path.lower()


@pytest.mark.unit
class TestBalotoModelLoadData:
    """Pruebas de carga y filtrado de datos históricos."""

    def test_load_data_sets_df_attribute(self, model_with_data):
        model_with_data.load_data()
        assert hasattr(model_with_data, "df")
        assert isinstance(model_with_data.df, pd.DataFrame)
        assert len(model_with_data.df) == 5

    def test_load_data_raises_if_file_missing(self):
        model = BalotoModel(data_path="/no/existe.csv")
        with pytest.raises(FileNotFoundError):
            model.load_data()


@pytest.mark.unit
class TestBalotoModelTrain:
    """Pruebas del entrenamiento y sus distribuciones de frecuencia."""

    def test_train_sets_frecuencias(self, model_with_data):
        model_with_data.load_data()
        model_with_data.train()
        assert hasattr(model_with_data, "frecuencias_principales")
        assert hasattr(model_with_data, "frecuencias_superbalota")

    def test_train_requires_load_data_first(self):
        model = BalotoModel(data_path="/cualquiera.csv")
        with pytest.raises(RuntimeError):
            model.train()


@pytest.mark.unit
class TestBalotoModelPredict:
    """Pruebas de generación y validación de predicciones."""

    def test_predict_returns_list(self, model_with_data):
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        assert isinstance(result, list)

    def test_predict_returns_six_elements(self, model_with_data):
        """[n1, n2, n3, n4, n5, superbalota] — 6 enteros."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        assert len(result) == 6

    def test_predict_main_numbers_are_unique_and_sorted(self, model_with_data):
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        main_numbers = result[:5]
        # Check uniqueness
        assert len(set(main_numbers)) == 5
        # Check sorted
        assert main_numbers == sorted(main_numbers)

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
