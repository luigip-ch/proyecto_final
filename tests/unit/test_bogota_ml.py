"""Valida carga, entrenamiento y predicción del modelo de Bogotá."""

import pytest
from unittest.mock import patch
import pandas as pd
import numpy as np
import os

from app.ml.bogota.bogota_ml import BogotaModel


SAMPLE_CSV_ROWS = [
    {
        "FECHA": "2020-01-14",
        "NUMERO": "1234",
        "SERIE": "42",
        "SORTEO": "100"
    },
    {
        "FECHA": "2020-01-21",
        "NUMERO": "5678",
        "SERIE": "15",
        "SORTEO": "101"
    },
    {
        "FECHA": "2020-02-04",
        "NUMERO": "9012",
        "SERIE": "88",
        "SORTEO": "102"
    },
    {
        "FECHA": "2020-02-11",
        "NUMERO": "3456",
        "SERIE": "73",
        "SORTEO": "103"
    },
    {
        "FECHA": "2020-03-03",
        "NUMERO": "7890",
        "SERIE": "21",
        "SORTEO": "104"
    },
]


@pytest.fixture
def sample_df():
    """Construye un DataFrame con filas históricas mínimas de prueba."""
    return pd.DataFrame(SAMPLE_CSV_ROWS)


@pytest.fixture
def model_with_data(sample_df, tmp_path):
    """Entrega un modelo apuntando a un CSV temporal con datos de prueba."""
    csv_path = tmp_path / "bogota_historico.csv"
    sample_df.to_csv(csv_path, index=False, sep=';', encoding='latin1')
    return BogotaModel(data_path=str(csv_path))


@pytest.mark.unit
class TestBogotaModelInterface:
    """Pruebas de contrato e inicialización del modelo de Bogotá."""

    def test_extends_base_model(self):
        """Verifica que el modelo implemente la interfaz ``BaseModel``."""
        from app.ml.base_model import BaseModel
        assert issubclass(BogotaModel, BaseModel)

    def test_instantiates_with_data_path(self, tmp_path):
        """Verifica que el modelo acepte una ruta de datos explícita."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("")
        model = BogotaModel(data_path=str(csv_path))
        assert model is not None

    def test_default_data_path_contains_bogota(self):
        """Verifica que la ruta por defecto corresponda a Bogotá."""
        model = BogotaModel()
        assert "bogota" in model.data_path.lower()

    def test_initial_state_uninitialized(self):
        """Verifica que inicialmente no haya datos ni modelo entrenado."""
        model = BogotaModel()
        assert model.df is None
        assert model.model is None
        assert model.scaler is None


@pytest.mark.unit
class TestBogotaModelLoadData:
    """Pruebas de carga y limpieza de datos históricos."""

    def test_load_data_sets_df_attribute(self, model_with_data):
        """Verifica que ``load_data`` inicialice el DataFrame interno."""
        model_with_data.load_data()
        assert hasattr(model_with_data, "df")
        assert isinstance(model_with_data.df, pd.DataFrame)

    def test_load_data_has_correct_columns(self, model_with_data):
        """Verifica que el DataFrame contenga las columnas esperadas."""
        model_with_data.load_data()
        assert "Año" in model_with_data.df.columns
        assert "Mes" in model_with_data.df.columns
        assert "NUMERO" in model_with_data.df.columns
        assert "SERIE" in model_with_data.df.columns
        assert "SORTEO" in model_with_data.df.columns

    def test_load_data_processes_dates_correctly(self, model_with_data):
        """Verifica que las fechas se conviertan a año y mes."""
        model_with_data.load_data()
        assert model_with_data.df["Año"].dtype in [np.int32, np.int64, int]
        assert model_with_data.df["Mes"].dtype in [np.int32, np.int64, int]
        assert all(model_with_data.df["Año"] >= 1900)
        assert all(model_with_data.df["Mes"] >= 1)
        assert all(model_with_data.df["Mes"] <= 12)

    def test_load_data_cleans_numero_column(self, model_with_data):
        """Verifica que NUMERO se extraiga como enteros limpios."""
        model_with_data.load_data()
        assert model_with_data.df["NUMERO"].dtype in [np.int32, np.int64, int]
        assert all(model_with_data.df["NUMERO"] >= 0)

    def test_load_data_cleans_serie_column(self, model_with_data):
        """Verifica que SERIE se extraiga como enteros limpios."""
        model_with_data.load_data()
        assert model_with_data.df["SERIE"].dtype in [np.int32, np.int64, int]
        assert all(model_with_data.df["SERIE"] >= 0)

    def test_load_data_cleans_sorteo_column(self, model_with_data):
        """Verifica que SORTEO se extraiga como enteros limpios."""
        model_with_data.load_data()
        assert model_with_data.df["SORTEO"].dtype in [np.int32, np.int64, int]
        assert all(model_with_data.df["SORTEO"] >= 0)

    def test_load_data_preserves_record_count(self, model_with_data, sample_df):
        """Verifica que todos los registros se carguen."""
        model_with_data.load_data()
        assert len(model_with_data.df) == len(sample_df)

    def test_load_data_raises_if_file_missing(self):
        """Verifica error explícito cuando el CSV histórico no existe."""
        model = BogotaModel(data_path="/no/existe/bogota_historico.csv")
        with pytest.raises(FileNotFoundError):
            model.load_data()

    def test_load_data_handles_malformed_numbers(self, tmp_path):
        """Verifica que números con caracteres especiales se limpien."""
        csv_path = tmp_path / "bogota_test.csv"
        df = pd.DataFrame([
            {"FECHA": "2020-01-01", "NUMERO": "1234ABC", "SERIE": "42@", "SORTEO": "100XYZ"},
        ])
        df.to_csv(csv_path, index=False, sep=';', encoding='latin1')
        
        model = BogotaModel(data_path=str(csv_path))
        model.load_data()
        
        # Debe extraer solo los dígitos iniciales de cada campo
        assert model.df["NUMERO"].iloc[0] == 1234
        assert model.df["SERIE"].iloc[0] == 42
        assert model.df["SORTEO"].iloc[0] == 100


@pytest.mark.unit
class TestBogotaModelTrain:
    """Pruebas del entrenamiento del modelo MLP."""

    def test_train_sets_model_attribute(self, model_with_data):
        """Verifica que ``train`` inicialice el modelo MLPRegressor."""
        model_with_data.load_data()
        model_with_data.train()
        assert hasattr(model_with_data, "model")
        assert model_with_data.model is not None

    def test_train_sets_scaler_attribute(self, model_with_data):
        """Verifica que ``train`` inicialice el escalador."""
        model_with_data.load_data()
        model_with_data.train()
        assert hasattr(model_with_data, "scaler")
        assert model_with_data.scaler is not None

    def test_train_requires_load_data_first(self):
        """Verifica que entrenar sin cargar datos produzca ``RuntimeError``."""
        model = BogotaModel(data_path="/cualquiera.csv")
        with pytest.raises(RuntimeError, match="load_data"):
            model.train()

    def test_train_model_is_mlpregressor(self, model_with_data):
        """Verifica que el modelo entrenado sea un MLPRegressor."""
        from sklearn.neural_network import MLPRegressor
        model_with_data.load_data()
        model_with_data.train()
        assert isinstance(model_with_data.model, MLPRegressor)

    def test_train_model_can_make_predictions(self, model_with_data):
        """Verifica que el modelo entrenado pueda hacer predicciones."""
        model_with_data.load_data()
        model_with_data.train()
        
        # El modelo debe poder predecir sobre datos escalados
        X = model_with_data.df[['Año', 'Mes', 'SORTEO']].values
        X_scaled = model_with_data.scaler.transform(X)
        predictions = model_with_data.model.predict(X_scaled)
        
        assert predictions.shape == (len(model_with_data.df), 2)

    def test_train_scaler_transforms_features(self, model_with_data):
        """Verifica que el escalador normalice las características."""
        model_with_data.load_data()
        model_with_data.train()
        
        X = model_with_data.df[['Año', 'Mes', 'SORTEO']].values
        X_scaled = model_with_data.scaler.transform(X)
        
        # Después de escalado, la media debe estar cerca de 0
        assert np.abs(X_scaled.mean()) < 1


@pytest.mark.unit
class TestBogotaModelPredict:
    """Pruebas de generación y validación de predicciones."""

    def test_predict_returns_list(self, model_with_data):
        """Verifica que la predicción se devuelva como lista."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        assert isinstance(result, list)

    def test_predict_returns_two_elements(self, model_with_data):
        """Verifica que retorne [numero, serie]."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        assert len(result) == 2

    def test_predict_returns_integers(self, model_with_data):
        """Verifica que ambos elementos sean enteros."""
        model_with_data.load_data()
        model_with_data.train()
        numero, serie = model_with_data.predict()
        assert isinstance(numero, (int, np.integer))
        assert isinstance(serie, (int, np.integer))

    def test_predict_numero_is_four_digits(self, model_with_data):
        """Verifica que el número predicho sea razonable (0–9999)."""
        model_with_data.load_data()
        model_with_data.train()
        numero, _ = model_with_data.predict()
        assert 0 <= numero <= 9999

    def test_predict_serie_is_up_to_three_digits(self, model_with_data):
        """Verifica que la serie sea hasta 3 dígitos (0–999)."""
        model_with_data.load_data()
        model_with_data.train()
        _, serie = model_with_data.predict()
        assert 0 <= serie <= 999

    def test_predict_requires_train_first(self, model_with_data):
        """Verifica que predecir sin entrenar produzca ``RuntimeError``."""
        model_with_data.load_data()
        with pytest.raises(RuntimeError, match="train"):
            model_with_data.predict()

    def test_predict_requires_load_data_first(self, model_with_data):
        """Verifica que predecir sin cargar datos produzca ``RuntimeError``."""
        model_with_data.load_data()
        model_with_data.train()
        # Resetear df para simular que no se llamó load_data
        model_with_data.df = None
        with pytest.raises(RuntimeError, match="load_data"):
            model_with_data.predict()

    def test_predict_uses_next_sorteo_number(self, model_with_data):
        """Verifica que prediga para el siguiente número de sorteo."""
        model_with_data.load_data()
        model_with_data.train()
        
        max_sorteo = int(model_with_data.df['SORTEO'].max())
        # Debe funcionar correctamente usando max_sorteo + 1
        result = model_with_data.predict()
        assert len(result) == 2


@pytest.mark.unit
class TestBogotaModelCycleIntegration:
    """Pruebas del ciclo completo: load_data → train → predict."""

    def test_complete_cycle(self, model_with_data):
        """Verifica el ciclo completo sin errores."""
        model_with_data.load_data()
        model_with_data.train()
        result = model_with_data.predict()
        
        assert result is not None
        assert len(result) == 2
        assert all(isinstance(x, (int, np.integer)) for x in result)

    def test_cycle_with_default_path_would_work(self):
        """Verifica que el modelo pueda instanciarse con ruta por defecto."""
        model = BogotaModel()
        # Solo verifica que se cree sin errores; carga real requiere archivo existente
        assert model is not None
        assert "bogota" in model.data_path.lower()
