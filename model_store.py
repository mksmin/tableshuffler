import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_data_path

MODEL_ID = "qwen3.5-0.8b-q8-0"
MODEL_REPO = "bartowski/Qwen_Qwen3.5-0.8B-GGUF"
MODEL_REVISION = "f36b1ea49a332ede8fe5f389bbf5b3575ef71f48"
MODEL_FILENAME = "Qwen_Qwen3.5-0.8B-Q8_0.gguf"
MODEL_SIZE = 835_325_024
MODEL_SHA256 = "7182e2362766bb9569209bbc24cf1a4c" "dfbb8ab161babdb2080c84fa62c08c2f"

MODELS_DIR_ENV = "TABLESHUFFLE_MODELS_DIR"


class ModelStoreError(RuntimeError): ...


class ModelNotInstalledError(ModelStoreError): ...


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    repo_id: str
    revision: str
    filename: str
    size_bytes: int
    sha256: str


DEFAULT_MODEL = ModelSpec(
    model_id=MODEL_ID,
    repo_id=MODEL_REPO,
    revision=MODEL_REVISION,
    filename=MODEL_FILENAME,
    size_bytes=MODEL_SIZE,
    sha256=MODEL_SHA256,
)


def get_models_directory() -> Path:
    configured_directory = os.environ.get(MODELS_DIR_ENV)

    if configured_directory:
        return (
            Path(
                configured_directory,
            )
            .expanduser()
            .resolve()
        )

    return (
        user_data_path(
            "TableShuffle",
            appauthor=False,
        )
        / "models"
    )


def get_model_path(
    spec: ModelSpec = DEFAULT_MODEL,
) -> Path:
    return get_models_directory() / spec.model_id / spec.revision / spec.filename


def validate_model_file(
    path: Path,
    spec: ModelSpec = DEFAULT_MODEL,
) -> None:
    if not path.is_file():
        raise ModelNotInstalledError(
            f"Локальная модель не найдена: {path}",
        )

    actual_size = path.stat().st_size

    if actual_size != spec.size_bytes:
        raise ModelStoreError(
            f"Неверный размер модели: {actual_size} байт. "
            f"Ожидалось: {spec.size_bytes}",
        )

    with path.open("rb") as model_file:
        file_signature = model_file.read(4)

    if file_signature != b"GGUF":
        raise ModelStoreError(
            f"Файл не является GGUF-моделью: {path}",
        )


def require_model(
    spec: ModelSpec = DEFAULT_MODEL,
) -> Path:
    path = get_model_path(spec)
    validate_model_file(path, spec)
    return path


def is_model_ready(
    spec: ModelSpec = DEFAULT_MODEL,
) -> bool:
    try:
        require_model(spec)
    except ModelStoreError:
        return False

    return True
