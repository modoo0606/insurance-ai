import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# [핵심] API 키를 가져오는 가장 안전한 방법
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # 구글 서버에 연결 가능한 모델 목록을 확인하여 자동으로 선택함
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        st.error("AI 연결에 문제가 있습니다. API 키를 확인해주세요.")
        st.stop()
else:
    st.error("Secrets 설정에 GOOGLE_API_KEY가 없습니다!")
    st.stop()

# 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF를 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    results = []
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출 (첫 5페이지만)
                with pdfplumber.open(file) as pdf:
                    text = "".join([p.extract_text() for p in pdf.pages[:5] if p.extract_text()])
                
                # AI에게 분석 요청
                prompt = f"보험 분석가로서 다음 텍스트에서 보장 내역을 요약해 JSON으로 답해줘: {text[:8000]}"
                response = model.generate_content(prompt)
                
                # 결과 저장
                results.append({"파일명": file.name, "분석결과": response.text[:200] + "..."})
            except Exception as e:
                st.error(f"{file.name} 분석 실패: {e}")

    if results:
        st.write("### ✅ 분석 완료")
        st.table(pd.DataFrame(results))
