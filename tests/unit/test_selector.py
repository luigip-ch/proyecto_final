import pytest

from app.backend.selector import REGISTRY, get_model, list_lotteries
from app.ml.base_model import BaseModel


@pytest.mark.unit
class TestRegistry:
    def test_registry_is_dict(self):
        assert isinstance(REGISTRY, dict)

    def test_registry_contains_cundinamarca(self):
        assert "cundinamarca" in REGISTRY

    def test_registry_values_are_base_model_subclasses(self):
        for name, cls in REGISTRY.items():
            assert issubclass(cls, BaseModel), (
                f"{name} no extiende BaseModel"
            )


@pytest.mark.unit
class TestListLotteries:
    def test_returns_list(self):
        result = list_lotteries()
        assert isinstance(result, list)

    def test_contains_cundinamarca(self):
        result = list_lotteries()
        assert "cundinamarca" in result

    def test_matches_registry_keys(self):
        result = list_lotteries()
        assert set(result) == set(REGISTRY.keys())


@pytest.mark.unit
class TestGetModel:
    def test_returns_base_model_instance(self):
        model = get_model("cundinamarca")
        assert isinstance(model, BaseModel)

    def test_returns_correct_type_for_cundinamarca(self):
        from app.ml.cundinamarca.cundinamarca_ml import CundinamarcaModel

        model = get_model("cundinamarca")
        assert isinstance(model, CundinamarcaModel)

    def test_raises_value_error_for_unknown_lottery(self):
        with pytest.raises(ValueError, match="lotería no registrada"):
            get_model("loteria_inexistente")

    def test_raises_value_error_message_includes_name(self):
        with pytest.raises(ValueError, match="xyz_falsa"):
            get_model("xyz_falsa")

    def test_each_call_returns_new_instance(self):
        m1 = get_model("cundinamarca")
        m2 = get_model("cundinamarca")
        assert m1 is not m2
