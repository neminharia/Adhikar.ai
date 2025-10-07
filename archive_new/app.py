import streamlit as st
import pymongo
from pymongo.errors import ConnectionFailure
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time
from datetime import datetime
import os

# --- CONFIGURATION ---
DATABASE_NAME = "court_chat_db"
COLLECTION_NAME = "chat_messages"
MODEL_DIR = "legalbert_supreme"  # Folder containing model files

# --- PAGE SETUP ---
st.set_page_config(page_title="Legal Outcome Predictor", page_icon="⚖️", layout="wide")

# --- HELPER FUNCTIONS ---

@st.cache_resource
def init_connection():
    """Initialize MongoDB client connection."""
    try:
        # Directly use localhost instead of st.secrets
        MONGO_URI = "mongodb://localhost:27017/"
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('ping')
        return client
    except ConnectionFailure:
        return None

@st.cache_resource
def load_legalbert_model():
    """Load LegalBERT model and tokenizer from folder."""
    try:
        # Ensure the model directory exists before loading
        if not os.path.isdir(MODEL_DIR):
            st.error(f"Model directory not found: {MODEL_DIR}")
            return None, None
            
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
        return tokenizer, model
    except Exception as e:
        st.error(f"Model Load Error: {e}")
        return None, None

def predict_outcome(tokenizer, model, text):
    """Predict legal case outcome using LegalBERT model."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        predicted_class = torch.argmax(probs, dim=-1).item()
        confidence = probs[0][predicted_class].item()

    # Map your class indices to labels (Adjust these if your model has different labels)
    class_labels = ["Unfavorable", "Favorable", "Neutral"]
    prediction = class_labels[predicted_class] if predicted_class < len(class_labels) else f"Class_{predicted_class}"

    return prediction, confidence

def generate_explanation(prediction, confidence):
    """Generate explanation for the prediction."""
    conf_text = f"(Confidence: {confidence:.2%})"

    if prediction.lower() == "favorable":
        return f"The model predicts a **favorable outcome** {conf_text}. Strong legal indicators suggest a positive result."
    elif prediction.lower() == "unfavorable":
        return f"The model predicts an **unfavorable outcome** {conf_text}. The text shows patterns of weaker legal grounds."
    else:
        return f"The model predicts a **neutral or uncertain outcome** {conf_text}. The evidence may not be conclusive."

def save_message_to_db(collection, role, content, prediction=None):
    """Save chat messages to MongoDB."""
    try:
        collection.insert_one({
            "timestamp": datetime.now(),
            "role": role,
            "content": content,
            "prediction": prediction
        })
    except Exception as e:
        # st.warning(f"DB save failed: {e}") # Commented out to reduce clutter
        pass

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

# --- STREAMLIT APP ---

st.markdown("<h1>⚖️ LegalBERT Supreme - Outcome Predictor</h1>", unsafe_allow_html=True)
st.markdown("---")

# 1. Initialize DB and Model in Sidebar
with st.sidebar:
    st.subheader("⚙️ System Status")
    client = init_connection()
    if client:
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        st.success("MongoDB Connected ✅")
    else:
        db = collection = None
        st.error("MongoDB Disconnected ❌")

    tokenizer, model = load_legalbert_model()
    if model:
        st.success("Model Loaded ✅")
        st.info(f"Loaded from: {MODEL_DIR}")
    else:
        st.error("Failed to Load Model ❌")

    st.markdown("---")
    
    # 2. History Display Block
    st.subheader("🕰️ Database History")
    
    if collection is not None:
        history = get_history_from_db(collection, limit=20) # Fetch last 20 messages
        
        if history:
            with st.expander("Show Last 20 Messages"):
                # Display history
                for item in history:
                    timestamp_str = item.get("timestamp", datetime.min).strftime("%H:%M:%S")
                    role = item.get("role", "unknown")
                    
                    if role == "user":
                        content_summary = item['content'][:40] + "..." if len(item['content']) > 40 else item['content']
                        st.markdown(f"**👤 User** ({timestamp_str}): *{content_summary}*")
                    elif role == "assistant":
                        prediction = item.get("prediction", "N/A")
                        st.markdown(f"**🤖 AI** ({timestamp_str}): **Outcome: `{prediction}`**")

            st.caption(f"Found {len(history)} recent entries.")
        else:
            st.caption("No history found in the database.")
    else:
        st.caption("Cannot access history (DB disconnected).")

    st.markdown("---")
    st.caption("App powered by Streamlit + Hugging Face LegalBERT Supreme")

# 3. Chat History Persistence (The core update for refresh persistence)
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    
    # Try to load the last 10 messages from DB to restore history on a new session/hard refresh
    if collection is not None:
        # Use ASCENDING sort to ensure messages are in chronological order for display
        db_history = list(collection.find().sort("timestamp", pymongo.ASCENDING).limit(10)) 
        
        if db_history:
            for item in db_history:
                # Only restore 'user' and 'assistant' roles for chat display
                if item.get('role') in ['user', 'assistant']:
                    st.session_state["messages"].append({
                        "role": item['role'],
                        "content": item['content']
                    })

    # Ensure there's always a welcome message if the history is empty
    if not st.session_state["messages"] or st.session_state["messages"][-1]["role"] != "assistant":
         st.session_state["messages"].append({"role": "assistant", "content": "Hello! I’m LegalBERT Supreme. Please describe your case facts for analysis."})


# 4. Display Chat
chat_container = st.container(height=500, border=False)
with chat_container:
    for message in st.session_state["messages"]:
        avatar = "🤖" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# 5. User Input and Response Generation
user_input = st.chat_input("Enter case facts here...")

if user_input:
    # Append user message to session state
    st.session_state["messages"].append({"role": "user", "content": user_input})
    
    # Display user message immediately
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

    # Save user message to DB
    if collection is not None:
        save_message_to_db(collection, "user", user_input)

    # Generate and stream assistant response
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            placeholder = st.empty()
            response = "⚠️ Model not loaded. Please check your model folder path."
            prediction = None
            
            if model:
                prediction, confidence = predict_outcome(tokenizer, model, user_input)
                explanation = generate_explanation(prediction, confidence)
                response = f"### ⚖️ Predicted Outcome: `{prediction}`\n\n**🔎 Model Analysis:** {explanation}\n\n*Generated using LegalBERT Supreme*"

                streamed_text = ""
                for chunk in stream_response(response):
                    streamed_text += chunk
                    placeholder.markdown(streamed_text + "▌")
                placeholder.markdown(streamed_text)
            else:
                placeholder.markdown(response)

            # Append assistant message to session state
            st.session_state["messages"].append({"role": "assistant", "content": response})
            
            # Save assistant message to DB
            if collection is not None:
                save_message_to_db(collection, "assistant", response, prediction)