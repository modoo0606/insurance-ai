import streamlit as st
import pdfplumber
from google import genai
import pandas as pd
import json
import re

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 비교 분석")

# 2. AI 설정
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    st.error("⚠️ Secrets 설정에서 API 키를 찾을 수 없습니다!")
    st.stop()


# 3. AI 응답에서 JSON만 추출하는 함수
def extract_json(text):
    """
    Gemini 응답이 순수 JSON이면 바로 읽고,
    혹시 앞뒤에 설명 문장이 섞이면 JSON 부분만 찾아서 읽는 함수
    """
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("AI 응답에서 JSON 형식을 찾을 수 없습니다.")


# 4. 콤마로 구분된 보장내용을 줄바꿈 불릿으로 바꾸는 함수
def format_benefit_text(value):
    """
    예:
    암진단비 3천만원, 유사암진단비 6백만원
    ->
    - 암진단비 3천만원
    - 유사암진단비 6백만원
    """
    if value is None:
        return "확인 필요"

    text = str(value).strip()

    if not text or text == "nan":
        return "확인 필요"

    # 이미 줄바꿈 불릿 형태면 그대로 사용
    if text.startswith("- "):
        return text

    # 확인 필요는 그대로 사용
    if text == "확인 필요":
        return text

    # 콤마 기준으로 분리
    items = [item.strip() for item in text.split(",") if item.strip()]

    # 콤마가 없으면 그대로 반환
    if len(items) <= 1:
        return text

    return "\n".join([f"- {item}" for item in items])


# 5. 파일 업로드
uploaded_files = st.file_uploader(
    "제안서 PDF들을 업로드하세요",
    type="pdf",
    accept_multiple_files=True
)

if uploaded_files:
    all_results = []

    for file in uploaded_files:
        with st.spinner(f"{file.name} 분석 중..."):
            try:
                # 6. PDF 텍스트 추출
                text_content = ""

                with pdfplumber.open(file) as pdf:
                    # 보험 제안서는 뒤쪽에 담보표가 있는 경우가 많아서 앞 15페이지까지 읽음
                    for page in pdf.pages[:15]:
                        content = page.extract_text()
                        if content:
                            text_content += content + "\n"

                if not text_content.strip():
                    st.error(f"❌ {file.name}에서 텍스트를 추출하지 못했습니다. 스캔 이미지 PDF일 수 있습니다.")
                    continue

                # 7. Gemini에게 항목별 JSON 분석 요청
                prompt = f"""
너는 보험 제안서를 비교 분석하는 보험 설계 전문가야.

아래 PDF 텍스트를 분석해서 반드시 JSON 형식으로만 답변해.
설명 문장, 마크다운, 코드블록은 절대 넣지 마.

분석 기준:
- 보험사
- 상품명
- 월 보험료
- 가입나이
- 납입기간
- 보장기간
- 상해
- 암
- 뇌
- 심장
- 수술
- 입원비
- 특이사항
- 종합평가

중요한 출력 규칙:
- 없는 정보는 "확인 필요"라고 적어.
- 금액은 가능하면 원 단위 또는 만원 단위로 정리해.
- 담보명과 가입금액이 보이면 같이 적어.
- 여러 담보가 있으면 핵심 담보 위주로 요약해.
- 특히 암보장, 뇌보장, 심장보장, 수술비, 입원비는 여러 항목을 콤마로 구분해서 작성해.
- 예: 암진단비(유사암 제외) 3천만원, 유사암진단비 6백만원, 갑상선암진단비 1천만원
- 반드시 아래 JSON 구조 그대로 답변해.

JSON 형식:
{{
  "보험사": "",
  "상품명": "",
  "월보험료": "",
  "가입나이": "",
  "납입기간": "",
  "보장기간": "",
  "상해보장": "",
  "암보장": "",
  "뇌보장": "",
  "심장보장": "",
  "수술비": "",
  "입원비": "",
  "특이사항": "",
  "종합평가": ""
}}

PDF 텍스트:
{text_content[:12000]}
"""

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                result = extract_json(response.text)

                # 파일명을 결과에 추가
                result["파일명"] = file.name
                all_results.append(result)

            except Exception as e:
                st.error(f"❌ {file.name} 분석 중 오류 발생: {str(e)}")

    # 8. 결과 출력
    if all_results:
        st.success("✅ 분석 완료!")

        # 기본 DataFrame 생성
        df = pd.DataFrame(all_results)

        # 컬럼 순서 고정
        column_order = [
            "파일명",
            "보험사",
            "상품명",
            "월보험료",
            "가입나이",
            "납입기간",
            "보장기간",
            "상해보장",
            "암보장",
            "뇌보장",
            "심장보장",
            "수술비",
            "입원비",
            "특이사항",
            "종합평가"
        ]

        # 혹시 빠진 컬럼이 있으면 빈칸으로 채움
        for col in column_order:
            if col not in df.columns:
                df[col] = "확인 필요"

        df = df[column_order]

        # 9. 보장내용 컬럼은 콤마 기준으로 줄바꿈 처리
        benefit_columns = [
            "상해보장",
            "암보장",
            "뇌보장",
            "심장보장",
            "수술비",
            "입원비",
            "특이사항"
        ]

        for col in benefit_columns:
            df[col] = df[col].apply(format_benefit_text)

        # 10. 세로 비교표 만들기
        st.subheader("📊 제안서 세로 비교표")

        vertical_df = df.set_index("파일명").T
        vertical_df.index.name = "비교항목"

        st.dataframe(vertical_df, use_container_width=True)

        # 11. 표보다 보기 좋은 상세 비교 영역
        st.subheader("🔎 보장내용 상세 비교")

        important_sections = [
            "상해보장",
            "암보장",
            "뇌보장",
            "심장보장",
            "수술비",
            "입원비",
            "특이사항",
            "종합평가"
        ]

        for section in important_sections:
            st.markdown(f"### {section}")

            cols = st.columns(len(all_results))

            for idx, res in enumerate(all_results):
                file_name = res.get("파일명", f"제안서 {idx + 1}")
                raw_value = res.get(section, "확인 필요")
                formatted_value = format_benefit_text(raw_value)

                with cols[idx]:
                    st.markdown(f"**{file_name}**")
                    st.markdown(formatted_value)

        # 12. CSV 다운로드
        csv = vertical_df.to_csv().encode("utf-8-sig")

        st.download_button(
            label="📥 세로 비교표 CSV 다운로드",
            data=csv,
            file_name="보험_제안서_세로비교표.csv",
            mime="text/csv"
        )

        # 13. 파일별 상세 분석
        st.subheader("📌 파일별 전체 상세 보기")

        for res in all_results:
            with st.expander(f"📄 {res['파일명']} 상세 보기"):
                for key, value in res.items():
                    if key != "파일명":
                        if key in benefit_columns:
                            st.markdown(f"**{key}**")
                            st.markdown(format_benefit_text(value))
                        else:
                            st.write(f"**{key}**: {value}")
