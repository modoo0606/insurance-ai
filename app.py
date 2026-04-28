import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (설계사님의 키를 직접 연결)
API_KEY = st.secrets.get("GOOGLE_API_KEY", "AIzaSyBwzl5OsJwxlNhOcgNSW4MruQmLtvaTMK4")
genai.configure(api_key=API_KEY)

# 3. 분석 항목
items = ["월 보험료", "일반암 진단비", "뇌혈관 진단비", "허혈성심장 진단비"]

# 4. 파일 업로드
files = st.file_uploader("제안서 PDF를 업로드하세요", type="pdf", accept_multiple_files=True)

if files:
    results = []
    for file in files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출
                text = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:3]: # 3페이지만 빠르게 분석
                        text += page.extract_text() or ""
                
                # 모델 호출 (가장 안정적인 경로 지정)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"보험 분석가로서 {items} 정보를 찾아 JSON으로 답해줘. 텍스트: {text[:5000]}"
                
                response = model.generate_content(prompt)
                
                # 결과 정리
                results.append({"파일명": file.name, "분석내용": response.text[:100] + "..."})
            except Exception as e:
                st.error(f"❌ {file.name} 오류: {str(e)}")

    if results:
        st.table(pd.DataFrame(results))
