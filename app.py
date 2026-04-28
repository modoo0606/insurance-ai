import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (Secrets에서 키 가져오기)
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    # [핵심 수정] 최신 v1beta 버전이 아닌 표준 방식으로 연결 시도
    genai.configure(api_key=api_key)
    # 모델 이름을 명확하게 지정하여 404 에러 방지
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("⚠️ Secrets에 GOOGLE_API_KEY가 없습니다!")
    st.stop()

# 3. 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF를 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출
                text = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:3]: # 3페이지만 분석
                        content = page.extract_text()
                        if content: text += content
                
                # AI 분석 실행
                # 구형 v1beta 경로 문제를 피하기 위해 가장 표준적인 호출 방식 사용
                response = model.generate_content(
                    f"보험 설계사로서 다음 제안서 요약해줘: {text[:5000]}"
                )
                
                all_results.append({"파일명": file.name, "분석 결과": response.text})
            except Exception as e:
                # 에러가 나면 어떤 에러인지 화면에 자세히 표시
                st.error(f"❌ {file.name} 오류: {str(e)}")

    # 4. 결과 출력
    if all_results:
        st.success("✅ 분석이 완료되었습니다!")
        for res in all_results:
            with st.expander(f"📌 {res['파일명']} 상세 보기"):
                st.write(res['분석 결과'])
