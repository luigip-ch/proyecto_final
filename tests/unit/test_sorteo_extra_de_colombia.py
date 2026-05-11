"""Tests unitarios para el modelo de predicción del Sorteo Extra de Colombia."""

import os
import tempfile

import pandas as pd
import pytest

from app.ml.sorteo_extra_de_colombia.sorteo_extra_de_colombia_ml import SorteoExtraDeColombiaModel


@pytest.fixture
def sample_extra_data():
    """Fixture que proporciona datos de prueba compatibles con SorteoExtraDeColombiaModel."""
    # Para GridSearchCV con cv=3 se requieren suficientes filas
    data = {
        "Tipo de Premio": ["Mayor"] * 10,
        "Fecha del Sorteo": [
            "01/01/2024",
            "08/01/2024",
            "15/01/2024",
            "22/01/2024",
            "29/01/2024",
            "05/02/2024",
            "12/02/2024",
            "19/02/2024",
            "26/02/2024",
            "04/03/2024"
        ],
        "Numero billete ganador": [1234, 1234, 1234, 1234, 1234, 1234, 1234, 1234, 1234, 1234],
        "Numero serie ganadora": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    }
    return pd.DataFrame(data)


class TestSorteoExtraDeColombiaModel:
    """Suite de tests para SorteoExtraDeColombiaModel."""

    def test_init_default_path(self):
        model = SorteoExtraDeColombiaModel()
        expected_path = os.path.normpath("app/bd/historical/loteria_sorteo_extra/sorteo_extra_historico.csv")
        # El base dir depende de cómo se cargue localmente, podemos asegurar que termine en ese path
        assert model.data_path.endswith(os.path.normpath("loteria_sorteo_extra/sorteo_extra_historico.csv"))

    def test_init_custom_path(self, tmp_path):
        custom_path = tmp_path / "custom_extra.csv"
        model = SorteoExtraDeColombiaModel(data_path=str(custom_path))
        assert model.data_path == str(custom_path)

    def test_load_data_file_not_found(self):
        model = SorteoExtraDeColombiaModel(data_path="nonexistent.csv")
        with pytest.raises(FileNotFoundError, match="Archivo de datos no encontrado"):
            model.load_data()

    def test_load_data_parses_temporal_features(self, sample_extra_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_extra_data.to_csv(f.name, index=False)
            model = SorteoExtraDeColombiaModel(data_path=f.name)
            model.load_data()

            assert "mes" in model.df.columns
            assert "dia_semana" in model.df.columns
            assert "prev_miles" in model.df.columns
            assert model.last_features is not None
            assert len(model.last_features) == 1

        os.unlink(f.name)

    def test_load_data_filters_prize_type(self, sample_extra_data):
        mixed_data = sample_extra_data.copy()
        mixed_data.loc[0, "Tipo de Premio"] = "Secos"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            mixed_data.to_csv(f.name, index=False)
            model = SorteoExtraDeColombiaModel(data_path=f.name)
            model.load_data()

            assert all(model.df["Tipo de Premio"] == "Mayor")
            # 10 filas - 1 cambiada = 9. Luego se dropea el primer NA por el lag.
            # Por lo tanto deberían quedar 7 u 8 filas completas.
            assert len(model.df) > 0

        os.unlink(f.name)

    def test_train_requires_load_data(self):
        model = SorteoExtraDeColombiaModel()
        with pytest.raises(RuntimeError, match=r"Debe llamar a load_data\(\) antes de train\(\)"):
            model.train()

    def test_train_builds_models(self, sample_extra_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_extra_data.to_csv(f.name, index=False)
            model = SorteoExtraDeColombiaModel(data_path=f.name)
            model.load_data()
            model.train()

            assert model.models is not None
            assert set(model.models.keys()) == {
                "miles",
                "centenas",
                "decenas",
                "unidades",
                "serie"
            }

        os.unlink(f.name)

    def test_predict_requires_train(self, sample_extra_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_extra_data.to_csv(f.name, index=False)
            model = SorteoExtraDeColombiaModel(data_path=f.name)
            model.load_data()

            with pytest.raises(RuntimeError, match=r"Debe llamar a train\(\) antes de predict\(\)"):
                model.predict()

        os.unlink(f.name)

    def test_predict_returns_correct_format(self, sample_extra_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_extra_data.to_csv(f.name, index=False)
            model = SorteoExtraDeColombiaModel(data_path=f.name)
            model.load_data()
            model.train()

            result = model.predict()
            assert isinstance(result, list)
            assert len(result) == 5
            assert all(isinstance(x, int) for x in result)
            assert all(0 <= result[i] <= 9 for i in range(4))
            assert 0 <= result[4] <= 999

        os.unlink(f.name)

    def test_predict_with_seed_reproducible(self, sample_extra_data):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_extra_data.to_csv(f.name, index=False)
            model = SorteoExtraDeColombiaModel(data_path=f.name)
            model.load_data()
            model.train()

            result1 = model.predict(seed=42)
            result2 = model.predict(seed=42)
            assert result1 == result2

        os.unlink(f.name)
