from __future__ import annotations
from urllib import robotparser

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


class WebFetcher:
    def __init__(self, llm_client=None):
        self.timeout = 10
        self.llm_client = llm_client
        self.headers = {"User-Agent": "SovereignAgent/1.0 (+local)"}

    def execute(self, args: dict) -> str:
        action = args.get("action")
        if not action or not hasattr(self, action):
            return f"Unsupported web action: {action}"
        call_args = {k: v for k, v in args.items() if k != "action"}
        return str(getattr(self, action)(**call_args))

    def search(self, query: str, max_results: int = 5):
        results = []
        try:
            with DDGS() as ddgs:
                for item in ddgs.text(query, max_results=max_results):
                    results.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("href", ""),
                            "snippet": item.get("body", ""),
                        }
                    )
        except Exception as exc:
            return [{"title": "Search failed", "url": "", "snippet": str(exc)}]
        return results

    def fetch_page(self, url: str) -> str:
        if not self._allowed_by_robots(url):
            return f"Blocked by robots.txt: {url}"

        resp = requests.get(url, headers=self.headers, timeout=self.timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        text = " ".join(chunk.strip() for chunk in soup.stripped_strings)
        return text

    def fetch_json(self, url: str, headers: dict | None = None):
        merged_headers = dict(self.headers)
        merged_headers.update(headers or {})
        resp = requests.get(url, headers=merged_headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def summarize_page(self, url: str) -> str:
        text = self.fetch_page(url)
        if text.startswith("Blocked by robots.txt"):
            return text

        if self.llm_client is not None:
            summary_prompt = (
                "Summarize the page content below in exactly 3 concise bullet points.\n"
                "Return plain text bullets only, one per line.\n\n"
                f"Page URL: {url}\n\n"
                f"Content:\n{text[:8000]}"
            )
            try:
                return self.llm_client.complete(summary_prompt)
            except Exception:
                pass

        chunks = [s.strip() for s in text.split(".") if s.strip()]
        bullets = chunks[:3] if chunks else ["No readable content found."]
        return "\n".join(f"- {b}" for b in bullets)

    def _allowed_by_robots(self, url: str) -> bool:
        parsed = requests.utils.urlparse(url)
        rp = robotparser.RobotFileParser()
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            return True
