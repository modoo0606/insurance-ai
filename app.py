import streamlit as st
import pdfplumber
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="AI 보험 비교 분석기", layout="wide")
st.title("🛡️ 스마트 보험설계사: AI 제안서 자동 분석")

# 표준 비교 항목
standard_items = [
    "월 보험료", "일반암 진단비", "유사암 진단비", 
    "뇌혈관질환 진단비", "허혈성심장질환 진단비", 
    "사망 보험금(질병/상해)", "수술비(종/질병/상해)", 
    "입원비/치료비", "질병/상해 후유장해"
]

# 사이드바
with st.sidebar:
    st.header("⚙️ 분석 관리")
    selected_items = st.multiselect("비교 항목 선택", standard_items, default=standard_items)
    st.info("PDF를 업로드하면 AI가 분석을 시작합니다.")

# 파일 업로드
uploaded_files = st.file_uploader("제안서 PDF들을 업로드하세요", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_results = []
    unique_notes = []

    for file in uploaded_files:
        with st.spinner(f'{file.name} 분석 중...'):
            with pdfplumber.open(file) as pdf:
                text = "".join([page.extract_text() for page in pdf.pages])
            
            # (추후 Gemini API 연동 시 실제 데이터가 추출되는 부분입니다)
            analysis = {
                "보험사": file.name.split('.')[0],
                "월 보험료": "분석 준비 완료",
                "일반암 진단비": "확인 필요",
                "사망 보험금": "확인 필요",
                "수술비": "확인 필요",
                "입원/치료비": "확인 필요",
            }
            all_results.append(analysis)
            unique_notes.append({"보험사": file.name.split('.')[0], "특이사항": "파일 분석이 완료되면 여기에 각 보험사만의 특징이 요약됩니다."})

    st.subheader("📊 주요 보장 비교표")
    df = pd.DataFrame(all_results)
    st.table(df)

    st.subheader("💡 보험사별 특이사항 (AI 요약)")
    for note in unique_notes:
        with st.expander(f"📌 {note['보험사']} 상세 특징"):
            st.write(note['특이사항'])

    st.download_button("결과 리포트 저장 (CSV)", df.to_csv(index=False).encode('utf-8-sig'), "보험분석결과.csv", "text/csv")
else:
    st.write("왼쪽 메뉴나 업로드 창에 PDF를 넣어주세요.")
