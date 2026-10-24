"""Cliente mínimo da Riot API com rate limit e retry."""
import collections
import logging
import time

import requests

log = logging.getLogger(__name__)


class RateLimiter:
    """Janelas deslizantes no formato do header X-App-Rate-Limit ("20:1,100:120")."""

    def __init__(self, spec: str):
        self.calls: collections.deque[float] = collections.deque()
        self.set_spec(spec)

    def set_spec(self, spec: str) -> None:
        self.spec = spec
        self.windows = [(int(n), float(s)) for n, s in (p.split(":") for p in spec.split(","))]

    def wait(self) -> None:
        while True:
            now = time.monotonic()
            longest = max(s for _, s in self.windows)
            while self.calls and now - self.calls[0] > longest:
                self.calls.popleft()
            sleep_for = 0.0
            for n, s in self.windows:
                recent = [t for t in self.calls if now - t < s]
                if len(recent) >= n:
                    sleep_for = max(sleep_for, s - (now - recent[-n]) + 0.05)
            if sleep_for <= 0:
                self.calls.append(now)
                return
            time.sleep(sleep_for)


class RiotClient:
    def __init__(self, api_key: str, platform: str, region: str, rate_spec: str):
        self.platform = platform
        self.region = region
        self.limiter = RateLimiter(rate_spec)
        self.session = requests.Session()
        self.session.headers["X-Riot-Token"] = api_key

    def _get(self, host: str, path: str, params: dict | None = None):
        url = f"https://{host}.api.riotgames.com{path}"
        for attempt in range(8):
            self.limiter.wait()
            try:
                r = self.session.get(url, params=params, timeout=30)
            except requests.RequestException as e:
                log.warning("erro de rede (%s), tentando de novo", e)
                time.sleep(2**attempt)
                continue

            spec = r.headers.get("X-App-Rate-Limit")
            if spec and spec != self.limiter.spec:
                self.limiter.set_spec(spec)

            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", 10)))
                continue
            if r.status_code >= 500:
                time.sleep(2**attempt)
                continue
            if r.status_code in (401, 403):
                raise SystemExit("Chave da API inválida ou expirada (chaves de dev duram 24h).")
            r.raise_for_status()
        raise RuntimeError(f"falha após várias tentativas: {url}")

    # league-v4
    def apex_league(self, tier: str, queue: str):
        return self._get(self.platform, f"/lol/league/v4/{tier}leagues/by-queue/{queue}")

    def entries_by_puuid(self, puuid: str):
        return self._get(self.platform, f"/lol/league/v4/entries/by-puuid/{puuid}") or []

    # match-v5
    def match_ids(self, puuid: str, queue_id: int, count: int, start_time: int | None):
        params = {"queue": queue_id, "type": "ranked", "start": 0, "count": count}
        if start_time:
            params["startTime"] = start_time
        return self._get(self.region, f"/lol/match/v5/matches/by-puuid/{puuid}/ids", params) or []

    def match(self, match_id: str):
        return self._get(self.region, f"/lol/match/v5/matches/{match_id}")

    def timeline(self, match_id: str):
        return self._get(self.region, f"/lol/match/v5/matches/{match_id}/timeline")
