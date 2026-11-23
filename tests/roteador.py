"""Transporte falso. Nenhum teste desta suíte abre rede."""

from __future__ import annotations

from datetime import datetime, timezone

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc).timestamp()
CANAL_A = "UC" + "a" * 22
CANAL_B = "UC" + "b" * 22
CANAL_C = "UC" + "c" * 22


def publicado(dias: float) -> str:
    return datetime.fromtimestamp(NOW - dias * 86400, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def search_item(video_id: str, title: str, channel_id: str, channel_title: str, dias: float) -> dict:
    return {
        "id": {"kind": "youtube#video", "videoId": video_id},
        "snippet": {
            "publishedAt": publicado(dias),
            "channelId": channel_id,
            "title": title,
            "description": "prévia",
            "channelTitle": channel_title,
            "thumbnails": {"medium": {"url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"}},
            "liveBroadcastContent": "none",
        },
    }


def video_item(
    video_id: str,
    title: str,
    channel_id: str,
    channel_title: str,
    dias: float,
    *,
    views: int,
    duration: str,
    caption: bool,
    tags: list[str] | None = None,
    description: str = "",
    likes: int = 10,
) -> dict:
    return {
        "id": video_id,
        "snippet": {
            "publishedAt": publicado(dias),
            "channelId": channel_id,
            "title": title,
            "description": description,
            "tags": tags or [],
            "channelTitle": channel_title,
            "thumbnails": {"medium": {"url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"}},
            "liveBroadcastContent": "none",
        },
        "contentDetails": {"duration": duration, "caption": "true" if caption else "false"},
        "statistics": {"viewCount": str(views), "likeCount": str(likes), "commentCount": "2"},
    }


def channel_item(channel_id: str, title: str, subs: int | None, hidden: bool = False) -> dict:
    stats = {"videoCount": "40", "hiddenSubscriberCount": hidden}
    if subs is not None and not hidden:
        stats["subscriberCount"] = str(subs)
    return {
        "id": channel_id,
        "snippet": {"title": title},
        "statistics": stats,
        "contentDetails": {"relatedPlaylists": {"uploads": "UU" + channel_id[2:]}},
    }


DESCRICAO_CAPITULOS = "0:00 abertura\n0:45 massa\n2:10 forno\n"


def amostra_busca() -> tuple[list[dict], list[dict], list[dict]]:
    buscas = [
        search_item("vid00000001", "pao caseiro facil", CANAL_A, "Forno Pequeno", 100),
        search_item("vid00000002", "COMO fazer pao?", CANAL_B, "Cozinha B", 400),
        search_item("vid00000003", "pao", CANAL_A, "Forno Pequeno", 20),
    ]
    videos = [
        video_item(
            "vid00000001",
            "pao caseiro facil",
            CANAL_A,
            "Forno Pequeno",
            100,
            views=1000,
            duration="PT8M",
            caption=True,
            tags=["Pao", "caseiro"],
        ),
        video_item(
            "vid00000002",
            "COMO fazer pao?",
            CANAL_B,
            "Cozinha B",
            400,
            views=5000,
            duration="PT20M",
            caption=False,
            tags=["pao"],
            description=DESCRICAO_CAPITULOS,
        ),
        video_item(
            "vid00000003",
            "pao",
            CANAL_A,
            "Forno Pequeno",
            20,
            views=2000,
            duration="PT3M",
            caption=True,
            tags=["pao", "rapido"],
        ),
    ]
    canais = [
        channel_item(CANAL_A, "Forno Pequeno", 50_000),
        channel_item(CANAL_B, "Cozinha B", 80_000),
    ]
    return buscas, videos, canais


def amostra_concorrente() -> tuple[dict, list[dict], list[dict]]:
    canal = channel_item(CANAL_C, "Padaria C", 300_000)
    videos = []
    playlist = []
    views = [100, 100, 100, 100, 400]
    idades = [80, 73, 66, 59, 52]
    for indice, (view, idade) in enumerate(zip(views, idades), start=1):
        video_id = f"conc000000{indice}"
        titulo = f"receita de pao caseiro {indice}"
        videos.append(
            video_item(
                video_id,
                titulo,
                CANAL_C,
                "Padaria C",
                idade,
                views=view,
                duration="PT10M",
                caption=indice <= 3,
            )
        )
        playlist.append({"contentDetails": {"videoId": video_id, "videoPublishedAt": publicado(idade)}})
    return canal, videos, playlist


class Roteador:
    def __init__(self, sugestoes: dict[str, list[str]] | None = None, busca_extra: dict | None = None):
        self.calls: list[dict] = []
        self.posts: list[dict] = []
        self.sugestoes = sugestoes or {"pao caseiro": ["pao caseiro facil", "pao caseiro integral"]}
        buscas, videos, canais = amostra_busca()
        canal_c, videos_c, playlist = amostra_concorrente()
        self.busca = {"pao caseiro": buscas}
        if busca_extra:
            self.busca.update(busca_extra)
        self.videos = {v["id"]: v for v in videos}
        for video in videos_c:
            self.videos[video["id"]] = video
        self.canais = {c["id"]: c for c in canais}
        self.canais[canal_c["id"]] = canal_c
        self.playlists = {"UULF" + CANAL_C[2:]: playlist}

    def get_json(self, url: str, params: dict | None = None):
        params = dict(params or {})
        self.calls.append({"url": url, "params": params})
        path = url.split("?")[0].rstrip("/")
        if "complete/search" in path:
            consulta = params.get("q", "")
            return [consulta, self.sugestoes.get(consulta, [])]
        if path.endswith("/youtube/v3/search"):
            return {"items": self.busca.get(params.get("q"), [])}
        if path.endswith("/videos"):
            ids = [i for i in (params.get("id") or "").split(",") if i]
            return {"items": [self.videos[i] for i in ids if i in self.videos]}
        if path.endswith("/channels"):
            ids = [i for i in (params.get("id") or "").split(",") if i]
            return {"items": [self.canais[i] for i in ids if i in self.canais]}
        if path.endswith("/playlistItems"):
            return {"items": self.playlists.get(params.get("playlistId"), [])}
        raise AssertionError(f"GET inesperado: {path}")

    def post_json(self, url: str, payload: dict, params: dict | None = None):
        self.posts.append({"url": url, "payload": payload, "params": params or {}})
        raise AssertionError("POST inesperado")

    def get_bytes(self, url: str) -> bytes:
        self.calls.append({"url": url, "params": {}})
        return b"\xff\xd8\xff\xd9"

    def urls(self) -> list[str]:
        return [c["url"] for c in self.calls]
