"""Browser compatibility tests for REQ-090.

Prerequisites:
  1. Start the FastAPI backend from the project root:
       python -m uvicorn backend.main:app --reload
  2. Start the React/Vite frontend in another terminal:
       cd frontend/ChessAI
       npm install
       npm run dev -- --host 127.0.0.1
  3. Install test dependencies and browser engines:
       python -m pip install pytest playwright
       python -m playwright install chromium firefox webkit

Run from the project root:
  python -m pytest tests/browser_tests/test_browser_compatibility.py -v

Set CHESSAI_BASE_URL if the frontend is hosted somewhere other than
http://127.0.0.1:5173.

"""

import os

import pytest
from playwright.sync_api import Browser, BrowserType, Page, sync_playwright

BASE_URL = os.getenv("CHESSAI_BASE_URL", "http://127.0.0.1:5173")
BROWSER_ENGINES = ["chromium", "firefox", "webkit"]
VIEWPORTS = [
    pytest.param({"width": 1280, "height": 800}, id="desktop"),
    pytest.param({"width": 390, "height": 844}, id="mobile"),
]


@pytest.mark.parametrize("engine_name", BROWSER_ENGINES)
@pytest.mark.parametrize("viewport", VIEWPORTS)
def  test_req_090_application_runs_correctly_across_supported_browsers(engine_name: str, viewport: dict[str, int]) -> None:
    """
    REQ-090: Verify that the application works correctly in a supported modern browser.
    """
    # 1. SETUP: Define a matrix executing against multiple target web layout instances (e.g., Chrome, Firefox, Safari, Edge).
    # 2. ACT: Load the app across each browser engine profile layer.
    # 3. ASSERT: Verify that visual rendering benchmarks pass, CSS grid alignments match,
    #    and JavaScript engine compilation logs remain free of layout-breaking core errors.
    page_errors: list[str] = []
    console_errors: list[str] = []

    with sync_playwright() as playwright:
        browser_type: BrowserType = getattr(playwright, engine_name)
        browser: Browser = browser_type.launch()
        try:
            page: Page = browser.new_page(viewport=viewport)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on(
                "console",
                lambda message: console_errors.append(message.text)
                if message.type == "error"
                else None,
            )

            response = page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
            assert response is not None, f"{engine_name}: navigation returned no response"
            assert response.status < 400, (
                f"{engine_name}: app returned HTTP {response.status}"
            )
            assert page.title().strip().lower() == "chessai", (
                f"{engine_name}: unexpected document title: {page.title()!r}"
            )

            # Check key UI elements that should appear in the current React app.
            assert page.get_by_role("button", name="New game").is_visible(), (
                f"{engine_name}: New game button did not render"
            )
            assert page.locator("#difficulty-button").is_visible(), (
                f"{engine_name}: difficulty button did not render"
            )
            assert page.get_by_text("Your move (white)", exact=False).is_visible(), (
                f"{engine_name}: initial game status did not render"
            )

            # Find the board's CSS Grid container and check its layout geometry.
            board = page.locator(
                "div"
            ).evaluate_all(
                "elements => {"
                " const candidates = elements.filter(el => {"
                "  const style = getComputedStyle(el);"
                "  return style.display === 'grid' &&"
                "    style.gridTemplateColumns.split(' ').length === 8;"
                " });"
                " if (!candidates.length) return null;"
                " candidates.sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width);"
                " const r = candidates[0].getBoundingClientRect();"
                " return {width: r.width, height: r.height, columns: getComputedStyle(candidates[0]).gridTemplateColumns.split(' ').length};"
                "}"
            )
            assert board is not None, (
                f"{engine_name}: could not find an 8-column CSS Grid chessboard"
            )
            assert board["columns"] == 8, f"{engine_name}: board should have 8 columns"
            assert board["width"] > 0 and board["height"] > 0, (
                f"{engine_name}: board has zero-sized layout"
            )
            ratio = board["width"] / board["height"]
            assert 0.90 <= ratio <= 1.10, (
                f"{engine_name}: board is not approximately square (ratio={ratio:.3f})"
            )

            # Key controls must remain inside the visible viewport (no horizontal overflow).
            dimensions = page.evaluate(
                "({scrollWidth: document.documentElement.scrollWidth, "
                "clientWidth: document.documentElement.clientWidth})"
            )
            assert dimensions["scrollWidth"] <= dimensions["clientWidth"] + 1, (
                f"{engine_name}: horizontal overflow at viewport {viewport}: {dimensions}"
            )

            assert not page_errors, (
                f"{engine_name}: JavaScript page errors: {page_errors}"
            )
            assert not console_errors, (
                f"{engine_name}: browser console errors: {console_errors}"
            )
        finally:
            browser.close()