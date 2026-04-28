import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 1. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (Secrets에서 키 가져오기)
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ API 키가 설정되지 않았습니다! Streamlit Secrets 설정을 확인해주세요.")
    st.stop()

# [중요] 최신 버전의 구글 AI 연결 설정
genai.configure(api_key=api_key)

# 3. 사이드바 - 비교 항목 선택
standard_items = ["월 보험료", "일반암 진단비", "유사암 진단비", "뇌혈관질환 진단비", "허혈성심장질환 진단비", "수술비 보장"]
selected_items = st.sidebar.multiselect("비교 항목", standard_items, default=standard_items)

# 4. 파일 업로드 및 분석
uploaded_files = st.file_uploader("제안서 PDF를 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF에서 텍스트 추출 (앞 5페이지만)
                text_content = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:5]:
                        content = page.extract_text()
                        if content: text_content += content
                
                if not text_content:
                    st.warning(f"⚠️ {file.name}의 내용을 읽을 수 없습니다.")
                    continue

                # [해결 포인트] 모델 이름을 'gemini-1.5-flash'로 시도하되, 시스템 경로를 명확히 지정
                model = genai.GenerativeModel(model_name='gemini-1.5-flash')
                
                prompt = f"""
                보험 분석 전문가로서 다음 텍스트에서 {selected_items} 정보를 추출해 JSON 형식으로 답변하세요.
                결과에 다른 설명은 생략하고 반드시 JSON만 출력하세요.
                {{
                    "보험사": "{file.name.split('.')[0]}",
                    "결과": {{ "항목": "금액/내용" }}
                }}
                텍스트: {text_content[:10000]}
                """
                
                # AI 실행
                response = model.generate_content(prompt)
                
                # 응답에서 JSON 데이터만 깨끗하게 추출
                res_text = response.text.strip()
                if "{" in res_text:
                    res_text = res_text[res_text.find("{"):res_text.rfind("}")+1]
                
                data = json.loads(res_text)
                
                # 데이터 정리
                row = {"보험사": data["보험사"]}
                row.update(data["결과"])
                all_results.append(row)
                
            except Exception as e:
                # 에러 발생 시 상세 원인 파악을 위해 에러 메시지 출력
                st.error(f"❌ {file.name} 분석 실패: {str(e)}")

    # 결과 테이블 출력
    if all_results:
        st.subheader("📊 주요 보장 비교표")
        df = pd.DataFrame(all_results)
        st.table(df)
