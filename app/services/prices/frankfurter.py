from __future__ import annotations

from typing import Iterable, Dict
import aiohttp


class FrankfurterClient:
    def __init__(self, http: aiohttp.ClientSession):
        self.http = http
        self.base_url = "https://api.frankfurter.app"

    async def _nbu_rate_to_uah(self, code: str) -> float:
        """
        Returns: 1 <CODE> in UAH (e.g. USD->UAH).
        """
        code = code.upper()
        if code == "UAH":
            return 1.0

        url = f"https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode={code}&json"
        async with self.http.get(url) as r:
            r.raise_for_status()
            data = await r.json()


        if not data or "rate" not in data[0]:
            raise RuntimeError(f"NBU rate not found for {code}")

        return float(data[0]["rate"])

    async def latest(self, base: str, symbols: Iterable[str]) -> Dict[str, float]:
        base = base.upper()
        symbols = [s.upper() for s in symbols]


        if base == "UAH" or "UAH" in symbols:
            out: Dict[str, float] = {}

            if base != "UAH":

                base_to_uah = await self._nbu_rate_to_uah(base)
                for s in symbols:
                    if s == "UAH":
                        out["UAH"] = base_to_uah
                    else:

                        sym_to_uah = await self._nbu_rate_to_uah(s)
                        out[s] = base_to_uah / sym_to_uah
                return out


            for s in symbols:
                if s == "UAH":
                    out["UAH"] = 1.0
                else:
                    sym_to_uah = await self._nbu_rate_to_uah(s)
                    out[s] = 1.0 / sym_to_uah
            return out


        params = {"from": base, "to": ",".join(symbols)}
        async with self.http.get(f"{self.base_url}/latest", params=params) as r:
            r.raise_for_status()
            data = await r.json()

        rates = data.get("rates") or {}
        return {k.upper(): float(v) for k, v in rates.items()}
