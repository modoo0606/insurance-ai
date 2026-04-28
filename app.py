import streamlit as st
import pdfplumber
from google import genai
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (최신 엔진 강제 고정)
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    # [수정] 최신 라이브러리 규격에 맞춰 클라이언트 생성
    client = genai.Client(api_key=api_key)
else:
    st.error("⚠️ Secrets 설정에서 API 키를 찾을 수 없습니다!")
    st.stop()

# 3. 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF를 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출 (앞 3페이지만)
                text_content = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:3]:
                        content = page.extract_text()
                        if content: text_content += content
                
                # [핵심 수정] 모델 이름에서 'models/'를 완전히 빼고 'gemini-1.5-flash'만 입력
                # 이렇게 해야 404 NOT FOUND 에러가 나지 않습니다.
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=f"당신은 전문 보험설계사입니다. 다음 내용을 요약해 주세요: {text_content[:5000]}"
                )
                
                all_results.append({"파일명": file.name, "분석 결과": response.text})
            except Exception as e:
                st.error(f"❌ {file.name} 분석 실패: {str(e)}")

    # 4. 결과 출력
    if all_results:
        st.success("✅ 최신 엔진으로 분석이 완료되었습니다!")
        for res in all_results:
            with st.expander(f"📌 {res['파일명']} 분석 결과 보기"):
                st.write(res['분석 결과'])
