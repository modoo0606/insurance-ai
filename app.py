import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# API 키 가져오기
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ [설정 오류] Secrets 창에 GOOGLE_API_KEY를 입력하지 않으셨어요! 위 가이드를 다시 봐주세요.")
    st.stop()

# AI 연결
try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ [연결 오류] API 키는 있는데 연결이 안 돼요: {e}")
    st.stop()

# 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF들을 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출
                with pdfplumber.open(file) as pdf:
                    text = "".join([p.extract_text() for p in pdf.pages[:5] if p.extract_text()])
                
                # AI 분석 요청
                prompt = f"보험 설계사로서 이 제안서의 핵심 보장내용(월보험료, 진단비 등)을 표 형태로 요약해줘: {text[:5000]}"
                response = model.generate_content(prompt)
                
                all_results.append({"파일명": file.name, "분석 결과": response.text})
            except Exception as e:
                st.error(f"❌ {file.name} 분석 실패: {e}")

    if all_results:
        st.write("### ✅ 분석 완료!")
        for res in all_results:
            with st.expander(f"📌 {res['파일명']} 결과 보기"):
                st.write(res['분석 결과'])
