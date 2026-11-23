from __future__ import annotations

from pathlib import Path

import pytest

from tests.roteador import NOW, Roteador
from youtube_seo.cache import FileCache
from youtube_seo.cliente import YouTubeClient
from youtube_seo.quota import QuotaLedger


@pytest.fixture
def agora():
    return lambda: NOW


@pytest.fixture
def roteador():
    return Roteador()


@pytest.fixture
def servicos(tmp_path: Path, roteador: Roteador, agora):
    cache = FileCache(tmp_path / "cache", now=agora)
    quota = QuotaLedger(tmp_path / "quota.json", now=agora)
    client = YouTubeClient("test-key", roteador, cache, quota)
    return {
        "cache": cache,
        "quota": quota,
        "client": client,
        "transport": roteador,
        "now": agora,
        "tmp": tmp_path,
    }
