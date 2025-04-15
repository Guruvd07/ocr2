import os
import time
import PyPDF2
import streamlit as st
from fpdf import FPDF
from io import BytesIO
import psutil
import tracemalloc
import requests
import tempfile
import shutil
import zipfile

# Initialize memory tracking
tracemalloc.start()

def setup_unicode_font():
    """Download and setup DejaVu Sans font with all variants (regular, bold, italic, bold-italic)"""
    font_url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-sans-ttf-2.37.zip"
    font_dir = os.path.join(tempfile.gettempdir(), "dejavu_fonts")
    
    try:
        os.makedirs(font_dir, exist_ok=True)
        
        # Download the font package
        zip_path = os.path.join(font_dir, "dejavu.zip")
        response = requests.get(font_url, stream=True)
        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        
        # Extract all font variants
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(font_dir)
        
        # Find all font files
        font_files = {
            'regular': None,
            'bold': None,
            'italic': None,
            'bold_italic': None
        }
        
        for file in os.listdir(font_dir):
            if file.endswith('.ttf'):
                if 'DejaVuSans.ttf' in file:
                    font_files['regular'] = os.path.join(font_dir, file)
                elif 'DejaVuSans-Bold.ttf' in file:
                    font_files['bold'] = os.path.join(font_dir, file)
                elif 'DejaVuSans-Oblique.ttf' in file:
                    font_files['italic'] = os.path.join(font_dir, file)
                elif 'DejaVuSans-BoldOblique.ttf' in file:
                    font_files['bold_italic'] = os.path.join(font_dir, file)
        
        os.remove(zip_path)
        return font_files
    
    except Exception as e:
        st.warning(f"Could not setup Unicode fonts: {e}")
        return None

# Get all font variants
FONT_VARIANTS = setup_unicode_font()

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)  # Return in MB

def extract_text_with_pypdf2(pdf_file):
    start_time = time.time()
    start_mem = get_memory_usage()
    snapshots = []
    
    text = ""
    try:
        # Take memory snapshot before processing
        snapshot1 = tracemalloc.take_snapshot()
        
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:  # Only add if text was extracted
                text += page_text + "\n\n"
        
        # Take memory snapshot after processing
        snapshot2 = tracemalloc.take_snapshot()
        
        execution_time = time.time() - start_time
        end_mem = get_memory_usage()
        memory_used = end_mem - start_mem
        
        # Calculate memory allocation differences
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        memory_stats = "\n".join([str(stat) for stat in top_stats[:5]])
        
        return text, execution_time, memory_used, memory_stats, True
    except Exception as e:
        return str(e), time.time() - start_time, 0, "", False

def generate_pypdf2_report(extraction_data, filename):
    pdf = FPDF()
    pdf.add_page()
    
    # Add Unicode fonts if available
    if FONT_VARIANTS and all(FONT_VARIANTS.values()):
        try:
            pdf.add_font('DejaVu', '', FONT_VARIANTS['regular'], uni=True)
            pdf.add_font('DejaVu', 'B', FONT_VARIANTS['bold'], uni=True)
            pdf.add_font('DejaVu', 'I', FONT_VARIANTS['italic'], uni=True)
            pdf.add_font('DejaVu', 'BI', FONT_VARIANTS['bold_italic'], uni=True)
            default_font = 'DejaVu'
        except:
            st.warning("Failed to load some font variants, using Arial")
            default_font = 'Arial'
    else:
        st.warning("Using fallback font (Arial) - some characters may not display correctly")
        default_font = 'Arial'
    
    pdf.set_font(default_font, size=12)
    pdf.set_margins(15, 15, 15)
    
    # Title
    pdf.set_font(default_font, 'B', 16)
    pdf.cell(0, 10, "PyPDF2 Text Extraction Report", 0, 1, 'C')
    pdf.ln(10)
    
    # File info
    pdf.set_font(default_font, 'B', 12)
    pdf.cell(0, 10, f"File: {filename}", 0, 1)
    pdf.ln(5)
    
    # Performance metrics
    pdf.set_font(default_font, 'B', 12)
    pdf.cell(0, 10, "Performance Metrics:", 0, 1)
    pdf.set_font(default_font, size=10)
    
    pdf.cell(0, 7, f"Execution Time: {extraction_data['time']:.4f} seconds", 0, 1)
    pdf.cell(0, 7, f"Memory Used: {extraction_data['memory']:.2f} MB", 0, 1)
    pdf.ln(5)
    
    # Memory allocation details
    if extraction_data['memory_stats']:
        pdf.set_font(default_font, 'B', 12)
        pdf.cell(0, 10, "Top Memory Allocations:", 0, 1)
        pdf.set_font(default_font, size=8)
        pdf.multi_cell(0, 5, extraction_data['memory_stats'])
        pdf.ln(10)
    
    # Extracted text
    if extraction_data['success'] and extraction_data['text']:
        pdf.set_font(default_font, 'B', 12)
        pdf.cell(0, 10, "Extracted Text:", 0, 1)
        pdf.set_font(default_font, size=8)
        
        # Clean text
        text = extraction_data['text'].replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('–', '-')  # Replace en-dashes with regular hyphens
        
        paragraphs = text.split('\n\n')
        
        for para in paragraphs[:20]:  # Limit to first 20 paragraphs
            if para.strip():  # Skip empty paragraphs
                try:
                    pdf.multi_cell(0, 5, para)
                except:
                    # Fallback for problematic characters
                    pdf.multi_cell(0, 5, para.encode('ascii', 'replace').decode('ascii'))
                pdf.ln(3)
    
    # Save to bytes buffer
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def main():
    st.set_page_config(page_title="PDF Text Extraction", layout="wide")
    st.title("PyPDF2 Text Extraction")
    st.subheader("Performance Monitoring and Analysis")
    
    if not FONT_VARIANTS or not all(FONT_VARIANTS.values()):
        st.warning("""
        Some Unicode font variants not available. Special characters may not display correctly in reports.
        For full Unicode support, please ensure internet access is available to download fonts.
        """)
    
    # File upload
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"], key="pypdf2_uploader")
    
    if uploaded_file is not None:
        if st.button("Extract Text with PyPDF2", key="pypdf2_extract"):
            with st.spinner("Extracting text and monitoring performance..."):
                text, exec_time, memory_used, memory_stats, success = extract_text_with_pypdf2(uploaded_file)
                
                st.subheader("Extraction Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Execution Time", f"{exec_time:.4f} seconds")
                    st.metric("Memory Used", f"{memory_used:.2f} MB")
                
                with col2:
                    st.metric("Status", "Success" if success else "Failed")
                    if success:
                        st.metric("Text Length", f"{len(text)} characters")
                
                if success:
                    st.subheader("Extracted Text Sample")
                    st.text_area("Text", value=text[:2000] + ("..." if len(text) > 2000 else ""), 
                                height=300, key="pypdf2_text_output")
                
                # Store results for report generation
                st.session_state.pypdf2_results = {
                    'text': text if success else "",
                    'time': exec_time,
                    'memory': memory_used,
                    'memory_stats': memory_stats,
                    'success': success,
                    'filename': uploaded_file.name
                }
                
                # Generate and show PDF report
                if success:
                    with st.spinner("Generating PDF report..."):
                        report = generate_pypdf2_report(
                            st.session_state.pypdf2_results,
                            uploaded_file.name
                        )
                        
                        st.download_button(
                            label="Download PyPDF2 Report",
                            data=report,
                            file_name=f"pypdf2_report_{uploaded_file.name}.pdf",
                            mime="application/pdf",
                            key="pypdf2_download"
                        )

if __name__ == "__main__":
    main()