import json
from datetime import datetime
from pathlib import Path
from types import TracebackType

import pytest
from fetch_web import fetch_site


class FailingPage:
    async def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        raise RuntimeError(f"navigation failed for {url}")


class SuccessfulPage:
    url = "https://example.test/final"

    async def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        return None

    async def wait_for_load_state(self, state: str, *, timeout: int) -> None:
        return None

    async def evaluate(self, script: str) -> int | None:
        if "scrollHeight" in script:
            return 100
        return None

    async def wait_for_timeout(self, timeout: int) -> None:
        return None

    async def title(self) -> str:
        return "Example Page"

    async def content(self) -> str:
        return "<html><title>Example Page</title></html>"

    async def screenshot(self, *, path: str, full_page: bool) -> None:
        Path(path).write_bytes(b"png")


class FakeContext:
    def __init__(self, page: FailingPage | SuccessfulPage) -> None:
        self.pages: list[FailingPage | SuccessfulPage] = [page]
        self.closed = False

    async def close(self) -> None:
        self.closed = True


class FakeChromium:
    def __init__(self, context: FakeContext) -> None:
        self._context = context

    async def launch_persistent_context(
        self,
        *,
        user_data_dir: str,
        channel: str,
        headless: bool,
        no_viewport: bool,
    ) -> FakeContext:
        return self._context


class FakePlaywright:
    def __init__(self, context: FakeContext) -> None:
        self.chromium = FakeChromium(context)


class FakeAsyncPlaywright:
    def __init__(self, context: FakeContext) -> None:
        self._context = context

    async def __aenter__(self) -> FakePlaywright:
        return FakePlaywright(self._context)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class FixedDatetime:
    @classmethod
    def now(cls) -> datetime:
        return datetime(2026, 1, 2, 3, 4, 5)


@pytest.mark.asyncio
async def test_fetch_writes_run_log_and_closes_context_when_navigation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = FakeContext(FailingPage())

    def fake_async_playwright() -> FakeAsyncPlaywright:
        return FakeAsyncPlaywright(context)

    monkeypatch.setattr(fetch_site, "async_playwright", fake_async_playwright)
    monkeypatch.setattr(fetch_site, "datetime", FixedDatetime)

    with pytest.raises(RuntimeError, match="navigation failed"):
        await fetch_site.fetch("https://example.test/page", tmp_path)

    assert context.closed
    assert (tmp_path / "run.log").read_text(encoding="utf-8").splitlines() == [
        "[03:04:05] goto https://example.test/page",
        "[03:04:05] failed: RuntimeError: navigation failed for https://example.test/page",
    ]


@pytest.mark.asyncio
async def test_fetch_writes_outputs_and_run_log_when_capture_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = FakeContext(SuccessfulPage())

    def fake_async_playwright() -> FakeAsyncPlaywright:
        return FakeAsyncPlaywright(context)

    monkeypatch.setattr(fetch_site, "async_playwright", fake_async_playwright)
    monkeypatch.setattr(fetch_site, "datetime", FixedDatetime)

    result = await fetch_site.fetch("https://example.test/page", tmp_path)

    assert result == 0
    assert context.closed
    assert (tmp_path / "page.html").read_text(encoding="utf-8") == "<html><title>Example Page</title></html>"
    assert (tmp_path / "page.png").read_bytes() == b"png"
    assert json.loads((tmp_path / "meta.json").read_text(encoding="utf-8")) == {
        "saved_at": "2026-01-02T03:04:05",
        "input_url": "https://example.test/page",
        "final_url": "https://example.test/final",
        "page_title": "Example Page",
        "profile_dir": str(Path.home() / "Documents" / "patchright_profile"),
        "store_dir": str(tmp_path),
        "html_chars": 40,
        "html_file": "page.html",
        "screenshot_file": "page.png",
    }
    assert (tmp_path / "run.log").read_text(encoding="utf-8").splitlines()[-1] == "[03:04:05] done"
