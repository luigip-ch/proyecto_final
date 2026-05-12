"""Tests unitarios para el modelo de predicción de la Lotería de Boyacá."""

import os
import tempfile

import pandas as pd
import pytest

from app.ml.boyaca.boyaca_ml import BoyacaModel


@pytest.fixture
def sample_boyaca_data():
    """Fixture que proporciona datos de prueba compatibles con BoyacaModel."""
    data = {
        "Tipo de Premio": ["Mayor"] * 7,
        "Fecha del Sorteo": [
            "01/01/2024",
            "08/01/2024",
            "15/01/2024",
            "22/01/2024",
            "29/01/2024",
            "05/02/2024",
            "12/02/2024",
        ],
        "Número del Sorteo": [1, 2, 3, 4, 5, 6, 7],
        "Numero billete ganador": [1234, 2345, 3456, 4567, 5678, 6789, 7890],
        "Numero serie ganadora": [10, 20, 30, 40, 50, 60, 70],
    }
    return pd.DataFrame(data)


class TestBoyacaModel:
    """Suite de tests para BoyacaModel."""

    def test_init_default_path(self):
        model = BoyacaModel()
        expected_path = os.path.normpath("app/bd/historical/loteria_boyaca/boyaca_historico.csv")
        assert model.data_path == expected_path

    def test_init_custom_path(self, tmp_path):
        custom_path = tmp_path / "custom_boyaca.csv"
        model = BoyacaModel(data_path=str(custom_path))
        assert model.data_path == str(custom_path)

    def test_load_data_file_not_found(self):
        model = BoyacaModel(data_path="nonexistent.csv")
        with pytest.raises(FileNotFoundError, match="Archivo de datos no encontrado"):
            model.load_data()

    def test_load_data_parses_temporal_features(self, sample_boyaca_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()

            assert "Año" in model.df.columns
            assert "Mes" in model.df.columns
            assert "DiaSemana" in model.df.columns
            assert "prev_miles" in model.df.columns
            assert model.last_features is not None
            assert model.last_features.iloc[0]["Numero del Sorteo"] == 8

        os.unlink(f.name)

    def test_load_data_filters_prize_type(self, sample_boyaca_data):
        mixed_data = sample_boyaca_data.copy()
        mixed_data.loc[0, "Tipo de Premio"] = "Secos"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            mixed_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()

            assert all(model.df["Tipo de Premio"] == "Mayor")
            assert len(model.df) == 5

        os.unlink(f.name)

    def test_train_requires_load_data(self):
        model = BoyacaModel()
        with pytest.raises(RuntimeError, match=r"Debe llamar a load_data\(\) antes de train\(\)"):
            model.train()

    def test_train_builds_models(self, sample_boyaca_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            assert model.models is not None
            assert set(model.models.keys()) == {
                "miles",
                "centenas",
                "decenas",
                "unidades",
                "serie_hundreds",
                "serie_tens",
                "serie_units",
            }

        os.unlink(f.name)

    def test_predict_requires_train(self, sample_boyaca_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()

            with pytest.raises(RuntimeError, match=r"Debe llamar a train\(\) antes de predict\(\)"):
                model.predict()

        os.unlink(f.name)

    def test_predict_returns_correct_format(self, sample_boyaca_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            result = model.predict()
            assert isinstance(result, list)
            assert len(result) == 5
            assert all(isinstance(x, int) for x in result)
            assert all(0 <= result[i] <= 9 for i in range(4))
            assert 0 <= result[4] <= 999

        os.unlink(f.name)

    def test_predict_with_seed_reproducible(self, sample_boyaca_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            result1 = model.predict(seed=42)
            result2 = model.predict(seed=42)
            assert result1 == result2

        os.unlink(f.name)

    def test_predict_without_seed_produces_results(self, sample_boyaca_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            results = [tuple(model.predict()) for _ in range(5)]
            assert len(results) == 5
            assert all(len(r) == 5 for r in results)

        os.unlink(f.name)
