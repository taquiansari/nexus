"""
NEXUS Web Researcher Worker — Search and scrape web content.
"""
from __future__ import annotations
import json
import logging
from workers.base_worker import BaseWorker, WorkerResult

logger = logging.getLogger(__name__)


class WebResearcher(BaseWorker):
    name = "WebResearcher"

    async def _execute(
        self,
        instruction: str,
        context: dict,
        uploaded_files: list[str],
    ) -> WorkerResult:
        try:
            from duckduckgo_search import DDGS

            # Extract search query from instruction
            query = instruction[:200]  # Use instruction as query

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=5):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })

            if not results:
                return WorkerResult(
                    success=False,
                    error="No search results found."
                )

            output = f"Found {len(results)} results for: {query}\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. {r['title']}\n   {r['url']}\n   {r['snippet']}\n\n"

            return WorkerResult(
                success=True,
                output=output,
                data=results,
            )

        except ImportError:
            return WorkerResult(
                success=False,
                error="duckduckgo_search package not installed."
            )
        except Exception as e:
            return WorkerResult(
                success=False,
                error=f"Web research failed: {str(e)}",
            )
