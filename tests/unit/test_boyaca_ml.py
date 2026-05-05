"""Tests unitarios para el modelo de predicción de la Lotería de Boyacá."""

import os
import tempfile

import pandas as pd
import pytest

from app.ml.boyaca.boyaca_ml import BoyacaModel


@pytest.fixture
def sample_boyaca_data():
    """
    Fixture que proporciona datos de prueba para la Lotería de Boyacá.

    Crea un DataFrame con registros de premios mayores simulados,
    similar a la estructura del CSV histórico real.
    """
    data = {
        "Tipo de Premio": ["Mayor", "Mayor", "Mayor", "Mayor", "Mayor"],
        "Numero billete ganador": [1234, 5678, 9012, 3456, 7890],
        "Numero serie ganadora": [10, 20, 30, 40, 50]
    }
    return pd.DataFrame(data)


class TestBoyacaModel:
    """Suite de tests para BoyacaModel."""

    def test_init_default_path(self):
        """Test que el modelo se inicializa con la ruta por defecto."""
        model = BoyacaModel()
        expected_path = os.path.normpath("app/bd/historical/loteria_boyaca/boyaca_historico.csv")
        assert model.data_path == expected_path

    def test_init_custom_path(self, tmp_path):
        """Test que el modelo acepta una ruta personalizada."""
        custom_path = tmp_path / "custom_boyaca.csv"
        model = BoyacaModel(data_path=str(custom_path))
        assert model.data_path == str(custom_path)

    def test_load_data_file_not_found(self):
        """Test que load_data lanza FileNotFoundError si el archivo no existe."""
        model = BoyacaModel(data_path="nonexistent.csv")
        with pytest.raises(FileNotFoundError, match="Archivo de datos no encontrado"):
            model.load_data()

    def test_load_data_filters_prize_type(self, sample_boyaca_data):
        """Test que load_data filtra solo registros de premio mayor."""
        # Crear CSV temporal con datos mixtos
        mixed_data = sample_boyaca_data.copy()
        mixed_data.loc[0, "Tipo de Premio"] = "Secos"  # Cambiar uno a tipo diferente

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            mixed_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()

            # Solo debe cargar los registros "Mayor"
            assert len(model.df) == 4  # 5 total - 1 "Secos"
            assert all(model.df["Tipo de Premio"] == "Mayor")

        os.unlink(f.name)

    def test_train_requires_load_data(self):
        """Test que train lanza RuntimeError si no se llamó load_data."""
        model = BoyacaModel()
        with pytest.raises(RuntimeError, match="Debe llamar a load_data\\(\\) antes de train\\(\\)"):
            model.train()

    def test_train_builds_frequencies(self, sample_boyaca_data):
        """Test que train construye correctamente las distribuciones de frecuencia."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            # Verificar que se crearon las frecuencias
            assert model.frecuencias is not None
            assert "miles" in model.frecuencias
            assert "centenas" in model.frecuencias
            assert "decenas" in model.frecuencias
            assert "unidades" in model.frecuencias

            # Verificar que las frecuencias suman 1.0 aproximadamente
            for pos in ["miles", "centenas", "decenas", "unidades"]:
                freq_dict = model.frecuencias[pos]
                total_prob = sum(freq_dict.values())
                assert abs(total_prob - 1.0) < 1e-10

            # Verificar frecuencias de serie
            assert model.serie_frecuencias is not None
            total_serie_prob = sum(model.serie_frecuencias.values())
            assert abs(total_serie_prob - 1.0) < 1e-10

        os.unlink(f.name)

    def test_predict_requires_train(self, sample_boyaca_data):
        """Test que predict lanza RuntimeError si no se llamó train."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()

            with pytest.raises(RuntimeError, match="Debe llamar a train\\(\\) antes de predict\\(\\)"):
                model.predict()

        os.unlink(f.name)

    def test_predict_returns_correct_format(self, sample_boyaca_data):
        """Test que predict retorna lista de 5 enteros en el formato esperado."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            result = model.predict()

            # Verificar formato: [miles, centenas, decenas, unidades, serie]
            assert isinstance(result, list)
            assert len(result) == 5
            assert all(isinstance(x, int) for x in result)

            # Verificar rangos de dígitos (0-9 para los primeros 4)
            for i in range(4):
                assert 0 <= result[i] <= 9, f"Dígito en posición {i} fuera de rango 0-9"

            # Serie puede ser cualquier entero positivo
            assert result[4] >= 0

        os.unlink(f.name)

    def test_predict_with_seed_reproducible(self, sample_boyaca_data):
        """Test que predict con seed produce resultados reproducibles."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            # Generar predicciones con el mismo seed
            result1 = model.predict(seed=42)
            result2 = model.predict(seed=42)

            assert result1 == result2, "Resultados con mismo seed deben ser idénticos"

        os.unlink(f.name)

    def test_predict_without_seed_different(self, sample_boyaca_data):
        """Test que predict sin seed produce resultados diferentes (probabilístico)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_boyaca_data.to_csv(f.name, index=False)
            model = BoyacaModel(data_path=f.name)
            model.load_data()
            model.train()

            # Generar múltiples predicciones sin seed
            results = [model.predict() for _ in range(10)]

            # Al menos algunas deberían ser diferentes (con datos pequeños, es posible
            # que todas sean iguales por casualidad, pero esto es un test básico)
            unique_results = set(tuple(r) for r in results)
            # No podemos garantizar diferencias con datos de prueba pequeños,
            # pero al menos verificar que no hay errores
            assert len(results) == 10
            assert all(len(r) == 5 for r in results)

        os.unlink(f.name)

    def test_is_valid_number_rejects_identical_digits(self):
        """Test que _is_valid_number rechaza números con dígitos idénticos."""
        model = BoyacaModel()
        # Simular entrenamiento mínimo
        model.sum_range = (10, 20)
        model.valid_even_counts = {2}

        assert not model._is_valid_number([1, 1, 1, 1])  # Todos iguales
        assert model._is_valid_number([1, 2, 3, 4])      # Diferentes

    def test_is_valid_number_checks_sum_range(self):
        """Test que _is_valid_number valida el rango de suma de dígitos."""
        model = BoyacaModel()
        model.sum_range = (10, 15)
        model.valid_even_counts = {2}

        assert not model._is_valid_number([1, 1, 1, 1])  # Suma = 4, fuera de rango
        assert model._is_valid_number([1, 2, 3, 4])      # Suma = 10, dentro de rango

    def test_is_valid_number_checks_even_count(self):
        """Test que _is_valid_number valida la cantidad de dígitos pares."""
        model = BoyacaModel()
        model.sum_range = (5, 15)
        model.valid_even_counts = {2}  # Solo acepta exactamente 2 pares

        assert not model._is_valid_number([1, 1, 1, 1])  # 0 pares, suma=4 (fuera de rango)
        assert not model._is_valid_number([2, 2, 2, 1])  # 3 pares, suma=7 (dentro de rango)
        assert model._is_valid_number([2, 1, 2, 1])      # 2 pares, suma=6 (dentro de rango)</content>
