import streamlit as st
import pdfplumber
from google import genai
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (최신 방식 강제 고정)
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    # 경로 문제를 피하기 위해 클라이언트를 가장 표준적인 방식으로 생성
    client = genai.Client(api_key=api_key)
else:
    st.error("⚠️ Secrets 설정에서 API 키를 확인해주세요!")
    st.stop()

# 3. 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF를 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출
                text_content = ""
                with pdfplumber.open(file) as pdf:
                    # 속도를 위해 핵심 내용이 담긴 앞 3페이지만 추출
                    for page in pdf.pages[:3]:
                        content = page.extract_text()
                        if content: text_content += content
                
                # [핵심 수정] 모델 이름에서 'models/'를 빼고 순수하게 이름만 입력
                # 구글 최신 라이브러리(v1.73.1)의 표준 방식입니다.
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=f"당신은 전문 보험설계사입니다. 다음 제안서의 핵심 보장내용을 요약해 주세요: {text_content[:5000]}"
                )
                
                all_results.append({"파일명": file.name, "분석 결과": response.text})
            except Exception as e:
                st.error(f"❌ {file.name} 분석 실패: {str(e)}")

    # 4. 결과 출력
    if all_results:
        st.success("✅ 분석 완료!")
        for res in all_results:
            with st.expander(f"📌 {res['파일명']} 분석 결과"):
                st.write(res['분석 결과'])
