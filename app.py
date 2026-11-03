import os

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = (os.getenv("OPENAI_API_KEY") or "").strip()
OPENAI_MODEL = (os.getenv("OPENAI_MODEL") or "").strip() or "gpt-6-astra"

# 지원 언어: 버튼 이름 -> (모델에 전달할 언어명, 해당 언어로 쓴 이름)
# 언어를 추가하려면 이 딕셔너리에 한 줄만 추가하면 된다.
# 국기 이모지는 Windows에서 "US" 같은 글자로 표시되므로 쓰지 않는다.
LANGUAGES = {
    "영어": ("English", "English"),
    "일본어": ("Japanese", "日本語"),
    "베트남어": ("Vietnamese", "Tiếng Việt"),
}

SYSTEM_PROMPT = (
    "You are a professional translator. Translate the user's text into {target_language}. "
    "Output only the translated text without explanations, notes, or quotation marks. "
    "Preserve line breaks and formatting."
)

TEMPERATURE = 0.2

# 한 번에 번역할 수 있는 최대 글자 수 (응답 속도·토큰 한도·비용 보호)
MAX_CHARS = 5000

# 크레딧/사용량 부족을 뜻하는 429 오류 코드 (일시적인 요청 한도 초과와 구분)
QUOTA_ERROR_CODES = {"insufficient_quota", "credit_balance_exhausted"}

# 색상은 고정하지 않고 Streamlit 테마를 그대로 따른다 (라이트/다크 모드 모두 대응)
CUSTOM_CSS = """
<style>
h1, h3 { word-break: keep-all; }
div[data-testid="stButton"] button { border-radius: 999px; font-weight: 600; }
.st-key-result_card [data-testid="stText"] {
    font-family: inherit; font-size: 1.05rem; line-height: 1.7; white-space: pre-wrap;
}
</style>
"""


class TranslationError(Exception):
    """사용자에게 보여줄 메시지를 담은 번역 오류."""


@st.cache_resource
def get_client():
    """OpenAI 클라이언트를 한 번만 만들어 재사용한다.

    크레딧 부족처럼 재시도해도 소용없는 429 오류를 오래 기다리지 않도록 재시도는 1회로 줄인다.
    """
    return OpenAI(api_key=OPENAI_API_KEY, max_retries=1)


@st.cache_resource
def _model_options():
    """모델이 temperature를 지원하는지 기억한다. (앱 실행 동안 유지)"""
    return {"supports_temperature": True}


def _is_unsupported_temperature(error):
    """temperature 파라미터를 지원하지 않는 모델이라는 400 오류인지 확인한다."""
    return error.param == "temperature" or "temperature" in str(error).lower()


def _request_translation(text, target_language):
    """OpenAI에 번역을 요청한다. temperature를 거부하는 모델이면 빼고 한 번 더 요청한다."""
    options = _model_options()
    params = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT.format(target_language=target_language)},
            {"role": "user", "content": text},
        ],
    }
    if options["supports_temperature"]:
        try:
            return get_client().chat.completions.create(**params, temperature=TEMPERATURE)
        except openai.BadRequestError as e:
            if not _is_unsupported_temperature(e):
                raise
            options["supports_temperature"] = False
    return get_client().chat.completions.create(**params)


def _mask_secret(message):
    """오류 메시지에 API 키가 들어 있으면 가린다."""
    if OPENAI_API_KEY:
        message = message.replace(OPENAI_API_KEY, "***")
    return message


def translate(text, target_language):
    """text를 target_language로 번역해 결과 문자열을 반환한다."""
    try:
        response = _request_translation(text, target_language)
    except openai.AuthenticationError:
        raise TranslationError("API 키가 올바르지 않습니다. .env 파일의 OPENAI_API_KEY를 확인해주세요.")
    except (openai.NotFoundError, openai.PermissionDeniedError):
        raise TranslationError(
            f"모델 '{OPENAI_MODEL}'을(를) 사용할 수 없습니다. .env의 OPENAI_MODEL 값과 계정의 모델 접근 권한을 확인해주세요."
        )
    except openai.RateLimitError as e:
        if e.code in QUOTA_ERROR_CODES or e.type == "insufficient_quota":
            raise TranslationError(
                "OpenAI 계정의 크레딧(사용량)이 부족합니다. OpenAI 결제 설정에서 크레딧을 충전한 뒤 다시 시도해주세요."
            )
        raise TranslationError("요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
    except openai.APIConnectionError:
        raise TranslationError("OpenAI 서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요.")
    except openai.OpenAIError as e:
        raise TranslationError(f"번역 중 오류가 발생했습니다: {_mask_secret(str(e))}")

    content = response.choices[0].message.content if response.choices else None
    if not content or not content.strip():
        raise TranslationError("번역 결과가 비어 있습니다. 다시 시도해주세요.")
    return content.strip()


def init_state():
    """session_state 기본값을 설정한다."""
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("result_label", None)
    st.session_state.setdefault("source_text", None)
    st.session_state.setdefault("selected_label", None)
    st.session_state.setdefault("pending_label", None)


def select_language(label):
    """버튼 콜백: 화면을 그리기 전에 누른 언어를 기록한다.

    입력이 비어 있으면 번역하지 않으므로 버튼 강조도 바꾸지 않는다.
    (강조된 버튼과 결과 언어가 어긋나지 않게 하기 위함)
    """
    st.session_state.pending_label = label
    if st.session_state.get("source_input", "").strip():
        st.session_state.selected_label = label


def render_language_buttons():
    """언어 버튼을 같은 너비로 나란히 배치한다."""
    cols = st.columns(len(LANGUAGES))
    for col, (label, (_, native_name)) in zip(cols, LANGUAGES.items()):
        col.button(
            f"{label} · {native_name}",
            key=f"btn_{label}",
            type="primary" if st.session_state.selected_label == label else "secondary",
            width="stretch",
            disabled=not OPENAI_API_KEY,
            on_click=select_language,
            args=(label,),
        )


def handle_translation(text):
    """버튼이 눌렸으면 번역을 실행하고 결과를 session_state에 저장한다."""
    label = st.session_state.pending_label
    st.session_state.pending_label = None
    if not label:
        return

    if not text.strip():
        st.warning("번역할 텍스트를 입력해주세요.")
        return

    try:
        with st.spinner("번역 중..."):
            result = translate(text, LANGUAGES[label][0])
    except TranslationError as e:
        st.session_state.result = None
        st.error(str(e))
    else:
        st.session_state.result = result
        st.session_state.result_label = label
        st.session_state.source_text = text


def render_result(text):
    """번역 결과 카드와 복사 영역을 표시한다."""
    result = st.session_state.result
    if not result:
        st.subheader("번역 결과")
        st.caption("아직 번역된 내용이 없습니다.")
        return

    st.subheader(f"번역 결과 ({st.session_state.result_label})")
    if text != st.session_state.source_text:
        st.info("입력한 글이 바뀌었습니다. 다시 번역하려면 언어 버튼을 누르세요.")
    # st.text는 마크다운/HTML로 해석하지 않으므로 번역문이 그대로 표시된다.
    with st.container(border=True, key="result_card"):
        st.text(result)
    with st.expander("📋 복사하기"):
        st.code(result, language=None, wrap_lines=True)


def main():
    """화면을 구성하고 버튼 입력을 처리한다."""
    st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")
    init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    st.title("🌐 다국어 번역기")
    st.caption("번역할 글을 입력하고 언어를 선택하세요.")

    if not OPENAI_API_KEY:
        st.error(".env 파일에 OPENAI_API_KEY를 설정해주세요.")

    text = st.text_area(
        "번역할 텍스트",
        key="source_input",
        placeholder="번역할 텍스트를 입력하세요...",
        height=200,
        max_chars=MAX_CHARS,
        label_visibility="collapsed",
    )

    render_language_buttons()
    handle_translation(text)
    render_result(text)

    st.divider()
    st.caption(f"Powered by OpenAI {OPENAI_MODEL}")


if __name__ == "__main__":
    main()
