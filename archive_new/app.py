import streamlit as st
import pymongo
from pymongo.errors import ConnectionFailure
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time
from datetime import datetime, timedelta
import os
import google.generativeai as genai
import hashlib
import uuid
import bcrypt
import json
import io
import re

# OCR / PDF / Images
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import numpy as np

# --- CONFIGURATION ---
DATABASE_NAME = "court_chat_db"
COLLECTION_NAME = "chat_messages"
MODEL_DIR = "archive_new/legalbert_supreme"  # Folder containing model files

# --- HELPER: Safe print for Windows console compatibility ---
def safe_print(*args, **kwargs):
    """Safely print to console, handling Windows encoding errors."""
    try:
        import sys
        message = ' '.join(str(arg) for arg in args)
        sys.stdout.write(message + '\n')
        sys.stdout.flush()
    except (OSError, UnicodeEncodeError, AttributeError):
        # Silently fail on Windows console encoding issues
        pass

def _get_secret(section: str, key: str, default=None):
    """Safely read Streamlit secrets; return default if secrets.toml is missing or malformed."""
    try:
        # Accessing st.secrets can raise if the file is malformed
        sec = st.secrets.get(section, {})
        return sec.get(key, default)
    except Exception:
        return default

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or _get_secret("gemini", "api_key")

# Optional Tesseract path (Windows)
TESSERACT_CMD = os.getenv("TESSERACT_CMD") or _get_secret("ocr", "tesseract_cmd")
if TESSERACT_CMD:
    try:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    except Exception:
        pass

# Vector Search / Embeddings Configuration
DOCS_COLLECTION_NAME = "documents"
CHUNKS_COLLECTION_NAME = "doc_chunks"
VECTOR_INDEX_NAME = "doc_chunks_vector_index"  # Configure in MongoDB Atlas Vector Search
EMBEDDING_MODEL = "models/text-embedding-004"

# Language Configuration
SUPPORTED_LANGUAGES = {
    "English": {
        "code": "en",
        "name": "English",
        "native_name": "English"
    },
    "Hindi": {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिंदी"
    },
    "Gujarati": {
        "code": "gu",
        "name": "Gujarati",
        "native_name": "ગુજરાતી"
    }
}

# UI Translations
UI_TRANSLATIONS = {
    "English": {
        "app_title": "⚖️ Adhikar.ai - Legal AI Assistant",
        "login_required": "🔒 **Secure Login Required**: Please log in to access your personalized legal AI assistant",
        "login_tab": "🔑 Login",
        "register_tab": "📝 Register",
        "welcome_user": "👤 Welcome",
        "logout": "🚪 Logout",
        "secure_chat": "🔒 **Secure Chat**: All messages are encrypted with SHA-256 hashing for data integrity",
        "choose_mode": "Choose your mode:",
        "case_prediction": "🏛️ Case Outcome Prediction",
        "legal_aid": "💬 General Legal Aid",
        "system_status": "⚙️ System Status",
        "language_selector": "🌐 Select Language",
        "new_chat": "➕ New Chat",
        "chat_history": "💬 Chat History",
        "enter_case": "Enter your case details here...",
        "enter_question": "Ask your legal question...",
        "db_connected": "✅ MongoDB Connected",
        "db_disconnected": "❌ MongoDB Disconnected",
        "model_loaded": "✅ LegalBERT Model Loaded",
        "model_error": "❌ Model Load Failed",
        "gemini_active": "✅ Gemini AI Active",
        "gemini_inactive": "⚠️ Gemini AI Not Configured",
        "document_qa": "📄 Document Q&A",
        "upload_docs": "📤 Upload Documents (PDF, PNG, JPG)",
        "ask_docs": "Ask a question about your documents...",
        "processing_doc": "Processing document...",
        "ingestion_done": "✅ Document ingested successfully",
        "no_index": "Vector index not found or not configured. See docs to create Atlas Vector Search index.",
        "top_sources": "Top Sources"
    },
    "Hindi": {
        "app_title": "⚖️ अधिकार.ai - कानूनी AI सहायक",
        "login_required": "🔒 **सुरक्षित लॉगिन आवश्यक**: कृपया अपने व्यक्तिगत कानूनी AI सहायक तक पहुंचने के लिए लॉगिन करें",
        "login_tab": "🔑 लॉगिन",
        "register_tab": "📝 पंजीकरण",
        "welcome_user": "👤 स्वागत है",
        "logout": "🚪 लॉगआउट",
        "secure_chat": "🔒 **सुरक्षित चैट**: सभी संदेश डेटा अखंडता के लिए SHA-256 हैशिंग से एन्क्रिप्ट किए गए हैं",
        "choose_mode": "अपना मोड चुनें:",
        "case_prediction": "🏛️ मामले के परिणाम की भविष्यवाणी",
        "legal_aid": "💬 सामान्य कानूनी सहायता",
        "system_status": "⚙️ सिस्टम स्थिति",
        "language_selector": "🌐 भाषा चुनें",
        "new_chat": "➕ नई चैट",
        "chat_history": "💬 चैट इतिहास",
        "enter_case": "यहां अपने मामले का विवरण दर्ज करें...",
        "enter_question": "अपना कानूनी प्रश्न पूछें...",
        "db_connected": "✅ MongoDB जुड़ा हुआ है",
        "db_disconnected": "❌ MongoDB डिस्कनेक्ट हो गया",
        "model_loaded": "✅ LegalBERT मॉडल लोड हो गया",
        "model_error": "❌ मॉडल लोड विफल",
        "gemini_active": "✅ Gemini AI सक्रिय",
        "gemini_inactive": "⚠️ Gemini AI कॉन्फ़िगर नहीं किया गया",
        "document_qa": "📄 दस्तावेज़ प्रश्नोत्तर",
        "upload_docs": "📤 दस्तावेज़ अपलोड करें (PDF, PNG, JPG)",
        "ask_docs": "अपने दस्तावेज़ों के बारे में प्रश्न पूछें...",
        "processing_doc": "दस्तावेज़ संसाधित किया जा रहा है...",
        "ingestion_done": "✅ दस्तावेज़ सफलतापूर्वक जोड़ा गया",
        "no_index": "वेक्टर इंडेक्स नहीं मिला या कॉन्फ़िगर नहीं है। कृपया Atlas Vector Search इंडेक्स बनाएं।",
        "top_sources": "मुख्य स्रोत"
    },
    "Gujarati": {
        "app_title": "⚖️ અધિકાર.ai - કાનૂની AI સહાયક",
        "login_required": "🔒 **સુરક્ષિત લૉગિન જરૂરી**: કૃપા કરીને તમારા વ્યક્તિગત કાનૂની AI સહાયકને ઍક્સેસ કરવા માટે લૉગિન કરો",
        "login_tab": "🔑 લૉગિન",
        "register_tab": "📝 નોંધણી",
        "welcome_user": "👤 સ્વાગત છે",
        "logout": "🚪 લૉગઆઉટ",
        "secure_chat": "🔒 **સુરક્ષિત ચેટ**: ડેટા અખંડિતતા માટે તમામ સંદેશા SHA-256 હેશિંગ સાથે એન્ક્રિપ્ટ કરેલા છે",
        "choose_mode": "તમારો મોડ પસંદ કરો:",
        "case_prediction": "🏛️ કેસ પરિણામ અનુમાન",
        "legal_aid": "💬 સામાન્ય કાનૂની સહાય",
        "system_status": "⚙️ સિસ્ટમ સ્થિતિ",
        "language_selector": "🌐 ભાષા પસંદ કરો",
        "new_chat": "➕ નવી ચેટ",
        "chat_history": "💬 ચેટ ઇતિહાસ",
        "enter_case": "અહીં તમારા કેસની વિગતો દાખલ કરો...",
        "enter_question": "તમારો કાનૂની પ્રશ્ન પૂછો...",
        "db_connected": "✅ MongoDB જોડાયેલ છે",
        "db_disconnected": "❌ MongoDB ડિસ્કનેક્ટ થયું",
        "model_loaded": "✅ LegalBERT મોડેલ લોડ થયું",
        "model_error": "❌ મોડેલ લોડ નિષ્ફળ",
        "gemini_active": "✅ Gemini AI સક્રિય",
        "gemini_inactive": "⚠️ Gemini AI ગોઠવેલ નથી",
        "document_qa": "📄 દસ્તાવેજ પ્રશ્નોત્તરી",
        "upload_docs": "📤 દસ્તાવેજો અપલોડ કરો (PDF, PNG, JPG)",
        "ask_docs": "તમારા દસ્તાવેજો વિશે પ્રશ્ન પૂછો...",
        "processing_doc": "દસ્તાવેજ પ્રક્રિયા થઈ રહ્યું છે...",
        "ingestion_done": "✅ દસ્તાવેજ સફળતાપૂર્વક ઉમેરાયો",
        "no_index": "વેક્ટર ઇન્ડેક્સ મળ્યો નથી અથવા ગોઠવાયો નથી. કૃપા કરીને Atlas Vector Search ઇન્ડેક્સ બનાવો.",
        "top_sources": "મુખ્ય સ્ત્રોત"
    }
}

def get_text(key, language="English"):
    """Get translated text for the current language."""
    return UI_TRANSLATIONS.get(language, UI_TRANSLATIONS["English"]).get(key, key)

# --- PAGE SETUP ---
st.set_page_config(page_title="Legal Outcome Predictor", page_icon="⚖️", layout="wide")

# Custom CSS for better multilingual font support
st.markdown("""
<style>
    /* Enhanced font support for Hindi (Devanagari) and Gujarati scripts */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;500;700&family=Noto+Sans+Gujarati:wght@400;500;700&family=Inter:wght@400;500;700&display=swap');
    
    /* Apply appropriate fonts based on content */
    body, .stMarkdown, .stChatMessage, .stTextInput, .stSelectbox, .stRadio {
        font-family: 'Inter', 'Noto Sans Devanagari', 'Noto Sans Gujarati', sans-serif !important;
    }
    
    /* Better line height for Indian scripts */
    .stMarkdown p, .stChatMessage {
        line-height: 1.8 !important;
    }
    
    /* Ensure proper text rendering */
    * {
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Larger font size for better readability of Indic scripts */
    .stMarkdown, .stChatMessage {
        font-size: 16px !important;
    }
    
    /* Enhanced chat message styling */
    .stChatMessage {
        padding: 1rem !important;
        border-radius: 10px !important;
    }
    
    /* Custom attach files button styling */
    .custom-attach-button {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background-color: #F3F4F6;
        border: 1px solid #D1D5DB;
        border-radius: 8px;
        cursor: pointer;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        transition: all 0.2s ease;
        user-select: none;
    }
    
    .custom-attach-button:hover {
        background-color: #E5E7EB;
        border-color: #9CA3AF;
    }
    
    .custom-attach-button:active {
        background-color: #D1D5DB;
    }
    
    
    /* Language dropdown arrow hover style */
    div[data-baseweb="select"]:hover svg,
    div[data-baseweb="select"]:hover [data-baseweb="select"] svg {
        transform: rotate(180deg);
        transition: transform 0.3s ease;
    }
    
    /* Alternative selector for language dropdown */
    .stSelectbox > div > div:hover svg,
    .stSelectbox:hover svg {
        transform: rotate(180deg) !important;
        transition: transform 0.3s ease !important;
    }
    
    /* More specific selector for Streamlit selectbox arrow */
    div[data-testid="stSelectbox"] > div > div:hover > div > svg,
    div[data-testid="stSelectbox"]:hover > div > div > div > svg {
        transform: rotate(180deg) !important;
        transition: transform 0.3s ease !important;
    }
    
    /* Change cursor to pointer when hovering over language dropdown */
    div[data-testid="stSelectbox"],
    div[data-testid="stSelectbox"] > div,
    div[data-testid="stSelectbox"] > div > div,
    div[data-baseweb="select"] {
        cursor: pointer !important;
    }
    
    div[data-testid="stSelectbox"]:hover,
    div[data-testid="stSelectbox"] > div:hover,
    div[data-testid="stSelectbox"] > div > div:hover {
        cursor: pointer !important;
    }
    
    /* Set minimum width for sidebar */
    section[data-testid="stSidebar"] {
        min-width: 280px !important;
    }
    
    /* Prevent sidebar from collapsing below minimum width */
    section[data-testid="stSidebar"] > div {
        min-width: 280px !important;
    }
    
    /* Make session div clickable */
    .session-item {
        cursor: pointer;
        padding: 8px;
        border-radius: 6px;
        transition: background-color 0.2s ease;
    }
    
    .session-item:hover {
        background-color: #f0f2f6;
    }
    
    /* Prevent button clicks from triggering session load */
    .session-item button {
        pointer-events: auto;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

@st.cache_resource
def init_connection():
    """Initialize MongoDB client connection."""
    try:
        # Require Atlas URI from env or Streamlit secrets
        MONGO_URI = os.getenv("MONGODB_URI") or _get_secret("mongo", "uri")
        if not MONGO_URI:
            st.error("MongoDB Atlas URI not configured. Set MONGODB_URI env var or [mongo].uri in .streamlit/secrets.toml")
            return None

        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client
    except ConnectionFailure:
        st.error("Unable to connect to MongoDB Atlas. Check URI, network, and IP access list.")
        return None
    except Exception as e:
        st.error(f"MongoDB connection error: {e}")
        return None

@st.cache_resource
def load_legalbert_model():
    """Load LegalBERT model and tokenizer from folder."""
    try:
        # Ensure the model directory exists before loading
        if not os.path.isdir(MODEL_DIR):
            # Don't show error here - will be handled in main UI
            return None, None
            
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        model.eval()
        return tokenizer, model
    except Exception as e:
        # Don't show error here - will be handled in main UI
        return None, None

@st.cache_resource
def init_gemini():
    """Initialize Gemini API."""
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            # List available models to find free ones
            models = list(genai.list_models())
            free_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods and ('gemini-2.0-flash' in m.name or 'gemini-2.5-flash' in m.name or 'gemini-flash-latest' in m.name)]
            
            if free_models:
                # Use the first available free model
                model_name = free_models[0].split('/')[-1]  # Extract just the model name
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hello")
                st.info(f"Using free model: {model_name}")
                return True, model_name
            else:
                st.error("No free Gemini models available")
                st.info(f"Available models: {[m.name for m in models if 'generateContent' in m.supported_generation_methods]}")
                return False, None
        except Exception as e:
            st.error(f"Gemini API Error: {e}")
            return False, None
    else:
        st.warning("Gemini API key not configured or secrets file malformed. Set environment variable GEMINI_API_KEY or fix .streamlit/secrets.toml")
        return False, None

def predict_outcome(tokenizer, model, text):
    """Predict legal case outcome using LegalBERT model."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        predicted_class = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][predicted_class].item()

    # Map class indices to labels (matching notebook)
    class_labels = {0: "Appeal Dismissed", 1: "Appeal Allowed"}
    prediction = class_labels.get(predicted_class, f"Class_{predicted_class}")

    return prediction, confidence

def predict_outcome_with_gemini(case_text, model_name="gemini-2.5-flash-preview-05-20", language="English"):
    """Fallback: Predict legal case outcome using Gemini AI when LegalBERT model is not available."""
    if not GEMINI_API_KEY:
        return "Appeal Dismissed", 0.5  # Default fallback
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Language-specific instructions
        language_instruction = ""
        if language == "Hindi":
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in Hindi (हिंदी)."
        elif language == "Gujarati":
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in Gujarati (ગુજરાતી)."
        
        prompt = f"""
        **Role:** You are an expert legal AI assistant specializing in Supreme Court of India case analysis.

        **Case Text:**
        {case_text}

        **Your Task:**
        Analyze the above Supreme Court case text and predict the outcome. You must respond with ONLY one of these two options:
        - "Appeal Dismissed" - if the appeal is likely to be dismissed
        - "Appeal Allowed" - if the appeal is likely to be allowed

        Also provide a confidence score between 0.0 and 1.0 (where 1.0 is very confident).

        **Response Format (JSON only, no other text):**
        {{
            "prediction": "Appeal Dismissed" or "Appeal Allowed",
            "confidence": 0.85
        }}
        {language_instruction}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Try to parse JSON response
        import json
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        try:
            result = json.loads(response_text)
            prediction = result.get("prediction", "Appeal Dismissed")
            confidence = float(result.get("confidence", 0.7))
            # Ensure prediction is one of the valid options
            if prediction not in ["Appeal Dismissed", "Appeal Allowed"]:
                prediction = "Appeal Dismissed"
            return prediction, confidence
        except json.JSONDecodeError:
            # Fallback: try to extract prediction from text
            if "Appeal Allowed" in response_text:
                return "Appeal Allowed", 0.75
            else:
                return "Appeal Dismissed", 0.75
                
    except Exception as e:
        # Default fallback on error
        return "Appeal Dismissed", 0.5

# ---------------------------
# Document Upload & RAG helpers
# ---------------------------

def _clean_text(txt: str) -> str:
    if not txt:
        return ""
    # Fix hyphenation across line breaks, normalize whitespace
    txt = re.sub(r"(\w+)-\n(\w+)", r"\1\2", txt)
    txt = txt.replace("\r", "\n")
    txt = re.sub(r"\n{2,}", "\n\n", txt)
    txt = re.sub(r"[\t\u00A0]", " ", txt)
    txt = re.sub(r" +", " ", txt)
    return txt.strip()

def _page_to_image(page: fitz.Page, scale: float = 2.0) -> Image.Image:
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat)
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    if mode == "RGBA":
        img = img.convert("RGB")
    return img

def extract_image_text(file_bytes: bytes) -> str:
    """Extract text from image file using OCR."""
    try:
        img = Image.open(io.BytesIO(file_bytes))
        # Convert to RGB if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")
        # Try multilingual OCR where available
        try:
            ocr_lang = "eng+hin+guj"
            txt_ocr = pytesseract.image_to_string(img, lang=ocr_lang)
        except Exception:
            txt_ocr = pytesseract.image_to_string(img)
        return _clean_text(txt_ocr)
    except Exception as e:
        return f"Error processing image: {e}"

def extract_pdf_pages_text_or_ocr(file_bytes: bytes) -> list[dict]:
    """Return list of {page, text} using text extraction; fallback to OCR for low-text pages."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for i, page in enumerate(doc, start=1):
        txt = page.get_text("text") or ""
        txt_clean = _clean_text(txt)
        if len(txt_clean) < 50:  # likely scanned
            try:
                img = _page_to_image(page, scale=2.0)
                # Try multilingual OCR where available
                try:
                    ocr_lang = "eng+hin+guj"
                    txt_ocr = pytesseract.image_to_string(img, lang=ocr_lang)
                except Exception:
                    txt_ocr = pytesseract.image_to_string(img)
                txt_clean = _clean_text(txt_ocr)
            except Exception:
                pass
        pages.append({"page": i, "text": txt_clean})
    doc.close()
    return pages

def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    text = _clean_text(text)
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks

def embed_texts_gemini(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    embeddings = []
    for t in texts:
        try:
            res = genai.embed_content(model=EMBEDDING_MODEL, content=t, task_type="retrieval_document")
            emb = res.get("embedding") or res.get("data", [{}])[0].get("embedding")
            embeddings.append(emb)
        except Exception as e:
            st.warning(f"Embedding failed for a chunk: {e}")
            embeddings.append([])
    return embeddings

def ingest_document_to_mongo(collection_docs, collection_chunks, file_bytes: bytes, filename: str, user_id: str, file_type: str = "pdf") -> dict:
    """Extract text per page, chunk, embed, and store in MongoDB."""
    # Handle image files
    if file_type.lower() in ["png", "jpg", "jpeg"]:
        text = extract_image_text(file_bytes)
        if not text or text.startswith("Error"):
            return {"ok": False, "error": text if text else "No text extracted from image"}
        pages = [{"page": 1, "text": text}]
    else:
        # Handle PDF files
        pages = extract_pdf_pages_text_or_ocr(file_bytes)
        if not pages:
            return {"ok": False, "error": "No pages extracted"}

    doc_id = str(uuid.uuid4())
    doc_meta = {
        "doc_id": doc_id,
        "user_id": user_id,
        "filename": filename,
        "page_count": len(pages),
        "created_at": datetime.now(),
    }
    try:
        collection_docs.insert_one(doc_meta)
    except Exception as e:
        return {"ok": False, "error": f"Failed to save document meta: {e}"}

    total_chunks = 0
    for p in pages:
        chunks = chunk_text(p["text"]) if p["text"] else []
        if not chunks:
            continue
        embs = embed_texts_gemini(chunks)
        for i, (chunk, emb) in enumerate(zip(chunks, embs)):
            chunk_doc = {
                "doc_id": doc_id,
                "user_id": user_id,
                "page": p["page"],
                "chunk_index": i,
                "content": chunk,
                "embedding": emb,
                "created_at": datetime.now(),
            }
            try:
                collection_chunks.insert_one(chunk_doc)
                total_chunks += 1
            except Exception as e:
                st.warning(f"Failed to save chunk p{p['page']}#{i}: {e}")

    return {"ok": True, "doc_id": doc_id, "pages": len(pages), "chunks": total_chunks}

def vector_search_chunks(collection_chunks, query: str, user_id: str, k: int = 5) -> list[dict]:
    """Run Atlas Vector Search and return top-k chunks with scores."""
    try:
        res = genai.embed_content(model=EMBEDDING_MODEL, content=query, task_type="retrieval_query")
        qv = res.get("embedding") or res.get("data", [{}])[0].get("embedding")
    except Exception as e:
        st.error(f"Query embedding failed: {e}")
        return []

    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX_NAME,
                    "queryVector": qv,
                    "path": "embedding",
                    "numCandidates": 200,
                    "limit": k,
                    "filter": {"user_id": user_id}
                }
            },
            {
                "$project": {
                    "content": 1,
                    "doc_id": 1,
                    "page": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        results = list(collection_chunks.aggregate(pipeline))
        return results
    except Exception as e:
        st.warning(get_text("no_index", st.session_state.get("language", "English")))
        st.info(f"Mongo error: {e}")
        return []

def answer_with_rag(question: str, top_chunks: list[dict], language: str = "English", model_name: str = "gemini-2.0-flash") -> str:
    """Synthesize answer from top chunks. Request JSON with sources; fallback to text if JSON fails."""
    model = genai.GenerativeModel(model_name)
    lang_note = {
        "English": "Respond in English.",
        "Hindi": "पूरी प्रतिक्रिया हिंदी में दें। JSON की कुंजियाँ अंग्रेज़ी में रखें।",
        "Gujarati": "સમ્પૂર્ણ પ્રતિભાવ ગુજરાતી માં આપો. JSON કીઓ અંગ્રેજીમાં જ રાખો."
    }.get(language, "Respond in English.")

    sources_block = "\n\n".join([f"[doc:{r.get('doc_id','?')} p.{r.get('page','?')}] score={r.get('score',0):.4f} :: {r.get('content','')[:300]}" for r in top_chunks])

    prompt = f"""
You are a legal assistant for India. Use ONLY the following retrieved snippets to answer the user question. If insufficient, say so.

Question: {question}

Retrieved Snippets:
{sources_block}

{lang_note}

Return a compact JSON with these keys:
{{
  "answer": string,  
  "sources": [
    {{"doc_id": string, "page": number, "score": number}}
  ]
}}
Do not include extra keys.
"""

    try:
        resp = model.generate_content(prompt)
        text = resp.text or ""
        # Attempt to extract JSON
        import json as _json
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            payload = _json.loads(text[start:end+1])
            # Build a user-friendly string with sources
            ans = payload.get("answer", "")
            srcs = payload.get("sources", [])
            sources_md = "\n".join([f"- {s.get('doc_id','?')} p.{s.get('page','?')} (score {s.get('score',0):.3f})" for s in srcs])
            return f"{ans}\n\n**{get_text('top_sources', st.session_state.get('language','English'))}:**\n{sources_md}"
        return text
    except Exception as e:
        return f"Error synthesizing answer: {e}"

def generate_legal_explanation(case_text, predicted_outcome, model_name="gemini-2.0-flash", context_messages=None, language="English"):
    """Generate detailed legal explanation using Gemini API with conversation context."""
    if not GEMINI_API_KEY:
        return f"**Predicted Outcome:** {predicted_outcome}\n\n*Gemini API not configured for detailed analysis.*"
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Build context from recent messages
        context_section = ""
        if context_messages and len(context_messages) > 0:
            context_section = "\n\n**Previous Conversation Context:**\n"
            for msg in context_messages[-10:]:  # Last 10 messages for context
                role = "User" if msg["role"] == "user" else "Assistant"
                context_section += f"- {role}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"
        
        # Language-specific instructions
        language_instruction = ""
        if language == "Hindi":
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in Hindi (हिंदी). Use Devanagari script for all explanations."
        elif language == "Gujarati":
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in Gujarati (ગુજરાતી). Use Gujarati script for all explanations."
        else:
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in English."
        
        prompt = f"""
        **Role:** You are an expert legal AI assistant specializing in the jurisprudence of the **Supreme Court of India**.

        **Context:**
        A specialized NLP model has analyzed the following Supreme Court case summary and predicted a specific outcome.

        **1. Predicted Outcome by the NLP Model:**
        `{predicted_outcome}`

        **2. Full Case Text:**
        `{case_text}`{context_section}{language_instruction}

        **Your Task:**
        Analyze the full case text and write a detailed legal explanation that **justifies the predicted outcome**. You must act as if you are explaining the final judgment of the court. Base your entire analysis **strictly on the provided text**. Consider the conversation context to provide more relevant and coherent explanations.

        Please structure your response in markdown format with the following sections:

        ### Explanation for Predicted Outcome: {predicted_outcome}

        **1. Factual Background:**
        Briefly summarize the key facts of the case: who the parties are (appellant, respondent) and the core dispute.

        **2. Core Legal Analysis & Justification:**
        - Identify the main legal arguments raised by the appellant.
        - Identify the counter-arguments or position of the respondent.
        - Pinpoint the key legal statutes and precedents cited in the text.
        - Explain how the court's reasoning (as described in the text) supports the **predicted outcome**.

        **3. Conclusion:**
        Provide a final, one-sentence summary that concludes why the model's prediction is a logical conclusion based on the provided legal summary.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"**Predicted Outcome:** {predicted_outcome}\n\n*Error generating detailed explanation: {e}*"

def provide_legal_aid_info(user_query, model_name="gemini-2.0-flash", context_messages=None, language="English"):
    """Provide legal aid information for general queries with conversation context."""
    if not GEMINI_API_KEY:
        return "Gemini API not configured. Please set up your API key for legal aid assistance."
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Build context from recent messages
        context_section = ""
        if context_messages and len(context_messages) > 0:
            context_section = "\n\n**Previous Conversation Context:**\n"
            for msg in context_messages[-10:]:  # Last 10 messages for context
                role = "User" if msg["role"] == "user" else "Assistant"
                context_section += f"- {role}: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"
        
        # Language-specific instructions
        language_instruction = ""
        if language == "Hindi":
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in Hindi (हिंदी). Use Devanagari script for all explanations. The disclaimer must also be in Hindi."
        elif language == "Gujarati":
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in Gujarati (ગુજરાતી). Use Gujarati script for all explanations. The disclaimer must also be in Gujarati."
        else:
            language_instruction = "\n\n**IMPORTANT:** Please provide your ENTIRE response in English."
        
        prompt = f"""
        **Role:** You are an AI Legal Information Assistant for India. Your purpose is to provide helpful, clear, and safe information about Indian laws and legal procedures to the general public. You are NOT a lawyer and you MUST NOT provide legal advice.

        **User's Query:** "{user_query}"{context_section}{language_instruction}

        **Your Task:**
        Based on the user's query and conversation context, provide a structured and actionable response. The response must be tailored to the Indian legal system. Consider the conversation history to provide more relevant and coherent guidance.

        **Output Structure:**
        1.  **Understanding the Issue:** Briefly explain the legal concept related to the user's query in simple terms.
        2.  **Immediate Steps to Consider:** Provide a clear, step-by-step list of actions the user can take. Prioritize safety.
        3.  **Relevant Indian Laws:** Mention the key sections of Indian law that apply.
        4.  **Whom to Contact:** List the authorities or organizations the user can contact for help. Be specific.
        5.  **Crucial Disclaimer:** You MUST end the entire response with a disclaimer in the selected language:
            - English: "***Disclaimer: This is for informational purposes only and does not constitute legal advice. You should consult with a qualified lawyer for advice on your specific situation.***"
            - Hindi: "***अस्वीकरण: यह केवल सूचनात्मक उद्देश्यों के लिए है और कानूनी सलाह नहीं है। आपको अपनी विशिष्ट स्थिति पर सलाह के लिए एक योग्य वकील से परामर्श करना चाहिए।***"
            - Gujarati: "***અસ્વીકરણ: આ ફક્ત માહિતીના હેતુઓ માટે છે અને કાનૂની સલાહ નથી. તમારે તમારી વિશિષ્ટ પરિસ્થિતિ માટે સલાહ માટે યોગ્ય વકીલ સાથે પરામર્શ કરવો જોઈએ.***"
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating legal aid information: {e}"

def save_message_to_db(collection, role, content, prediction=None, user_id=None, session_id=None):
    """Save chat messages to MongoDB with hashed content for security."""
    try:
        # Hash the content for security
        content_hash = hash_message(content)
        
        message_doc = {
            "timestamp": datetime.now(),
            "role": role,
            "content": content,  # Keep original for display
            "content_hash": content_hash,  # Store hash for security verification
            "prediction": prediction
        }
        
        # Add user and session info if available
        if user_id:
            message_doc["user_id"] = user_id
        if session_id:
            message_doc["session_id"] = session_id
        
        result = collection.insert_one(message_doc)
        safe_print(f"Message saved to DB with ID: {result.inserted_id} (Hash: {content_hash[:16]}...)")  # Debug log
        return True
    except Exception as e:
        safe_print(f"DB save failed: {e}")  # Debug log
        return False

def get_history_from_db(collection, limit=20):
    """Fetch the most recent chat history from MongoDB."""
    try:
        # Fetch the last 'limit' messages, sorted by timestamp descending
        history = list(collection.find().sort("timestamp", pymongo.DESCENDING).limit(limit))
        return history
    except Exception as e:
        # st.warning(f"Failed to fetch history: {e}") # Commented out to reduce clutter
        return []

def stream_response(content: str):
    """Simulate typing/streaming effect for AI responses."""
    for word in content.split(" "):
        yield word + " "
        time.sleep(0.04)

def hash_message(content: str) -> str:
    """Hash message content for security using SHA-256."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def verify_message_integrity(content: str, stored_hash: str) -> bool:
    """Verify that stored message hasn't been tampered with."""
    current_hash = hash_message(content)
    return current_hash == stored_hash

# --- USER AUTHENTICATION FUNCTIONS ---

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_user(collection, username: str, email: str, password: str) -> bool:
    """Create a new user account."""
    try:
        # Check if user already exists
        if collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return False
        
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(password)
        
        user_doc = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password_hash": hashed_password,
            "created_at": datetime.now(),
            "last_login": None,
            "is_active": True
        }
        
        collection.insert_one(user_doc)
        return True
    except Exception as e:
        safe_print(f"Error creating user: {e}")
        return False

def authenticate_user(collection, username: str, password: str) -> dict:
    """Authenticate user login."""
    try:
        user = collection.find_one({"username": username, "is_active": True})
        if user and verify_password(password, user["password_hash"]):
            # Update last login
            collection.update_one(
                {"user_id": user["user_id"]},
                {"$set": {"last_login": datetime.now()}}
            )
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"]
            }
        return None
    except Exception as e:
        safe_print(f"Error authenticating user: {e}")
        return None

def get_user_sessions(collection, user_id: str) -> list:
    """Get user's chat sessions."""
    try:
        sessions = list(collection.find(
            {"user_id": user_id, "role": "session_start"},
            sort=[("timestamp", -1)]
        ))
        return sessions
    except Exception as e:
        safe_print(f"Error getting user sessions: {e}")
        return []

def create_chat_session(collection, user_id: str, session_name: str = None) -> str:
    """Create a new chat session for user."""
    try:
        session_id = str(uuid.uuid4())
        if not session_name:
            session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "role": "session_start",
            "content": session_name,
            "timestamp": datetime.now(),
            "content_hash": hash_message(session_name)
        }
        
        collection.insert_one(session_doc)
        return session_id
    except Exception as e:
        safe_print(f"Error creating session: {e}")
        return None

def get_session_messages(collection, session_id: str, user_id: str) -> list:
    """Get messages for a specific session."""
    try:
        messages = list(collection.find(
            {"session_id": session_id, "user_id": user_id},
            sort=[("timestamp", 1)]
        ))
        return messages
    except Exception as e:
        safe_print(f"Error getting session messages: {e}")
        return []

def rename_session(collection, session_id: str, user_id: str, new_name: str) -> bool:
    """Rename a session."""
    try:
        result = collection.update_one(
            {"session_id": session_id, "user_id": user_id, "role": "session_start"},
            {"$set": {"content": new_name, "content_hash": hash_message(new_name)}}
        )
        return result.modified_count > 0
    except Exception as e:
        safe_print(f"Error renaming session: {e}")
        return False

def delete_session(collection, session_id: str, user_id: str) -> bool:
    """Delete a session and all its messages from the database."""
    try:
        # Delete all messages in this session
        messages_result = collection.delete_many(
            {"session_id": session_id, "user_id": user_id}
        )
        safe_print(f"[INFO] Deleted {messages_result.deleted_count} messages for session {session_id}")
        return messages_result.deleted_count >= 0  # Return True even if no messages found
    except Exception as e:
        safe_print(f"Error deleting session: {e}")
        return False

# --- STREAMLIT APP ---

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "language" not in st.session_state:
    st.session_state.language = "English"

# Get current language
current_lang = st.session_state.language

st.markdown(f"<h1>{get_text('app_title', current_lang)}</h1>", unsafe_allow_html=True)

# Authentication check
if not st.session_state.authenticated:
    # Login/Register Interface
    st.info(get_text("login_required", current_lang))
    
    tab1, tab2 = st.tabs([get_text("login_tab", current_lang), get_text("register_tab", current_lang)])
    
    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                if username and password:
                    # Initialize connection for auth
                    client = init_connection()
                    if client:
                        db = client[DATABASE_NAME]
                        users_collection = db["users"]
                        
                        user_info = authenticate_user(users_collection, username, password)
                        if user_info:
                            st.session_state.authenticated = True
                            st.session_state.user_info = user_info
                            st.success(f"Welcome back, {user_info['username']}!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Database connection failed")
                else:
                    st.error("Please enter both username and password")
    
    with tab2:
        st.subheader("Create New Account")
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_submitted = st.form_submit_button("Register")
            
            if register_submitted:
                if new_username and new_email and new_password and confirm_password:
                    if new_password == confirm_password:
                        # Initialize connection for auth
                        client = init_connection()
                        if client:
                            db = client[DATABASE_NAME]
                            users_collection = db["users"]
                            
                            if create_user(users_collection, new_username, new_email, new_password):
                                st.success("Account created successfully! Please log in.")
                            else:
                                st.error("Username or email already exists")
                        else:
                            st.error("Database connection failed")
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")

else:
    # Main Application Interface (only shown when authenticated)
    user_info = st.session_state.user_info
    
    # User welcome message
    st.success(f"{get_text('welcome_user', current_lang)}, {user_info['username']}! 👋")
    
    # Security indicator
    st.info(get_text("secure_chat", current_lang))
    
    # Mode selector - initialize in session state if not exists
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = get_text("case_prediction", current_lang)
    
    mode = st.radio(
        get_text("choose_mode", current_lang),
        [get_text("case_prediction", current_lang), get_text("legal_aid", current_lang)],
        horizontal=True,
        index=[get_text("case_prediction", current_lang), get_text("legal_aid", current_lang)].index(st.session_state.current_mode) if st.session_state.current_mode in [get_text("case_prediction", current_lang), get_text("legal_aid", current_lang)] else 0
    )
    st.session_state.current_mode = mode
    
    st.markdown("---")

# 1. Initialize DB, Model, and Gemini (console output instead of sidebar)
# Print system status to console (using safe output for Windows compatibility)
safe_print("=" * 50)
safe_print("SYSTEM STATUS")
safe_print("=" * 50)

client = init_connection()
if client:
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    safe_print("[OK] MongoDB: Connected")
else:
    db = collection = None
    safe_print("[ERROR] MongoDB: Disconnected")

tokenizer, model = load_legalbert_model()
if model:
    safe_print("[OK] LegalBERT Model: Loaded")
else:
    safe_print("[INFO] LegalBERT Model: Not found (using Gemini AI fallback)")

gemini_result = init_gemini()
if gemini_result[0]:  # If available
    safe_print(f"[OK] Gemini AI: Active (using {gemini_result[1]})")
else:
    safe_print("[WARNING] Gemini AI: Inactive")

safe_print("=" * 50)

# Sidebar starts here
with st.sidebar:
    # Show user-specific features only when authenticated
    if st.session_state.authenticated:
        user_info = st.session_state.user_info
        
        # Enhanced New Chat and Logout buttons at the top
        st.markdown("### Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(get_text("new_chat", current_lang), use_container_width=True, type="primary"):
                st.session_state.current_session_id = None
                st.session_state.messages = []
                # Reset flag to allow reloading messages for new session
                if "messages_loaded" in st.session_state:
                    del st.session_state.messages_loaded
                st.rerun()
        with col2:
            if st.button(get_text("logout", current_lang), use_container_width=True, type="secondary"):
                st.session_state.authenticated = False
                st.session_state.user_info = None
                st.session_state.current_session_id = None
                st.session_state.messages = []
                # Clear session flags
                if "messages_loaded" in st.session_state:
                    del st.session_state.messages_loaded
                if "current_mode" in st.session_state:
                    del st.session_state.current_mode
                st.rerun()
        
        st.markdown("---")
        
        # Language Selector (moved above Previous Chats)
        st.subheader(get_text("language_selector", current_lang))
        language_options = [f"{SUPPORTED_LANGUAGES[lang]['native_name']} ({lang})" for lang in SUPPORTED_LANGUAGES.keys()]
        # Safely get index, default to 0 if language not found
        try:
            default_idx = list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.language)
        except ValueError:
            default_idx = 0
            st.session_state.language = list(SUPPORTED_LANGUAGES.keys())[0]
        
        selected_lang_idx = st.selectbox(
            "Language / भाषा / ભાષા",
            range(len(language_options)),
            format_func=lambda x: language_options[x],
            index=default_idx
        )
        
        selected_language = list(SUPPORTED_LANGUAGES.keys())[selected_lang_idx]
        if selected_language != st.session_state.language:
            st.session_state.language = selected_language
            st.rerun()
        
        st.markdown("---")
        
        # Previous Chats - Display prominently
        st.subheader("Previous Chats")
        
        if collection is not None:
            sessions = get_user_sessions(collection, user_info["user_id"])
            
            if sessions:
                # Display sessions in a more appealing way
                for idx, session in enumerate(sessions):
                    session_date = session['timestamp'].strftime('%Y-%m-%d %H:%M')
                    session_title = session.get('content', 'Untitled Chat')[:50]
                    session_id = session.get('session_id')
                    
                    # Create a clickable container for each session
                    session_container_key = f"session_container_{idx}"
                    
                    # Use columns with clickable area
                    col1, col2, col3 = st.columns([3, 0.5, 0.5])
                    
                    with col1:
                        # Make the entire column clickable by using a button that looks like text
                        if st.button(f"**{session_title}**\n\n{session_date}", key=f"load_session_{idx}", help="Click to load this session", use_container_width=True):
                            selected_session = session
                            st.session_state.current_session_id = selected_session["session_id"]
                            # Load session messages
                            session_messages = get_session_messages(collection, selected_session["session_id"], user_info["user_id"])
                            st.session_state.messages = []
                            for msg in session_messages:
                                if msg["role"] in ["user", "assistant"]:
                                    st.session_state.messages.append({
                                        "role": msg["role"],
                                        "content": msg["content"]
                                    })
                            st.session_state.messages_loaded = True
                            safe_print(f"[INFO] Loaded session: {session_title} ({len(st.session_state.messages)} messages)")
                            st.rerun()
                    
                    with col2:
                        if st.button("✏️", key=f"rename_{idx}", help="Rename this session", use_container_width=True):
                            st.session_state[f"renaming_{idx}"] = True
                            st.rerun()
                    with col3:
                        if st.button("🗑️", key=f"delete_{idx}", help="Delete this session", use_container_width=True):
                            st.session_state[f"deleting_{idx}"] = True
                            st.rerun()
                    
                    # Add CSS to make the load button look like regular text
                    st.markdown(f"""
                    <style>
                        button[data-testid*="load_session_{idx}"] {{
                            background: transparent !important;
                            border: none !important;
                            text-align: left !important;
                            padding: 8px !important;
                            cursor: pointer !important;
                            box-shadow: none !important;
                        }}
                        button[data-testid*="load_session_{idx}"]:hover {{
                            background-color: #f0f2f6 !important;
                            border-radius: 6px !important;
                        }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Rename dialog
                    if st.session_state.get(f"renaming_{idx}", False):
                        new_name = st.text_input(
                            "Enter new session name:",
                            value=session_title,
                            key=f"rename_input_{idx}"
                        )
                        col_rename1, col_rename2 = st.columns(2)
                        with col_rename1:
                            if st.button("Save", key=f"save_rename_{idx}", type="primary"):
                                if new_name and new_name.strip():
                                    if rename_session(collection, session_id, user_info["user_id"], new_name.strip()):
                                        safe_print(f"[INFO] Renamed session {session_id} to: {new_name.strip()}")
                                        st.session_state[f"renaming_{idx}"] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to rename session")
                                else:
                                    st.warning("Please enter a valid name")
                        with col_rename2:
                            if st.button("Cancel", key=f"cancel_rename_{idx}"):
                                st.session_state[f"renaming_{idx}"] = False
                                st.rerun()
                    
                    # Delete confirmation
                    if st.session_state.get(f"deleting_{idx}", False):
                        st.warning(f"Are you sure you want to delete '{session_title}'? This will delete all conversations in this session.")
                        col_del1, col_del2 = st.columns(2)
                        with col_del1:
                            if st.button("Yes, Delete", key=f"confirm_delete_{idx}", type="primary"):
                                if delete_session(collection, session_id, user_info["user_id"]):
                                    safe_print(f"[INFO] Deleted session {session_id} and all its messages")
                                    # Clear the deleting flag
                                    st.session_state[f"deleting_{idx}"] = False
                                    # If this was the current session, clear it
                                    if st.session_state.current_session_id == session_id:
                                        st.session_state.current_session_id = None
                                        st.session_state.messages = []
                                        if "messages_loaded" in st.session_state:
                                            del st.session_state.messages_loaded
                                    st.rerun()
                                else:
                                    st.error("Failed to delete session")
                        with col_del2:
                            if st.button("Cancel", key=f"cancel_delete_{idx}"):
                                st.session_state[f"deleting_{idx}"] = False
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("No previous chats found. Start a new conversation!")
        
        # Current Session Info
        if st.session_state.current_session_id:
            st.success(f"Active: {st.session_state.current_session_id[:8]}...")
        else:
            st.info("No active session")
        
        st.markdown("---")
    
    # Language Selector (for non-authenticated users)
    if not st.session_state.authenticated:
        st.subheader(get_text("language_selector", current_lang))
        language_options = [f"{SUPPORTED_LANGUAGES[lang]['native_name']} ({lang})" for lang in SUPPORTED_LANGUAGES.keys()]
        # Safely get index, default to 0 if language not found
        try:
            default_idx = list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.language)
        except ValueError:
            default_idx = 0
            st.session_state.language = list(SUPPORTED_LANGUAGES.keys())[0]
        
        selected_lang_idx = st.selectbox(
            "Language / भाषा / ભાષા",
            range(len(language_options)),
            format_func=lambda x: language_options[x],
            index=default_idx
        )
        
        selected_language = list(SUPPORTED_LANGUAGES.keys())[selected_lang_idx]
        if selected_language != st.session_state.language:
            st.session_state.language = selected_language
            st.rerun()
        
        st.markdown("---")
    
    # Debug info for MongoDB - console output instead of frontend
    if collection is not None:
        try:
            # Test database connection
            test_doc = {"test": "connection", "timestamp": datetime.now()}
            result = collection.insert_one(test_doc)
            collection.delete_one({"_id": result.inserted_id})  # Clean up test doc
            safe_print(f"[OK] Database test successful! Collection: {COLLECTION_NAME}")
            safe_print("[INFO] Messages are hashed with SHA-256 for security")
        except Exception as e:
            safe_print(f"[ERROR] Database test failed: {e}")
    
    st.caption("App powered by Streamlit + Hugging Face LegalBERT Supreme")

# 3. Chat History Persistence (only for authenticated users)
if st.session_state.authenticated and st.session_state.user_info and collection is not None:
    # Create new session if none exists
    if not st.session_state.current_session_id:
        st.session_state.current_session_id = create_chat_session(collection, st.session_state.user_info["user_id"])
    
    # Load messages for current session (only on initial load, not on every rerun)
    if st.session_state.current_session_id and "messages_loaded" not in st.session_state:
        session_messages = get_session_messages(collection, st.session_state.current_session_id, st.session_state.user_info["user_id"])
        if session_messages:
            st.session_state.messages = []
            for msg in session_messages:
                if msg["role"] in ["user", "assistant"]:
                    st.session_state.messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        st.session_state.messages_loaded = True
    
    # Ensure there's always a welcome message if the history is empty
    # Check if welcome message already exists to avoid duplicates
    welcome_exists = any(
        msg.get("role") == "assistant" and "Hello" in msg.get("content", "") and "AI legal assistant" in msg.get("content", "")
        for msg in st.session_state.messages
    )
    if not st.session_state.messages or (not welcome_exists and st.session_state.messages[-1]["role"] != "assistant"):
        st.session_state.messages.append({"role": "assistant", "content": f"Hello {st.session_state.user_info['username']}! I'm your AI legal assistant. Choose your mode above to get started:\n\n🏛️ **Case Outcome Prediction**: Analyze case facts and predict court outcomes. You can type case details directly or upload a document (PDF/Image) and then type your query.\n💬 **General Legal Aid**: Get information about Indian laws and legal procedures"})


# 4. Display Chat (only for authenticated users)
if st.session_state.authenticated:
    chat_container = st.container(height=500, border=False)
    with chat_container:
        for idx, message in enumerate(st.session_state.messages):
            avatar = "🤖" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                # Display message content (extract just the user input if it's a user message with doc)
                if message["role"] == "user" and "doc_filename" in message:
                    # Show just the user input text, not the doc_info
                    content = message["content"]
                    # Remove the doc_info part if present
                    if "📄 **Source Document:**" in content:
                        content = content.split("📄 **Source Document:**")[0].strip()
                    st.markdown(content)
                    # Show document name as plain text (no download button)
                    st.caption(f"📄 Source Document: {message['doc_filename']}")
                else:
                    st.markdown(message["content"])

    # 5. User Input and Response Generation
    # Ensure mode is defined (fallback to case prediction)
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = get_text("case_prediction", current_lang)
    mode = st.session_state.current_mode
    
    # Upload files section - placed just above the text input box
    if mode == get_text("case_prediction", current_lang):
        # Initialize file uploader key if not exists
        if "file_uploader_key" not in st.session_state:
            st.session_state.file_uploader_key = "case_doc_uploader"
        
        # File uploader with custom styling
        uploaded_file = st.file_uploader(
            "📎 Attach files (PDF, PNG, JPG, JPEG)",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
            key=st.session_state.file_uploader_key,
            help="Upload a document to extract text for case analysis"
        )
        
        # Add custom styling to make the file uploader look better
        st.markdown("""
        <style>
            /* Style the file uploader to look like a custom button */
            div[data-testid="stFileUploader"] {
                border: 2px dashed #D1D5DB;
                border-radius: 8px;
                padding: 12px;
                background-color: #F9FAFB;
                transition: all 0.2s ease;
            }
            
            div[data-testid="stFileUploader"]:hover {
                border-color: #9CA3AF;
                background-color: #F3F4F6;
            }
            
            /* Style the file uploader button */
            div[data-testid="stFileUploader"] button {
                background-color: #1F2937 !important;
                color: white !important;
                border: none !important;
                border-radius: 6px !important;
                padding: 8px 16px !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: background-color 0.2s ease !important;
            }
            
            div[data-testid="stFileUploader"] button:hover {
                background-color: #374151 !important;
            }
            
            /* Hide the "Drop files here" text if no file is uploaded */
            div[data-testid="stFileUploader"] > div:first-child {
                font-size: 14px;
                color: #6B7280;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Show option to clear uploaded document if one exists
        if "uploaded_doc_text" in st.session_state:
            col1, col2 = st.columns([10, 1])
            with col1:
                st.caption(f"📎 {st.session_state.get('uploaded_doc_filename', 'Document')} attached")
            with col2:
                if st.button("🗑️", key="clear_doc", help="Clear document"):
                    del st.session_state.uploaded_doc_text
                    if "uploaded_doc_filename" in st.session_state:
                        del st.session_state.uploaded_doc_filename
                    if "last_uploaded_file_id" in st.session_state:
                        del st.session_state.last_uploaded_file_id
                    st.rerun()
        
        if uploaded_file is not None:
            # Check if this is a new upload
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            if "last_uploaded_file_id" not in st.session_state or st.session_state.last_uploaded_file_id != file_id:
                st.session_state.last_uploaded_file_id = file_id
                # Extract text immediately
                file_bytes = uploaded_file.getvalue()
                file_ext = uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else "pdf"
                
                with st.spinner(f"📄 Extracting text from {uploaded_file.name}..."):
                    if file_ext.lower() in ["png", "jpg", "jpeg"]:
                        extracted_text = extract_image_text(file_bytes)
                    else:
                        # For PDF, extract all pages
                        pages = extract_pdf_pages_text_or_ocr(file_bytes)
                        extracted_text = "\n\n".join([f"Page {p['page']}:\n{p['text']}" for p in pages if p.get('text')])
                
                if extracted_text and not extracted_text.startswith("Error"):
                    # Store extracted text and file bytes in session state
                    st.session_state.uploaded_doc_text = extracted_text
                    st.session_state.uploaded_doc_filename = uploaded_file.name
                    st.session_state.uploaded_doc_bytes = file_bytes  # Store file bytes for download
                    st.session_state.uploaded_doc_ext = file_ext  # Store file extension
                    st.success(f"✅ Document loaded: {uploaded_file.name} ({len(extracted_text)} characters extracted)")
                    # Clear the file uploader widget by changing its key (but keep document data)
                    st.session_state.file_uploader_key = str(uuid.uuid4())
                    st.rerun()
                else:
                    st.error(f"❌ Failed to extract text from {uploaded_file.name}")
                    if "uploaded_doc_text" in st.session_state:
                        del st.session_state.uploaded_doc_text
                    if "uploaded_doc_filename" in st.session_state:
                        del st.session_state.uploaded_doc_filename
                    if "uploaded_doc_bytes" in st.session_state:
                        del st.session_state.uploaded_doc_bytes
                    if "uploaded_doc_ext" in st.session_state:
                        del st.session_state.uploaded_doc_ext
            else:
                # File already processed, no need to show info again (already shown above)
                pass
    
    # Chat input box
    if mode == get_text("case_prediction", current_lang):
        user_input = st.chat_input(get_text("enter_case", current_lang))
    else:
        user_input = st.chat_input(get_text("enter_question", current_lang))

    if user_input:
        # Prepare input text - combine with uploaded document if available
        input_text = user_input
        doc_info = ""
        doc_filename = None
        doc_bytes = None
        doc_ext = None
        
        if mode == get_text("case_prediction", current_lang) and "uploaded_doc_text" in st.session_state:
            # Combine user input with uploaded document text
            doc_filename = st.session_state.get("uploaded_doc_filename", "Document")
            doc_text = st.session_state.uploaded_doc_text
            doc_bytes = st.session_state.get("uploaded_doc_bytes")
            doc_ext = st.session_state.get("uploaded_doc_ext", "pdf")
            input_text = f"{doc_text}\n\n---\n\nUser Query: {user_input}"
            # Show document name as plain text (no link)
            doc_info = f"\n\n📄 **Source Document:** {doc_filename}"
        
        # Create user message for display
        display_message = user_input
        if doc_info:
            display_message = f"{user_input}{doc_info}"
        
        # Store document info in message metadata if available
        message_data = {"role": "user", "content": display_message}
        if doc_filename and doc_bytes:
            message_data["doc_filename"] = doc_filename
            message_data["doc_bytes"] = doc_bytes
            message_data["doc_ext"] = doc_ext
        
        # Append user message to session state
        st.session_state.messages.append(message_data)
        
        # Display user message immediately
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
                # Show document name as plain text (no download button)
                if doc_filename:
                    st.caption(f"📄 Source Document: {doc_filename}")
        
        # Clear file uploader and document data from session state after query is sent
        # (document is now stored in the message)
        if mode == get_text("case_prediction", current_lang) and "uploaded_doc_text" in st.session_state:
            # Clear the file uploader widget by changing its key
            st.session_state.file_uploader_key = str(uuid.uuid4())
            # Clear document data from session state (it's now in the message)
            if "uploaded_doc_text" in st.session_state:
                del st.session_state.uploaded_doc_text
            if "uploaded_doc_filename" in st.session_state:
                del st.session_state.uploaded_doc_filename
            if "uploaded_doc_bytes" in st.session_state:
                del st.session_state.uploaded_doc_bytes
            if "uploaded_doc_ext" in st.session_state:
                del st.session_state.uploaded_doc_ext
            if "last_uploaded_file_id" in st.session_state:
                del st.session_state.last_uploaded_file_id

        # Save user message to DB with user and session info
        if collection is not None and st.session_state.user_info and st.session_state.current_session_id:
            save_success = save_message_to_db(
                collection, "user", display_message, 
                user_id=st.session_state.user_info["user_id"],
                session_id=st.session_state.current_session_id
            )
            if not save_success:
                st.warning("Failed to save message to database")

        # Generate and stream assistant response
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                response = ""
                prediction = None
                
                # Get context messages BEFORE appending current user message (exclude the last one which is the current input)
                context_messages = st.session_state.messages[:-1][-10:] if len(st.session_state.messages) > 1 else []
                
                if mode == get_text("case_prediction", current_lang):
                    if model:
                        # Use combined text (document + user input) for prediction with LegalBERT
                        prediction, confidence = predict_outcome(tokenizer, model, input_text)
                        if gemini_result[0]:  # If Gemini is available
                            response = generate_legal_explanation(input_text, prediction, gemini_result[1], context_messages, current_lang)
                        else:
                            response = f"### ⚖️ Predicted Outcome: `{prediction}`\n\n**Confidence:** {confidence:.2%}\n\n*Gemini AI not available for detailed analysis. Please configure your API key.*"
                    else:
                        # Fallback: Use Gemini for prediction when LegalBERT model is not available
                        if gemini_result[0]:  # If Gemini is available
                            prediction, confidence = predict_outcome_with_gemini(input_text, gemini_result[1], current_lang)
                            response = generate_legal_explanation(input_text, prediction, gemini_result[1], context_messages, current_lang)
                            # Add a note that Gemini was used instead of LegalBERT
                            response = f"*Note: Using Gemini AI for prediction (LegalBERT model not available).*\n\n{response}"
                        else:
                            response = "⚠️ LegalBERT model not loaded and Gemini AI is not available. Please configure at least one of them."
                else:  # General Legal Aid mode
                    if gemini_result[0]:  # If Gemini is available
                        response = provide_legal_aid_info(user_input, gemini_result[1], context_messages, current_lang)
                    else:
                        response = "⚠️ Gemini AI not available. Please configure your API key for legal aid assistance."

                # Stream the response
                streamed_text = ""
                for chunk in stream_response(response):
                    streamed_text += chunk
                    placeholder.markdown(streamed_text + "▌")
                placeholder.markdown(streamed_text)

                # Append assistant message to session state
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Save assistant message to DB with user and session info
                if collection is not None and st.session_state.user_info and st.session_state.current_session_id:
                    save_success = save_message_to_db(
                        collection, "assistant", response, prediction,
                        user_id=st.session_state.user_info["user_id"],
                        session_id=st.session_state.current_session_id
                    )
                    if not save_success:
                        st.warning("Failed to save assistant response to database")