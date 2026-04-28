import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ API 키가 설정되지 않았습니다!")
    st.stop()

genai.configure(api_key=api_key)

# 3. 사이드바
standard_items = ["월 보험료", "일반암 진단비", "유사암 진단비", "뇌혈관질환 진단비", "허혈성심장질환 진단비"]
selected_items = st.sidebar.multiselect("비교 항목", standard_items, default=standard_items)

# 4. 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF 업로드", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                text = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:5]:
                        content = page.extract_text()
                        if content: text += content
                
                # 모델 이름을 'gemini-1.5-flash'로 시도하되, 안되면 'gemini-pro'로 자동 전환
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                except:
                    model = genai.GenerativeModel('gemini-pro')
                
                prompt = f"보험 분석가로서 {file.name}에서 {selected_items}를 추출해 JSON으로 응답해줘. 텍스트: {text[:5000]}"
                
                response = model.generate_content(prompt)
                # 응답에서 JSON만 추출하는 안전한 로직
                res_text = response.text.strip()
                if "{" in res_text:
                    res_text = res_text[res_text.find("{"):res_text.rfind("}")+1]
                
                data = json.loads(res_text)
                all_results.append(data)
                
            except Exception as e:
                st.error(f"❌ {file.name} 에러: {str(e)}")

    if all_results:
        st.table(pd.DataFrame(all_results))
