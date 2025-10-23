import streamlit as st
import whisper
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import textwrap
import tempfile
import os
import google.generativeai as genai

# ==========================
# GEMINI / GOOGLE API SETUP
# ==========================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ==========================
# FUNCTIONS
# ==========================
def generate_summary(transcript):
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            f"Summarize the following lecture in clear, structured bullet points:\n\n{transcript}"
        )
        return response.text
    except Exception as e:
        return f"❌ Error generating summary: {e}"

def generate_questions(transcript):
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(
            f"Generate 5 practice questions and 5 quick study tips for revision based on this lecture:\n\n{transcript}"
        )
        return response.text
    except Exception as e:
        return f"❌ Error generating questions: {e}"

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(page_title="🎓 Smart Lecture Notes AI Assistant", page_icon="🧠", layout="wide")

st.markdown("""
<style>
body, .stApp {
    background: linear-gradient(145deg, #0f2027, #203a43, #2c5364);
    color: #f1f1f1;
    font-family: 'Poppins', sans-serif;
}
h1, h2, h3 {
    color: #00e0ff;
    text-shadow: 0 0 10px #00e0ff;
    font-family: 'Orbitron', sans-serif;
}
.stTextArea>div>textarea {
    background-color: #111827;
    color: #e5e7eb;
    font-family: 'Fira Code', monospace;
    border-radius: 12px;
    padding: 12px;
}
.stButton>button {
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 12px;
    padding: 10px 22px;
    font-weight: bold;
}
.stButton>button:hover {
    transform: scale(1.05);
}
</style>
""", unsafe_allow_html=True)

# ==========================
# TITLE
# ==========================
st.markdown("<h1>🧠 Smart Lecture Voice-to-Notes Assistant</h1>", unsafe_allow_html=True)
st.markdown("<h3>🎓 'Listen. Learn. Summarize. Revise.'</h3>", unsafe_allow_html=True)
st.write("Upload your lecture audio, get your transcript, AI summary, smart study tips, and PDF instantly!")

# ==========================
# UPLOAD SECTION
# ==========================
uploaded_file = st.file_uploader("🎧 Upload Lecture Audio (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"])

if uploaded_file:
    st.audio(uploaded_file, format="audio/wav")

    with st.spinner("🎙️ Transcribing audio..."):
        try:
            whisper_model = whisper.load_model("tiny")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            result = whisper_model.transcribe(tmp_path)
            transcript = result["text"]
            st.text_area("📝 Transcript", transcript, height=200)

        except Exception as e:
            st.error(f"❌ Error during transcription: {e}")
            st.stop()

    if 'transcript' in locals() and transcript.strip():
        with st.spinner("✨ Generating AI Summary..."):
            summary_text = generate_summary(transcript)
            st.text_area("📚 AI Summary", summary_text, height=200)

        with st.spinner("🧠 Creating Study Questions & Tips..."):
            questions_text = generate_questions(transcript)
            st.text_area("🎯 AI-Generated Questions & Study Tips", questions_text, height=220)

        # ==========================
        # BUILD PDF
        # ==========================
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#00c6ff"),
            leading=28
        )
        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Heading2"],
            fontName="Helvetica-BoldOblique",
            fontSize=16,
            textColor=colors.HexColor("#0072ff"),
            backColor=colors.HexColor("#e0f7fa"),
            leading=20
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0f172a")
        )

        story = []
        story.append(Spacer(1, 20))
        story.append(Paragraph("🧠 Smart Lecture Notes", title_style))
        story.append(Spacer(1, 20))

        # Transcript
        story.append(Paragraph("📝 Transcript:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(transcript, 90):
            story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 20))

        # Summary
        story.append(Paragraph("📚 AI Summary:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(summary_text, 90):
            story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 20))

        # Questions & Tips
        story.append(Paragraph("🎯 AI-Generated Practice Questions & Study Tips:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(questions_text, 90):
            story.append(Paragraph(line, body_style))

        doc.build(story)
        pdf_buffer.seek(0)

        # Download
        if st.download_button("📥 Download PDF", data=pdf_buffer,
                              file_name="SmartLectureNotes.pdf", mime="application/pdf"):
            st.balloons()
            st.success("🎉 Notes successfully downloaded with AI summary, questions & tips!")
