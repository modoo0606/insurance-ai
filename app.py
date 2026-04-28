import streamlit as st
import pdfplumber
import google.generativeai as genai
import pandas as pd
import json

# 1. AI 설정 (Secrets에서 키 가져오기)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("설정에서 API 키를 먼저 입력해주세요!")

# 2. 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 비교 항목 (사망, 수술비, 치료비, 입원비 포함)
standard_items = [
    "월 보험료", "일반암 진단비", "유사암 진단비", "뇌혈관질환 진단비", 
    "허혈성심장질환 진단비", "질병/상해 사망 보험금", "수술비 보장", 
    "입원비/치료비", "질병/상해 후유장해"
]

with st.sidebar:
    st.header("⚙️ 분석 관리")
    selected_items = st.multiselect("비교 항목 선택", standard_items, default=standard_items)

# 3. 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF들을 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    
    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            # PDF 텍스트 추출
            with pdfplumber.open(file) as pdf:
                text = "".join([page.extract_text() for page in pdf.pages if page.extract_text()])
            
            # AI에게 분석 명령
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            당신은 보험 전문 분석가입니다. 아래 텍스트에서 다음 항목들의 보장 금액을 찾아주세요.
            찾을 항목: {', '.join(selected_items)}
            
            추가로 제안서의 독특한 특징을 한 문장으로 요약해줘.
            응답은 반드시 아래 형식을 지켜줘:
            {{
                "보험사": "{file.name.split('.')[0]}",
                "분석결과": {{ "항목명": "금액/내용", ... }},
                "특이사항": "내용"
            }}
            텍스트: {text[:8000]}
            """
            
            try:
                response = model.generate_content(prompt)
                # JSON 형식만 골라내기
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(res_text)
                
                # 표 데이터 정리
                row = {"보험사": data["보험사"]}
                row.update(data["분석결과"])
                row["특이사항"] = data["특이사항"]
                all_results.append(row)
            except:
                st.error(f"{file.name} 분석 중 오류가 발생했습니다.")

    if all_results:
        # 4. 결과 출력
        st.subheader("📊 주요 보장 비교표")
        df = pd.DataFrame(all_results)
        # 특이사항은 표에서 빼고 아래 따로 보여주기
        table_df = df.drop(columns=['특이사항'])
        st.table(table_df)

        st.subheader("💡 보험사별 특이사항 (AI 요약)")
        for _, r in df.iterrows():
            with st.expander(f"📌 {r['보험사']} 상세 특징"):
                st.write(r['특이사항'])
        
        st.download_button("결과 리포트 저장 (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "보험분석.csv")

else:
    st.write("PDF를 업로드하면 AI가 분석을 시작합니다.")
