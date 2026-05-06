import csv
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from app.ml.risaralda.risaralda_ml import RisaraldaModel


@pytest.mark.unit
class TestRisaraldaModel:
    def test_load_data_raises_when_file_missing(self, tmp_path: Path):
        model = RisaraldaModel(data_path=str(tmp_path / "no_existe.csv"))

        with pytest.raises(FileNotFoundError, match="Archivo de datos no encontrado"):
            model.load_data()

    def test_load_data_parses_csv_and_creates_expected_columns(self, tmp_path: Path):
        csv_path = tmp_path / "risaralda_historico.csv"
        fieldnames = [
            "Fecha del Sorteo",
            "Tipo de Premio",
            "Numero billete ganador",
            "Numero serie ganadora",
        ]
        rows = [
            {
                "Fecha del Sorteo": "01/01/2020",
                "Tipo de Premio": "Mayor",
                "Numero billete ganador": "123",
                "Numero serie ganadora": "4",
            },
            {
                "Fecha del Sorteo": "02/01/2020",
                "Tipo de Premio": "Mayor",
                "Numero billete ganador": "0456",
                "Numero serie ganadora": "7",
            },
        ]
        with open(csv_path, mode="w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        model = RisaraldaModel(data_path=str(csv_path))
        model.load_data()

        assert model.df is not None
        assert all(col in model.df.columns for col in [
            "NUMERO", "d0", "d1", "d2", "d3", "SERIE",
            "d0_lag1", "d1_lag1", "d2_lag1", "d3_lag1", "SERIE_lag1",
        ])
        assert model.df.iloc[0]["NUMERO"] == "0123"
        assert model.df.iloc[1]["NUMERO"] == "0456"
        assert list(model.df["d0"]) == [0, 0]
        assert list(model.df["SERIE"]) == [4, 7]

    def test_train_raises_if_load_data_not_called(self):
        model = RisaraldaModel()

        with pytest.raises(RuntimeError, match="Debe llamar a load_data"):
            model.train()

    def test_predict_uses_trained_models_and_scaler(self):
        model = RisaraldaModel()
        model.df = pd.DataFrame([
            {
                "Año": 2024,
                "Mes": 5,
                "d0": 1,
                "d1": 2,
                "d2": 3,
                "d3": 4,
                "SERIE": 5,
            }
        ])

        scaler = MagicMock()
        scaler.transform.return_value = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
        model.scaler = scaler

        model.models = {
            "d0": MagicMock(predict=MagicMock(return_value=[7])),
            "d1": MagicMock(predict=MagicMock(return_value=[7])),
            "d2": MagicMock(predict=MagicMock(return_value=[7])),
            "d3": MagicMock(predict=MagicMock(return_value=[7])),
            "SERIE": MagicMock(predict=MagicMock(return_value=[8])),
        }

        prediction = model.predict()

        assert prediction == [7, 7, 7, 7, 8]
        scaler.transform.assert_called_once()
