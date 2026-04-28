import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 2. AI 설정 (Secrets 확인)
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("⚠️ API 키가 설정되지 않았습니다! Streamlit 'Secrets' 설정창을 확인해 주세요.")
    st.stop()

# 구글 AI 연결 (가장 표준적인 방식으로 설정)
genai.configure(api_key=api_key)

# 3. 사이드바 설정
standard_items = [
    "월 보험료", "일반암 진단비", "유사암 진단비", "뇌혈관질환 진단비", 
    "허혈성심장질환 진단비", "질병/상해 사망 보험금", "수술비 보장", 
    "입원비/치료비", "질병/상해 후유장해"
]

with st.sidebar:
    st.header("⚙️ 분석 관리")
    selected_items = st.multiselect("비교 항목 선택", standard_items, default=standard_items)

# 4. 파일 업로드 및 분석
uploaded_files = st.file_uploader("제안서 PDF들을 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            try:
                # PDF 텍스트 추출 (앞부분 위주로 추출하여 오류 방지)
                text_content = ""
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages[:7]: # 7페이지까지 읽기
                        content = page.extract_text()
                        if content: text_content += content
                
                if not text_content:
                    st.warning(f"⚠️ {file.name}에서 내용을 읽을 수 없습니다.")
                    continue

                # 모델 호출 (가장 범용적인 이름인 gemini-pro로 시도)
                # 만약 flash 모델 에러가 계속나면 이 이름이 가장 안전합니다.
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                당신은 보험 전문 분석가입니다. 제안서 내용을 바탕으로 {', '.join(selected_items)} 정보를 찾아주세요.
                응답은 반드시 아래 JSON 형식으로만 작성하세요. 다른 말은 하지 마세요.
                {{
                    "보험사": "{file.name.split('.')[0]}",
                    "결과": {{ "항목": "금액/내용" }},
                    "요약": "특이사항 1문장 요약"
                }}
                텍스트: {text_content[:10000]}
                """
                
                response = model.generate_content(prompt)
                
                # 결과 텍스트 정제 (AI가 앞뒤에 붙이는 마크다운 제거)
                res_raw = response.text.strip()
                if "```json" in res_raw:
                    res_raw = res_raw.split("```json")[1].split("```")[0]
                elif "```" in res_raw:
                    res_raw = res_raw.split("```")[1].split("```")[0]
                
                data = json.loads(res_raw)
                
                row = {"보험사": data["보험사"]}
                row.update(data["결과"])
                row["특이사항"] = data["요약"]
                all_results.append(row)
                
            except Exception as e:
                # 에러가 나면 화면에 더 친절하게 표시
                st.error(f"❌ {file.name} 분석 실패: {str(e)}")

    # 5. 결과 출력
    if all_results:
        st.subheader("📊 주요 보장 비교표")
        df = pd.DataFrame(all_results)
        # 특이사항 열만 제외하고 표 만들기
        table_cols = [c for c in df.columns if c != "특이사항"]
        st.table(df[table_cols])

        st.subheader("💡 AI 상세 요약")
        for res in all_results:
            with st.expander(f"📌 {res['보험사']} 분석 결과"):
                st.info(res['특이사항'])
