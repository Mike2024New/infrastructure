from infrastructure.http_clients.downloader import Downloader
from infrastructure.http_clients.adapters.hf_adapter import adpater_download_from_hf

__all__ = [
    'Downloader',  # загрузчик
    'adpater_download_from_hf'  # адаптеры для загрузки
]
