# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project docs

- `PRD.md` — the source of truth for requirements (Korean). Feature IDs F-1 ~ F-9, exception handling (§11), and acceptance criteria (§12) are referenced by the prompts and reviews.
- `PROMPTS.md` — the 4-step build sequence (1: skeleton, 2: translation + error handling, 3: UI, 4: review against PRD). When asked to do "N단계", follow that step's prompt and do not change work owned by earlier steps (e.g. step 3 must not alter step 2's translation logic, error handling, or `session_state` behavior). Step 4 produces a review report first and modifies code only after the user approves.
- `REVIEW.md` — the step-4 review report: open issues, ranked by severity.

## Architecture

Single-file Streamlit app (`app.py`) that translates user text into English / Japanese / Vietnamese, one button per language, via the OpenAI Chat Completions API.

- Config: `.env` loaded with `python-dotenv` — `OPENAI_API_KEY` (required) and `OPENAI_MODEL` (default `gpt-6-astra`). The model ID is **lowercase**; `GPT-6-ASTRA` (as written in the PRD) returns 404. The local `.env` defines only the key. Changes to `.env` need an app restart (`load_dotenv` doesn't override existing env vars and the client is `st.cache_resource`-cached).
- `LANGUAGES` maps button label → (English language name sent to the model, native name shown on the button). Adding a language only requires a new entry. Flag emojis are deliberately not used: Windows renders them as "US"/"JP" letters.
- Rerun flow: button `on_click` callback (`select_language`) sets `selected_label` (button highlight) and `pending_label` before the script reruns; `handle_translation` consumes `pending_label` once, so a translation runs exactly once per click. Results live in `st.session_state` (`result`, `result_label`, `source_text`).
- `_request_translation()` sends `temperature`; if the model rejects it with a 400, it retries without it and remembers that in the `st.cache_resource` dict `_model_options()`. Real behavior of `gpt-6-astra` here is unverified (account had no credits at build time).
- `translate()` converts each OpenAI exception into `TranslationError` with a Korean user-facing message; 429s with `insufficient_quota` / `credit_balance_exhausted` are reported as out-of-credit, not as a retryable rate limit. Messages never include the API key.
- Translations are rendered with `st.text` (and `st.code` for copying) so model output is never interpreted as Markdown/HTML. `unsafe_allow_html` is used only for the constant CSS block.

## Commands

```bash
pip install -r requirements.txt
streamlit run app.py
```

There is no test suite or linter. On this machine `python` on PATH is the Microsoft Store stub; use Anaconda: `/c/Users/User/anaconda3/python.exe -m streamlit run app.py`. For headless checks, use `streamlit.testing.v1.AppTest` and patch `openai.resources.chat.completions.Completions.create` so tests don't call the real API.
