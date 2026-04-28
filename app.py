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

# JSON만 안전하게 추출하는 함수
def extract_json(text):
    try:
        return json.loads(text)
    except:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("AI 응답에서 JSON을 찾을 수 없습니다.")

# 3. 파일 업로드
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
                # PDF 텍스트 추출
                text_content = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:5]:
                        content = page.extract_text()
                        if content:
                            text_content += content + "\n"

                prompt = f"""
너는 보험 제안서를 비교 분석하는 보험 설계 전문가야.

아래 PDF 텍스트를 분석해서 반드시 JSON 형식으로만 답변해.
설명 문장, 마크다운, 코드블록은 절대 넣지 마.

분석 기준:
- 상해
- 암
- 뇌
- 심장
- 수술
- 입원비
- 보험료
- 납입기간
- 보장기간
- 특이사항

없는 정보는 "확인 필요"라고 적어.

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
                result["파일명"] = file.name
                all_results.append(result)

            except Exception as e:
                st.error(f"❌ {file.name} 분석 중 오류 발생: {str(e)}")

    # 4. 결과 출력
    if all_results:
        st.success("✅ 분석 완료!")

        df = pd.DataFrame(all_results)

        # 파일명을 맨 앞으로 이동
        columns = ["파일명"] + [col for col in df.columns if col != "파일명"]
        df = df[columns]

        st.subheader("📊 제안서 비교표")
        st.dataframe(df, use_container_width=True)

        # CSV 다운로드
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 비교표 CSV 다운로드",
            data=csv,
            file_name="보험_제안서_비교표.csv",
            mime="text/csv"
        )

        # 상세 보기
        st.subheader("📌 파일별 상세 분석")
        for res in all_results:
            with st.expander(f"📄 {res['파일명']} 상세 보기"):
                for key, value in res.items():
                    if key != "파일명":
                        st.write(f"**{key}**: {value}")
