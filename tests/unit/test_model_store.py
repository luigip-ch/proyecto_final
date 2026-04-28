"""Valida la persistencia en memoria y disco de modelos entrenados."""

from app.backend import model_store


class SerializableModel:
    """Modelo mínimo serializable para pruebas del store."""

    def __init__(self, value: int):
        """Inicializa un valor observable tras serializar y recargar."""
        self.value = value


def test_save_trained_model_writes_pickle_file(tmp_path, monkeypatch):
    """Verifica que guardar un modelo cree su archivo persistido."""
    monkeypatch.setattr(model_store, "MODEL_STORE_DIR", str(tmp_path))

    model_store.save_trained_model("cundinamarca", SerializableModel(10))

    assert (tmp_path / "cundinamarca.pkl").exists()


def test_get_trained_model_loads_from_disk(tmp_path, monkeypatch):
    """Verifica que el store recargue desde disco si la memoria está vacía."""
    monkeypatch.setattr(model_store, "MODEL_STORE_DIR", str(tmp_path))
    model_store.save_trained_model("cundinamarca", SerializableModel(20))
    model_store.clear_trained_models()

    model = model_store.get_trained_model("cundinamarca")

    assert model.value == 20


def test_get_trained_model_returns_none_when_file_missing(tmp_path, monkeypatch):
    """Verifica que una lotería sin artefacto persistido retorne ``None``."""
    monkeypatch.setattr(model_store, "MODEL_STORE_DIR", str(tmp_path))

    model = model_store.get_trained_model("cundinamarca")

    assert model is None


def test_clear_trained_models_can_delete_files(tmp_path, monkeypatch):
    """Verifica que la limpieza opcional elimine archivos persistidos."""
    monkeypatch.setattr(model_store, "MODEL_STORE_DIR", str(tmp_path))
    model_store.save_trained_model("cundinamarca", SerializableModel(30))

    model_store.clear_trained_models(delete_files=True)

    assert not (tmp_path / "cundinamarca.pkl").exists()
