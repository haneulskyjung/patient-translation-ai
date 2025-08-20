import streamlit as st
import openai
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import matplotlib.pyplot as plt
from io import BytesIO
from dotenv import load_dotenv
import time

# --- Load API Key ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- App UI ---
st.set_page_config(page_title="AI Patient-Friendly Note Translator", layout="wide")
st.title("🩺 AI Healthcare Translator")
st.markdown("외국인 환자들과 소통하는 데에 도움을 주는 도구. \n\n 1. 왼쪽 상단 >> 을 클릭하세요. \n 2. 리포트 생성하기를 클릭하세요.")

# --- Author & Data Credit ---
st.markdown("""
<p style='text-align:right; color: gray; font-size:12px;'>
Created by Ha-neul Jung | Data source: WHO, CDC, and publicly available medical datasets
</p>
""", unsafe_allow_html=True)

# --- Sidebar: Sample Notes & Settings ---
st.sidebar.title("📝 환자 메모 입력 & 설정")

sample_notes = {
    "예시 메모 선택": "",
    "고혈압 & 고지혈증": "45세 남성, 고혈압(2기) 및 고지혈증 진단. 아토르바스타틴 20mg 처방 예정.",
    "당뇨병 & 비만": "52세 여성, 제2형 당뇨병 (HbA1C 8.2%), BMI 32. 메트포르민 복용 중, 생활습관 개선 권장.",
    "천식 악화": "30세 환자, 호흡곤란 및 쌕쌕거림으로 내원. 흡입용 스테로이드 처방.",
    "만성신질환 & 고혈압": "60세 여성, CKD 3단계 (eGFR 42). 아몰로디핀 복용 중. 저염식 및 신장내과 추적 관찰 필요.",
    "심부전 & 부정맥": "70세 남성, 심부전 EF 35%. 이뇨제 및 베타차단제 복용 중. 간헐적 심실 조기수축 관찰."
}


# --- Dropdown to select sample ---
note_choice = st.sidebar.selectbox("샘플 메모 선택:", options=list(sample_notes.keys()))

# --- Fill text area automatically ---
if note_choice and note_choice != "예시 메모 선택":
    doctor_note_text = st.sidebar.text_area("또는 의사 메모를 직접 입력하세요:", value=sample_notes[note_choice], height=300)
else:
    doctor_note_text = st.sidebar.text_area("또는 의사 메모를 직접 입력하세요:", height=300)

# --- Risk Keywords & Conditions ---
risk_keywords = {
    "hypertension": {"high": ["stage 2", "severe", "crisis"], "moderate": ["elevated", "stage 1"], "low": ["borderline"]},
    "diabetes": {"high": ["hba1c >9", "insulin"], "moderate": ["hba1c 7-9", "metformin"], "low": ["prediabetes"]},
    "hyperlipidemia": {"high": ["ldl >190"], "moderate": ["ldl 130-189"], "low": ["borderline cholesterol"]},
    "asthma": {"high": ["status asthmaticus", "severe"], "moderate": ["moderate"], "low": ["mild"]},
    "obesity": {"high": ["bmi >35"], "moderate": ["bmi 30-35"], "low": ["bmi 25-30"]},
}

# --- Helper: sanitize text for Streamlit & PDF ---
def sanitize_text(text):
    return ''.join(
        c if ('\u0000' <= c <= '\u007F') or ('\uAC00' <= c <= '\uD7AF') or c in ".,!?()-/:%" else ' '
        for c in text
    )

# --- Button Action ---
if st.button("리포트 생성하기 🩺"):
    if not doctor_note_text.strip():
        st.error("Doctor's note 를 먼저 기입해주세요.")
    else:
        with st.spinner("생성중... ⏳"):
            try:
                # --- AI Prompts ---
                enhanced_prompt = f"""Based on the following Korean doctor's note, provide a patient-friendly English explanation for the foreign patient.
                
                                    Requirements:
                                    - Explain medical terms clearly in simple language.
                                    - Describe why each treatment or medication is suggested.
                                    - Highlight potential risks related to the patient's conditions that are not immediately obvious.
                                    - Include practical, actionable daily tips and lifestyle guidance tailored to this patient's conditions, lab results, and age that the patient might not already know
                                    - Explanations of why certain treatments or lifestyle changes are recommended.
                                    - Must reference public health data from WHO or CDC or open data once.
                                    - Keep the tone clear, concise, and patient-focused, suitable for direct display in a PDF.

                                    Patient note: {doctor_note_text}
                                    """

                # --- Progress simulation ---
                progress = st.progress(0)
                for i in range(20, 101, 20):
                    time.sleep(0.2)
                    progress.progress(i)

                # --- OpenAI API calls ---
                enhanced_ai = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": enhanced_prompt}]
                ).choices[0].message.content.strip()

                # --- Sanitize AI outputs for Streamlit display ---
                enhanced_ai_safe = sanitize_text(enhanced_ai)

                tab1, tab2 = st.tabs(["🇺🇸 English (Patient Version)", "🇰🇷 Korean (Doctor Version)"])

                with tab1:
                    # --- Display Translations & Awareness ---
                    st.subheader("✅ Patient-Friendly Explanation")
                    st.write(enhanced_ai_safe)

                    # --- PDF Export (same as before) ---
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf")
                    pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf")
                    pdf.add_font("DejaVu", "I", "fonts/DejaVuSans-Oblique.ttf")
                    pdf.add_font("DejaVu", "BI", "fonts/DejaVuSans-BoldOblique.ttf")
                    pdf.set_font("DejaVu", size=14)     
                    pdf.set_text_color(0, 51, 102)
                    pdf.cell(0, 12, "Patient Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.ln(8)    

                    pdf.set_font("DejaVu", size=14, style="B")
                    pdf.cell(0, 10, "Patient-Friendly Translation", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf.set_font("DejaVu", size=12)
                    pdf.multi_cell(0, 8, enhanced_ai_safe)
                    pdf.ln(4)

                    pdf.set_font("DejaVu", size=10, style="I")
                    pdf.set_text_color(100, 100, 100)
                    pdf.multi_cell(0, 6, "Disclaimer: This report is for educational purposes only and not a substitute for professional medical advice.")
                    pdf.ln(3)
                    pdf.set_font("DejaVu", size=10, style="I")
                    pdf.set_text_color(120, 120, 120)
                    page_width = pdf.w - 2 * pdf.l_margin  # page width minus left/right margins
                    pdf.multi_cell(page_width, 6, "Created by Ha-neul Jung | Data source: WHO, CDC, publicly available datasets", align="R")
                    
                    pdf_file = "translation_report.pdf"
                    pdf.output(pdf_file)
                    with open(pdf_file, "rb") as f:
                        st.download_button("⬇️ Download Full Report (PDF)", f, file_name="patient_report_eng.pdf")

                    # --- Follow-up Q&A ---
                    st.subheader("💬 Ask a Question About Your Note")
                    user_q = st.text_input("Type your question here:")
                    if st.button("Ask AI"):
                        if user_q.strip():
                            q_response = openai.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a helpful medical explainer for patients."},
                                    {"role": "user", "content": f"Doctor's note: {doctor_note_text}"},
                                    {"role": "user", "content": f"Patient question: {user_q}"}
                                ]
                            )
                            st.info(sanitize_text(q_response.choices[0].message.content.strip()))

                with tab2:
                    # Translate into Korean
                    enhanced_ai_kor_prompt = f"Translate the following doctor's note to Korean:\n\n{enhanced_ai_safe}. aware that the patient is one person not people."
                    enhanced_ai_kor = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": enhanced_ai_kor_prompt}]
                    ).choices[0].message.content.strip()

                    # --- Sanitize AI outputs for Streamlit display ---
                    enhanced_ai_kor_safe = sanitize_text(enhanced_ai_kor)

                    # --- Display Translations & Awareness ---
                    st.subheader("✅ 환자 친화적 설명")
                    st.write(enhanced_ai_kor_safe)

                    # --- PDF Export (same as before) ---
                    pdf_kor = FPDF()
                    pdf_kor.add_page()
                    pdf_kor.add_font("NotoSansKR", "", "fonts/NotoSansKR-Regular.ttf")
                    pdf_kor.add_font("NotoSansKR", "B", "fonts/NotoSansKR-Bold.ttf")
                    pdf_kor.add_font("NotoSansKR", "I", "fonts/NotoSansKR-ExtraLight.ttf")
                    pdf_kor.set_font("NotoSansKR", size=12)
                    pdf_kor.set_text_color(0, 51, 102)
                    pdf_kor.cell(0, 12, "Patient Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf_kor.ln(8)

                    pdf_kor.set_font("NotoSansKR", size=14, style="B")
                    pdf_kor.cell(0, 10, "환자 친화적 설명", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
                    pdf_kor.set_font("NotoSansKR", size=12)
                    pdf_kor.multi_cell(0, 8, enhanced_ai_kor_safe)
                    pdf_kor.ln(4)

                    pdf_kor.set_font("NotoSansKR", size=10, style="I")
                    pdf_kor.set_text_color(100, 100, 100)
                    pdf_kor.multi_cell(0, 6, "면책 조항: 이 보고서는 전문적인 의학적 조언을 대신하는 것이 아니라 교육 목적으로만 작성되었습니다.")
                    pdf_kor.ln(3)
                    pdf_kor.set_font("NotoSansKR", size=10, style="I")
                    pdf_kor.set_text_color(120, 120, 120)
                    page_width = pdf_kor.w - 2 * pdf_kor.l_margin  # page width minus left/right margins
                    pdf_kor.multi_cell(page_width, 6, "정하늘 작성 | 데이터 출처: WHO, CDC, 공개 데이터셋", align="R")

                    pdf_file_kor = "translation_report_kor.pdf"
                    pdf_kor.output(pdf_file_kor)
                    with open(pdf_file_kor, "rb") as f:
                        st.download_button("⬇️ Download Full Report (PDF)", f, file_name="patient_report_kor.pdf")

            except Exception as e:
                st.error(f"Error: {e}")

