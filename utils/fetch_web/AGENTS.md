# utils/fetch_web Working Notes

## Identity

- `utils/fetch_web` is a small utility that opens or captures web pages with Patchright Chrome.
- `fetch_site.py` visits a URL and saves `page.html`, `page.png`, `meta.json`, and `run.log`.
- `launch_chrome.py` keeps a Chrome window open for cases that need manual interaction, such as preparing logins/cookies.
- `__init__.py` exposes no public API but defines the internal constant `_PROFILE_DIR` shared by both scripts.

## Runtime assumptions

- Run with the Python from the root `.venv`. Do not use the OS-global `python3`/`pip`.
- `patchright==1.59.1` and the Google Chrome channel are assumed. On a fresh environment without the browser, run the root bootstrap and then install it with `.venv/bin/patchright install chrome`.
- Both scripts use `launch_persistent_context(user_data_dir=_PROFILE_DIR, channel="chrome", headless=False, no_viewport=True)`.
- Patchright loses its bot-detection evasion in headless mode, so it always runs headed. No headless option is provided.

## File/state caveats

- The profile path is hardcoded to `~/Documents/patchright_profile` (`__init__.py:_PROFILE_DIR`). Both scripts use the same profile, so cookies and login state are shared.
- Do not run `fetch_site.py` and `launch_chrome.py` at the same time — they share `_PROFILE_DIR`, and Patchright/Chrome does not allow multiple browser instances on the same User Data Directory. To capture multiple URLs, the current implementation runs `fetch_site.py` serially.
- `fetch_site.py` deletes the existing contents of the `store` directory at startup before writing fresh results. Reusing a `store` loses the previous capture.
- `launch_chrome.py` intentionally opens an OS window and does not exit until the user closes every browser window.

## Verification after changes

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python utils/fetch_web/fetch_site.py --help
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python utils/fetch_web/launch_chrome.py --help
```

Run the headed smoke test with a `data:` URL and a `store` under `.temp_files/`. If `store` ends up containing all of `page.html`, `page.png`, `meta.json`, and `run.log`, the basic capture path is healthy.
