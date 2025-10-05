import io
import os
import zipfile
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import streamlit as st
from pdfminer.high_level import extract_text


# -----------------------
# Helper functions
# -----------------------

def extract_text_pdfminer(pdf_bytes: bytes, page_numbers: List[int] = None) -> str:
    """
    Extract text using pdfminer.six. This works well for digital (embedded-text) PDFs.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp.flush()
            txt = extract_text(tmp.name, page_numbers=page_numbers)
        return txt or ""
    except Exception:
        return ""


def process_single_file(file_obj) -> Tuple[str, str, bytes]:
    """
    Process a single uploaded PDF file and return (filename, method, text_bytes).
    """
    filename = file_obj.name
    pdf_bytes = file_obj.read()
    txt = extract_text_pdfminer(pdf_bytes)
    method = "pdfminer" if txt.strip() else "failed"
    text_bytes = txt.encode("utf-8", errors="ignore")
    return filename, method, text_bytes


def make_zip_in_memory(results: List[Tuple[str, bytes]]) -> bytes:
    """
    Given list of (filename, bytes) create an in-memory zip and return bytes.
    Filenames are the base original name replaced with .txt
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for orig_name, data in results:
            base = os.path.splitext(orig_name)[0]
            txt_name = base + ".txt"
            z.writestr(txt_name, data)
    buf.seek(0)
    return buf.read()


# -----------------------
# Streamlit UI
# -----------------------

st.set_page_config(page_title="PDF → Text Converter", layout="wide", page_icon="📄➡️📝")
st.title("📄 → 📝 PDF to Text — Precise, Powerful, Accurate")

st.markdown(
    """
A lightweight Streamlit app to convert PDFs to plain text.  
- Uses **pdfminer.six** for accurate text extraction.  
- Supports bulk processing + parallel workers + ZIP download.  
- Skips OCR and images entirely — for **digital PDFs only**.
"""
)

with st.sidebar:
    st.header("Options")
    workers = st.number_input(
        "Parallel workers (bulk)", min_value=1, max_value=16, value=4,
        help="Number of threads for bulk processing."
    )
    out_single = st.selectbox(
        "When a single file is uploaded — show",
        ["Preview & Download .txt", "Direct .txt Download"],
        index=0
    )

uploaded = st.file_uploader("Upload one or multiple PDF files", type=["pdf"], accept_multiple_files=True)
if not uploaded:
    st.info("Upload at least one PDF file to begin.")
    st.stop()

# Processing area
st.subheader("Processing")

progress_bar = st.progress(0)
status_area = st.empty()
log_area = st.empty()

results = []  # (filename, text_bytes, method)
errors = []

total_files = len(uploaded)
status_area.info(f"Queued {total_files} file(s) for processing — starting...")

# Parallel processing
with ThreadPoolExecutor(max_workers=int(workers)) as executor:
    future_to_name = {}
    for f in uploaded:
        future = executor.submit(process_single_file, f)
        future_to_name[future] = f.name

    done_count = 0
    for future in as_completed(future_to_name):
        name = future_to_name[future]
        try:
            filename, method, text_bytes = future.result()
            results.append((filename, text_bytes, method))
            log_area.text(f"✔ {filename} → {method} ({len(text_bytes)} bytes)")
        except Exception as e:
            errors.append((name, str(e)))
            log_area.text(f"✖ {name} failed: {e}")
        done_count += 1
        progress_bar.progress(done_count / total_files)

# Show summary
st.success(f"Processed {len(results)} / {total_files} files.")
if errors:
    st.error(f"{len(errors)} file(s) failed.")
    for n, reason in errors:
        st.write(f"- {n}: {reason}")

# Single file OR bulk
if len(results) == 1:
    name, data, method = results[0]
    st.markdown(f"**File:** `{name}` — **Method:** {method}")
    text = data.decode("utf-8", errors="replace")
    if out_single == "Preview & Download .txt":
        st.text_area("Extracted text (preview)", value=text, height=400)
        st.download_button(
            "Download extracted .txt",
            data,
            file_name=os.path.splitext(name)[0] + ".txt",
            mime="text/plain"
        )
    else:
        st.download_button(
            "Download extracted .txt",
            data,
            file_name=os.path.splitext(name)[0] + ".txt",
            mime="text/plain"
        )
else:
    import pandas as pd
    df = pd.DataFrame([{"filename": fn, "method": m, "size_bytes": len(b)} for fn, b, m in results])
    st.table(df)

    zipped = make_zip_in_memory([(fn, b) for fn, b, m in results])
    st.download_button("Download all results as ZIP", zipped, file_name="pdf_texts.zip", mime="application/zip")

    st.markdown("**Individual downloads**")
    for fn, b, m in results:
        st.download_button(
            f"Download {os.path.splitext(fn)[0]}.txt",
            b,
            file_name=os.path.splitext(fn)[0] + ".txt",
            key=f"dl_{fn}"
        )

st.markdown("---")
st.caption("Built with pdfminer.six for clean digital PDF text extraction. OCR skipped.")
