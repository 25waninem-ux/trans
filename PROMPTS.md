# 다국어 번역기 단계별 개발 프롬프트

> `PRD.md`를 바탕으로 만든 단계별 프롬프트입니다. 한 단계씩 순서대로 AI에게 입력하고, 각 단계의 결과를 확인한 뒤 다음 단계로 넘어가세요.

---

## 1단계: 기본 뼈대 작성

```
PRD.md 파일을 읽고, 다국어 번역기 프로젝트의 기본 뼈대를 만들어줘.

[만들 파일]
1. requirements.txt — streamlit, openai, python-dotenv
2. .env.example — 아래 내용
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
   OPENAI_MODEL=gpt-6-astra
3. .gitignore — .env, __pycache__/, .venv/, *.pyc 포함
4. app.py — 아래 구조만 갖춘 뼈대

[app.py 뼈대 요구사항]
- load_dotenv()로 .env를 불러오고 OPENAI_API_KEY, OPENAI_MODEL(기본값 "gpt-6-astra")을 읽는다.
- 지원 언어는 딕셔너리 하나로 관리한다.
  LANGUAGES = {"영어": "English", "일본어": "Japanese", "베트남어": "Vietnamese"}
- 아래 함수들을 정의하되, 이번 단계에서는 실제 API 호출 없이 틀만 만든다.
  - get_client(): OpenAI 클라이언트를 만들어 반환
  - translate(text, target_language): 번역 결과 문자열 반환 (지금은 임시로 "[번역 예정] " + text 반환)
  - main(): 화면 구성
- main()에는 제목, 안내 문구, st.text_area 입력창, st.columns로 나란히 놓은 버튼 3개(영어/일본어/베트남어), 결과 표시 영역만 둔다.
- if __name__ == "__main__": main() 형태로 실행한다.

[주의]
- API 키를 코드에 직접 쓰지 마.
- 아직 디자인(CSS, 아이콘 등)은 신경 쓰지 마.
- 작성 후 `pip install -r requirements.txt`와 `streamlit run app.py`로 실행되는지 확인하는 방법을 알려줘.
```

**확인할 것:** 앱이 실행되고, 버튼을 누르면 `[번역 예정] 입력한 글`이 표시되는지.

---

## 2단계: 주요 기능 추가

```
PRD.md의 5장(기능 요구사항), 6장(번역 로직), 11장(예외 처리)에 맞춰 app.py에 실제 번역 기능을 추가해줘.

[번역 기능]
- translate() 함수에서 OpenAI 공식 Python SDK로 OPENAI_MODEL 모델을 호출한다.
- system 프롬프트:
  "You are a professional translator. Translate the user's text into {target_language}. Output only the translated text without explanations, notes, or quotation marks. Preserve line breaks and formatting."
- user 메시지에는 사용자가 입력한 원문을 넣는다.
- temperature는 0.2로 설정한다.
- 결과 문자열은 앞뒤 공백을 제거(strip)해서 반환한다.

[동작 흐름]
- 버튼을 누르면 st.spinner("번역 중...")를 띄우고 translate()를 호출한다.
- 번역 결과, 대상 언어명, 원문을 st.session_state에 저장해서 화면이 다시 그려져도 결과가 유지되게 한다.
- 다른 언어 버튼을 누르면 같은 원문을 그 언어로 다시 번역한다.

[입력 검증과 예외 처리]
- 입력이 비어 있거나 공백뿐이면 API를 호출하지 말고 st.warning("번역할 텍스트를 입력해주세요.")를 표시한다.
- OPENAI_API_KEY가 없으면 화면 상단에 st.error(".env 파일에 OPENAI_API_KEY를 설정해주세요.")를 표시하고 버튼을 비활성화(disabled=True)한다.
- openai 라이브러리의 예외를 종류별로 나눠 처리한다.
  - AuthenticationError → API 키가 올바르지 않다는 안내
  - NotFoundError / PermissionDeniedError → 모델명(OPENAI_MODEL)이나 접근 권한을 확인하라는 안내
  - RateLimitError → 요청 한도 초과, 잠시 후 다시 시도하라는 안내
  - APIConnectionError → 네트워크 연결을 확인하라는 안내
  - 그 밖의 예외 → "번역 중 오류가 발생했습니다: {오류 내용}"
- 어떤 오류가 나도 앱이 멈추지 않아야 하고, 오류 메시지에 API 키가 노출되면 안 된다.

[코드 품질]
- OpenAI 클라이언트는 @st.cache_resource로 한 번만 만든다.
- 함수마다 짧은 한국어 docstring을 단다.

작성 후 바뀐 부분을 요약하고, 각 예외 상황을 직접 재현해서 테스트하는 방법을 알려줘.
```

**확인할 것:** 세 언어 번역이 실제로 되는지, 빈 입력·잘못된 API 키·잘못된 모델명일 때 알맞은 메시지가 나오는지.

---

## 3단계: UI 디자인

```
기능은 그대로 두고 app.py의 UI를 PRD.md 9장 와이어프레임을 바탕으로 보기 좋게 다듬어줘.

[페이지 설정]
- st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")를 맨 처음에 호출한다.

[화면 구성]
- 상단: "🌐 다국어 번역기" 제목과 "번역할 글을 입력하고 언어를 선택하세요." 부제
- 입력창: placeholder "번역할 텍스트를 입력하세요...", 높이 200px 정도, 오른쪽 아래에 글자 수 표시
- 버튼: "🇺🇸 영어", "🇯🇵 일본어", "🇻🇳 베트남어" 세 개를 같은 너비로 나란히 배치 (use_container_width=True)
- 마지막으로 누른 언어 버튼이 시각적으로 구분되게 한다. (예: type="primary")
- 결과 영역: "번역 결과 (영어)"처럼 대상 언어가 들어간 소제목 + 카드 형태의 박스(st.container(border=True))에 번역문 표시
- 결과 아래에 번역문을 복사할 수 있도록 st.code(번역문, language=None)도 함께 제공한다. (PRD F-9)
- 결과가 없을 때는 "아직 번역된 내용이 없습니다." 같은 안내를 흐린 글씨로 표시한다.
- 하단에 "Powered by OpenAI {모델명}" 캡션

[스타일]
- st.markdown(..., unsafe_allow_html=True)로 최소한의 CSS만 추가한다. (버튼 모서리 둥글게, 결과 박스 여백·줄 간격 등)
- 라이트 모드와 다크 모드에서 모두 글씨가 잘 보여야 한다. 배경색이나 글자색을 고정값으로 박지 말 것.
- 모바일 화면(좁은 폭)에서도 레이아웃이 깨지지 않게 한다.

[주의]
- 2단계에서 만든 번역 로직, 예외 처리, session_state 동작은 바꾸지 마.
- 바뀐 부분만 요약해서 알려줘.
```

**확인할 것:** 라이트/다크 모드 전환, 브라우저 폭을 좁혔을 때 레이아웃, 결과 복사 버튼 동작.

---

## 4단계: PRD 준수 여부 및 버그 검토

```
지금까지 만든 프로젝트 전체(app.py, requirements.txt, .env.example, .gitignore)를 PRD.md와 비교해서 자세하게 검토해줘. 코드는 바로 고치지 말고 먼저 검토 보고서를 작성해줘.

[1. PRD 요구사항 대조]
- PRD 5장 기능 요구사항 F-1 ~ F-9 각각에 대해 "충족 / 부분 충족 / 미충족"을 표로 정리하고, 근거가 되는 코드 위치(파일명:줄 번호)를 적어줘.
- PRD 7장(.env 설정), 8장(파일 구조), 10장(비기능 요구사항), 11장(예외 처리)도 같은 방식으로 확인해줘.
- PRD 12장 완료 기준 체크리스트를 하나씩 검증하고 결과를 표시해줘.

[2. 버그 검토]
다음 항목을 중심으로 실제로 문제가 생길 수 있는 부분을 찾아줘.
- Streamlit 재실행(rerun) 구조 때문에 생기는 문제: 버튼 클릭 후 결과가 사라지거나, 이전 결과가 잘못 남거나, 같은 요청이 두 번 호출되는 경우
- session_state 키 이름 충돌, 초기화 누락
- 입력이 빈 문자열/공백/아주 긴 텍스트/특수문자·이모지·여러 줄일 때 동작
- API 응답이 비어 있거나(None) 예상과 다른 형태일 때
- 예외 처리 누락, 너무 넓은 except로 오류가 숨겨지는 부분
- .env가 없을 때, OPENAI_MODEL만 없을 때의 동작
- 번역 결과에 따옴표·설명이 섞여 나오는지 (프롬프트 품질)

[3. 보안 검토]
- API 키가 코드, 화면, 오류 메시지, 로그 어디에도 노출되지 않는지
- .env가 .gitignore에 들어 있는지
- unsafe_allow_html=True 사용 부분에 사용자 입력이나 번역 결과가 그대로 들어가 HTML/스크립트가 실행될 위험이 없는지

[4. 코드 품질]
- 중복 코드, 불필요한 코드, 하드코딩된 값
- 언어를 추가할 때 LANGUAGES 딕셔너리만 고치면 되는 구조인지
- requirements.txt에 필요한 패키지가 빠지거나 불필요한 것이 들어 있지 않은지

[보고서 형식]
- 발견한 문제마다: 심각도(높음/중간/낮음), 위치(파일명:줄 번호), 문제 설명, 재현 방법, 수정 방안
- 심각도 높은 순으로 정렬
- 마지막에 전체 요약과 "바로 고쳐야 할 것 / 고치면 좋은 것"을 나눠서 정리

보고서를 확인한 뒤 내가 승인하면 그때 수정해줘.
```

**확인할 것:** 보고서에서 심각도 "높음" 항목부터 수정을 승인하고, 수정 후 PRD 12장 완료 기준을 다시 점검.
