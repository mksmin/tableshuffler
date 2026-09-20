import hashlib
import logging
from pathlib import Path
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

from model_store import DEFAULT_MODEL
from model_store import ModelSpec
from model_store import ModelStoreError
from model_store import get_model_path
from model_store import validate_model_file

log = logging.getLogger(__name__)

DOWNLOAD_CHUNK_SIZE = 1024 * 1024
HASH_CHUNK_SIZE = 1024 * 1024 * 4
USER_AGENT = "TableShuffle/0.1"


class ModelDownloadError(ModelStoreError): ...


def get_model_download_url(
    spec: ModelSpec = DEFAULT_MODEL,
) -> str:
    return (
        f"https://huggingface.co/{spec.repo_id}"
        f"/resolve/{spec.revision}/{spec.filename}"
    )


def calculate_sha256(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as model_file:
        while chunk := model_file.read(HASH_CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def validate_downloaded_model(
    path: Path,
    spec: ModelSpec = DEFAULT_MODEL,
) -> None:
    validate_model_file(path, spec)

    log.info("Проверяю контрольную сумму модели")

    actual_sha256 = calculate_sha256(path)

    if actual_sha256 != spec.sha256:
        raise ModelDownloadError(
            f"Неверная контрольная сумма модели {actual_sha256}. "
            f"Ожидалось: {spec.sha256}",
        )


def download_model(
    spec: ModelSpec = DEFAULT_MODEL,
) -> Path:
    model_path = get_model_path(spec)

    if model_path.exists():
        try:
            validate_model_file(model_path, spec)
        except ModelStoreError as e:
            log.debug(
                "Существующая модель не прошла проверку: %s",
                e,
            )

        else:
            log.info("Модель уже установлена: %s", model_path)
            return model_path

    model_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    partial_path = model_path.with_suffix(
        model_path.suffix + ".part",
    )

    downloaded_bytes = partial_path.stat().st_size if partial_path.exists() else 0

    if downloaded_bytes > spec.size_bytes:
        log.info(
            "Удалю некорректную незавершенную загрузку",
        )
        partial_path.unlink()
        downloaded_bytes = 0

    if downloaded_bytes == spec.size_bytes:
        try:
            validate_downloaded_model(partial_path, spec)
        except ModelStoreError as e:
            log.debug(
                "Загруженный временный файл повреждён: %s",
                e,
            )
            partial_path.unlink()
            downloaded_bytes = 0
        else:
            partial_path.replace(model_path)
            log.info("Модуль установлена: %s", model_path)
            return model_path

    download_url = get_model_download_url(spec)

    headers = {
        "User-Agent": USER_AGENT,
    }

    if downloaded_bytes:
        headers["Range"] = f"bytes={downloaded_bytes}-"
        log.info(
            "Продолжаю загрузку модели с %.1f МБ",
            downloaded_bytes / 1024 / 1024,
        )
    else:
        log.info(
            "Начинаю загрузку модели размером %.1f МБ",
            spec.size_bytes / 1024 / 1024,
        )

    log.debug(
        "Адрес загрузки модели: %s",
        download_url,
    )

    request = Request(
        download_url,
        headers=headers,
    )

    try:
        with urlopen(
            request,
            timeout=60,
        ) as response:
            response_status = response.status
            content_range = response.headers.get(
                "Content-Range",
                "",
            )

            range_was_accepted = (
                downloaded_bytes > 0
                and response_status == 206
                and content_range.startswith(f"bytes {downloaded_bytes}-")
            )

            if downloaded_bytes and not range_was_accepted:
                log.info(
                    "Сервер не продолжил загрузку, начинаю заново",
                )
                downloaded_bytes = 0
                file_mode = "wb"
            else:
                file_mode = "ab"

            next_progress_percent = downloaded_bytes * 100 // spec.size_bytes
            next_progress_percent = (next_progress_percent // 5 + 1) * 5

            with partial_path.open(
                file_mode,
            ) as output_file:
                while chunk := response.read(DOWNLOAD_CHUNK_SIZE):
                    output_file.write(chunk)
                    downloaded_bytes += len(chunk)

                    current_percent = downloaded_bytes * 100 // spec.size_bytes

                    while current_percent >= next_progress_percent:
                        log.info(
                            "Загрузка модели: %d%%",
                            min(
                                next_progress_percent,
                                100,
                            ),
                        )
                        next_progress_percent += 5
    except (HTTPError, URLError, TimeoutError) as error:
        raise ModelDownloadError(
            f"Не удалось скачать модель: {error}",
        ) from error

    try:
        validate_downloaded_model(
            partial_path,
            spec,
        )
    except ModelStoreError:
        partial_path.unlink(
            missing_ok=True,
        )
        raise

    partial_path.replace(model_path)

    log.info("Модель установлена: %s", model_path)
    return model_path


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
    )

    download_model()
