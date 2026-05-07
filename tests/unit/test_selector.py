"""Valida el registro y selector de modelos de lotería disponibles."""

import pytest

from app.backend.selector import REGISTRY, get_model, list_lotteries
from app.ml.base_model import BaseModel


@pytest.mark.unit
class TestRegistry:
    """Pruebas del registro central de modelos disponibles."""

    def test_registry_is_dict(self):
        """Verifica que el registro sea un diccionario."""
        assert isinstance(REGISTRY, dict)

    def test_registry_contains_cundinamarca(self):
        """Verifica que Cundinamarca esté registrada."""
        assert "cundinamarca" in REGISTRY

    def test_registry_values_are_base_model_subclasses(self):
        """Verifica que cada modelo registrado extienda ``BaseModel``."""
        for name, cls in REGISTRY.items():
            assert issubclass(cls, BaseModel), (
                f"{name} no extiende BaseModel"
            )


@pytest.mark.unit
class TestListLotteries:
    """Pruebas para listar los slugs de loterías registradas."""

    def test_returns_list(self):
        """Verifica que ``list_lotteries`` retorne una lista."""
        result = list_lotteries()
        assert isinstance(result, list)

    def test_contains_cundinamarca(self):
        """Verifica que la lista incluya Cundinamarca."""
        result = list_lotteries()
        assert "cundinamarca" in result

    def test_matches_registry_keys(self):
        """Verifica que la lista coincida con las llaves del registro."""
        result = list_lotteries()
        assert set(result) == set(REGISTRY.keys())


@pytest.mark.unit
class TestGetModel:
    """Pruebas para instanciar modelos desde el selector."""

    def test_returns_base_model_instance(self):
        """Verifica que el selector retorne una instancia de ``BaseModel``."""
        model = get_model("cundinamarca")
        assert isinstance(model, BaseModel)

    def test_returns_correct_type_for_cundinamarca(self):
        """Verifica que el slug Cundinamarca instancie su modelo concreto."""
        from app.ml.cundinamarca.cundinamarca_ml import CundinamarcaModel

        model = get_model("cundinamarca")
        assert isinstance(model, CundinamarcaModel)

    def test_raises_value_error_for_unknown_lottery(self):
        """Verifica error cuando el slug solicitado no está registrado."""
        with pytest.raises(ValueError, match="lotería no registrada"):
            get_model("loteria_inexistente")

    def test_raises_value_error_message_includes_name(self):
        """Verifica que el mensaje de error incluya el slug inválido."""
        with pytest.raises(ValueError, match="xyz_falsa"):
            get_model("xyz_falsa")

    def test_each_call_returns_new_instance(self):
        """Verifica que cada llamada entregue una instancia nueva."""
        m1 = get_model("cundinamarca")
        m2 = get_model("cundinamarca")
        assert m1 is not m2
