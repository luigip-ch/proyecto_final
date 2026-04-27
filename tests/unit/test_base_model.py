import pytest
from app.ml.base_model import BaseModel


# ── RED: estas pruebas fallarán hasta que base_model.py exista ──


@pytest.mark.unit
def test_cannot_instantiate_base_model_directly():
    with pytest.raises(TypeError):
        BaseModel()


@pytest.mark.unit
def test_subclass_missing_train_cannot_be_instantiated():
    class MissingTrain(BaseModel):
        def load_data(self) -> None: pass
        def predict(self) -> list[int]: return []

    with pytest.raises(TypeError):
        MissingTrain()


@pytest.mark.unit
def test_subclass_missing_predict_cannot_be_instantiated():
    class MissingPredict(BaseModel):
        def load_data(self) -> None: pass
        def train(self) -> None: pass

    with pytest.raises(TypeError):
        MissingPredict()


@pytest.mark.unit
def test_subclass_missing_load_data_cannot_be_instantiated():
    class MissingLoadData(BaseModel):
        def train(self) -> None: pass
        def predict(self) -> list[int]: return []

    with pytest.raises(TypeError):
        MissingLoadData()


@pytest.mark.unit
def test_valid_subclass_can_be_instantiated(concrete_model):
    assert concrete_model is not None


@pytest.mark.unit
def test_predict_returns_list(concrete_model):
    concrete_model.load_data()
    result = concrete_model.predict()
    assert isinstance(result, list)


@pytest.mark.unit
def test_predict_returns_list_of_ints(concrete_model):
    concrete_model.load_data()
    result = concrete_model.predict()
    assert all(isinstance(n, int) for n in result)
