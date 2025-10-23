import streamlit as st
import whisper
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import textwrap
import tempfile
import google.generativeai as genai

# ==========================
# GEMINI / GOOGLE API SETUP
# ==========================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ==========================
# FUNCTIONS
# ==========================
def chunked_generate(prompt_text, model_name="models/gemini-2.5-flash", chunk_size=1500):
    chunks = textwrap.wrap(prompt_text, chunk_size)
    results = []
    model = genai.GenerativeModel(model_name)
    for c in chunks:
        response = model.generate_content(c)
        results.append(response.text)
    return "\n".join(results)

def generate_summary(transcript):
    try:
        prompt = f"Summarize the following lecture in clear, structured bullet points:\n\n{transcript}"
        return chunked_generate(prompt)
    except Exception as e:
        return f"❌ Error generating summary: {e}"

def generate_questions(transcript):
    try:
        prompt = f"Generate 5 practice questions and 5 quick study tips for revision based on this lecture:\n\n{transcript}"
        return chunked_generate(prompt)
    except Exception as e:
        return f"❌ Error generating questions: {e}"

# ==========================
# PAGE CONFIG
# ==========================
st.set_page_config(
    page_title="AI Lecture Notes Generator",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================
# THEME TOGGLE
# ==========================
theme = st.sidebar.radio("Choose Theme:", ["Dark", "Light"])

if theme == "Dark":
    bg_color = "#0f2027"
    text_color = "#f1f1f1"
    textarea_bg = "#111827"
    textarea_text = "#e5e7eb"
    glow_color = "#00ffff"
else:
    bg_color = "#ffffff"
    text_color = "#111827"
    textarea_bg = "#f5f5f5"
    textarea_text = "#111827"
    glow_color = "#0077ff"

# ==========================
# STYLES
# ==========================
st.markdown(f"""
<style>
body, .stApp {{
    background: {bg_color};
    color: {text_color};
    font-family: 'Poppins', sans-serif;
}}
h1 {{
    color: {glow_color};
    text-align: center;
    font-weight: bold;
    text-shadow: 0 0 10px {glow_color}, 0 0 20px {glow_color};
}}
h2, h3 {{
    color: {glow_color};
    font-weight: bold;
}}
.stTextArea>div>textarea {{
    background-color: {textarea_bg};
    color: {textarea_text};
    font-family: 'Courier', monospace;
    border-radius: 12px;
    padding: 12px;
}}
.stButton>button {{
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 12px;
    padding: 10px 22px;
    font-weight: bold;
    transition: 0.3s;
}}
.stButton>button:hover {{
    transform: scale(1.05);
}}
</style>
""", unsafe_allow_html=True)

# ==========================
# TITLE
# ==========================
st.markdown("<h1>📝 AI Lecture Notes Generator</h1>", unsafe_allow_html=True)
st.markdown("<h3>🎓 'Listen. Learn. Summarize. Revise.'</h3>", unsafe_allow_html=True)
st.write("Upload your lecture audio, get your transcript, AI summary, study tips, and PDF instantly!")

# ==========================
# UPLOAD AUDIO
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

    if transcript.strip():
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

        title_style = ParagraphStyle(
            "TitleStyle", parent=styles["Heading1"],
            fontName="Helvetica-Bold", fontSize=22, alignment=TA_CENTER,
            textColor=colors.HexColor(glow_color.replace('#','0x')), leading=28
        )
        subtitle_style = ParagraphStyle(
            "SubtitleStyle", parent=styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=16,
            textColor=colors.HexColor("#0072ff"), backColor=colors.HexColor("#e0f7fa"), leading=20
        )
        body_style = ParagraphStyle(
            "BodyStyle", parent=styles["Normal"],
            fontName="Courier", fontSize=11, leading=14, textColor=colors.HexColor("#0f172a")
        )
        highlight_style = ParagraphStyle(
            "HighlightStyle", parent=styles["Normal"],
            fontName="Courier-Bold", fontSize=11, leading=14,
            textColor=colors.HexColor("#0f172a"), backColor=colors.HexColor("#fffacd")
        )

        story = []
        story.append(Spacer(1, 20))
        story.append(Paragraph("📝 AI Lecture Notes Generator", title_style))
        story.append(Spacer(1, 20))

        # Transcript
        story.append(Paragraph("📝 Transcript:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(transcript, 90):
            story.append(Paragraph(line, highlight_style))
        story.append(Spacer(1, 20))

        # Summary
        story.append(Paragraph("📚 AI Summary:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(summary_text, 90):
            story.append(Paragraph(line, highlight_style))
        story.append(Spacer(1, 20))

        # Questions & Tips
        story.append(Paragraph("🎯 AI-Generated Practice Questions & Study Tips:", subtitle_style))
        story.append(Spacer(1, 10))
        questions_list = [Paragraph(q, highlight_style) for q in questions_text.split('\n') if q.strip()]
        story.append(ListFlowable([ListItem(q) for q in questions_list]))

        doc.build(story)
        pdf_buffer.seek(0)

        # Download PDF
        if st.download_button("📥 Download PDF", data=pdf_buffer,
                              file_name="AILectureNotes.pdf", mime="application/pdf"):
            st.balloons()
            st.success("🎉 Notes successfully downloaded with AI summary, questions & tips!")
