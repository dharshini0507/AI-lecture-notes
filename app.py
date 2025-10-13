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
api_key = "your api key"  # Replace with your valid API key
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# ==========================
# FUNCTION TO GENERATE SUMMARY
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

# ==========================
# PAGE CONFIG & THEME
# ==========================
st.set_page_config(page_title="Lecture Notes Assistant", page_icon="📝", layout="wide")

dark_mode = st.sidebar.checkbox("🌙 Dark Mode", value=True)
bg_color, text_color, accent_color = (
    ("#0d1117", "#c9d1d9", "#58a6ff") if dark_mode else ("#ffffff", "#0d1117", "#4a00e0")
)

st.markdown(f"""
<style>
body, .stApp {{ background-color: {bg_color}; color: {text_color}; }}
h1, h2, h3 {{ color: {accent_color}; text-shadow: 0 0 10px {accent_color}; }}
.stButton>button {{
    background: linear-gradient(90deg, #ff6ec4, #7873f5); 
    color: white; 
    border-radius: 12px; 
    padding: 10px 20px;
}}
.stButton>button:hover {{ transform: scale(1.05); }}
textarea, .stTextArea>div>textarea {{ 
    background-color: #161b22; 
    color: #c9d1d9; 
    border-radius: 8px; 
}}
div[data-baseweb="file-uploader"] {{ 
    background-color: #161b22 !important; 
    border: 2px dashed {accent_color} !important; 
    border-radius: 12px; 
}}
</style>
""", unsafe_allow_html=True)

# ==========================
# PAGE TITLE
# ==========================
st.title("📝 AI Lecture Voice-to-Notes Assistant")
st.write("Upload your lecture audio, get transcript, summary, and download PDF immediately.")

# ==========================
# UPLOAD AUDIO
# ==========================
uploaded_file = st.file_uploader("Upload Lecture Audio (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"])
if uploaded_file:
    st.audio(uploaded_file, format="audio/wav")

    # ==========================
    # TRANSCRIBE (With Error Handling)
    # ==========================
    with st.spinner("Transcribing audio... ⏳"):
        try:
            whisper_model = whisper.load_model("tiny")

            # Save the uploaded audio to a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Check if file exists before transcribing
            if not os.path.exists(tmp_path):
                st.error("❌ Audio file was not saved properly.")
            else:
                result = whisper_model.transcribe(tmp_path)
                transcript = result["text"]
                st.text_area("Transcript", transcript, height=200)

        except FileNotFoundError:
            st.error("❌ ffmpeg not found or audio file missing. Add 'ffmpeg' in packages.txt for deployment.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Unexpected error during transcription: {e}")
            st.stop()

    # ==========================
    # SUMMARY
    # ==========================
    if 'transcript' in locals() and transcript.strip():
        with st.spinner("Generating summary... ⏳"):
            summary_text = generate_summary(transcript)
            st.text_area("Summary", summary_text, height=200)

        # ==========================
        # PDF DOWNLOAD WITH STYLING
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
            textColor=colors.HexColor("#ff6ec4"),
            leading=28
        )

        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Heading2"],
            fontName="Helvetica-BoldOblique",
            fontSize=16,
            textColor=colors.HexColor("#4a90e2"),
            backColor=colors.HexColor("#f0f8ff"),
            leading=20
        )

        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#161b22")
        )

        # Build the PDF Story
        story = []

        # Title
        story.append(Spacer(1, 20))
        story.append(Paragraph("📝 Lecture Notes", title_style))
        story.append(Spacer(1, 20))

        # Transcript Section
        story.append(Paragraph("Transcript:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(transcript, 90):
            story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 20))

        # Summary Section
        story.append(Paragraph("Summary:", subtitle_style))
        story.append(Spacer(1, 10))
        for line in textwrap.wrap(summary_text, 90):
            story.append(Paragraph(line, body_style))

        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)

        # Download button
        st.download_button(
            label="📥 Download PDF",
            data=pdf_buffer,
            file_name="LectureNotes.pdf",
            mime="application/pdf"
        )
