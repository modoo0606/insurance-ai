import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 1. 페이지 및 AI 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# Secrets에서 API 키 가져오기
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ API 키가 설정되지 않았습니다! Streamlit 'Secrets' 설정에 키를 넣어주세요.")
    st.stop()

# AI 연결 설정
genai.configure(api_key=api_key)

# 2. 분석 항목 설정
standard_items = [
    "월 보험료", "일반암 진단비", "유사암 진단비", "뇌혈관질환 진단비", 
    "허혈성심장질환 진단비", "질병/상해 사망 보험금", "수술비 보장", 
    "입원비/치료비", "질병/상해 후유장해"
]

with st.sidebar:
    st.header("⚙️ 분석 관리")
    selected_items = st.multiselect("비교 항목 선택", standard_items, default=standard_items)

# 3. 파일 업로드 및 분석
uploaded_files = st.file_uploader("제안서 PDF들을 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출
                text = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:5]: # 첫 5페이지만 분석
                        content = page.extract_text()
                        if content: text += content
                
                if not text:
                    st.warning(f"⚠️ {file.name}에서 내용을 읽을 수 없습니다.")
                    continue

                # 모델 이름을 가장 단순한 형태로 변경 (핵심 수정 사항)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                보험 전문 분석가로서 다음 텍스트에서 {', '.join(selected_items)} 정보를 찾아주세요.
                응답은 반드시 아래 JSON 형식으로만 작성하세요:
                {{
                    "보험사": "{file.name.split('.')[0]}",
                    "결과": {{ "항목": "금액/내용" }},
                    "요약": "특이사항 요약"
                }}
                텍스트: {text[:8000]}
                """
                
                response = model.generate_content(prompt)
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(res_text)
                
                row = {"보험사": data["보험사"]}
                row.update(data["결과"])
                row["특이사항"] = data["요약"]
                all_results.append(row)
                
            except Exception as e:
                st.error(f"❌ {file.name} 분석 오류가 발생했습니다. (원인: {e})")

    if all_results:
        st.subheader("📊 주요 보장 비교표")
        df = pd.DataFrame(all_results)
        st.table(df.drop(columns=['특이사항']))

        st.subheader("💡 AI 상세 요약")
        for res in all_results:
            with st.expander(f"📌 {res['보험사']} 분석 결과"):
                st.write(res['특이사항'])
