import streamlit as st
import pdfplumber
from google import genai
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (최신 방식)
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    # 최신 google-genai 클라이언트 생성
    client = genai.Client(api_key=api_key)
else:
    st.error("⚠️ Secrets 설정에서 API 키를 찾을 수 없습니다!")
    st.stop()

# 3. 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF들을 업로드하세요", type="pdf", accept_multiple_files=True)

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
                
                # [핵심 수정] 404 에러를 방지하는 최신 모델 호출 방식
                # 'models/'를 붙이지 않고 이름만 정확히 입력합니다.
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"보험 설계사로서 다음 제안서를 요약해줘: {text_content[:5000]}"
                )
                
                all_results.append({"파일명": file.name, "분석 결과": response.text})
            except Exception as e:
                # 에러 발생 시 상세 메시지 출력 (분석 실패 문구 수정)
                st.error(f"❌ {file.name} 분석 중 오류 발생: {str(e)}")

    # 4. 결과 출력
    if all_results:
        st.success("✅ 분석 완료!")
        for res in all_results:
            with st.expander(f"📌 {res['파일명']} 결과 보기"):
                st.write(res['분석 결과'])
