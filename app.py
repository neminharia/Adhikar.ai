import streamlit as st
import pymongo
from pymongo.errors import ConnectionFailure
import joblib
import os
import time # Used for streaming effect
from datetime import datetime

# --- CONFIGURATION ---
DATABASE_NAME = "court_chat_db"
COLLECTION_NAME = "chat_messages"
MODEL_FILE = 'court_case_predictor.pkl'

# --- PAGE SETUP (Modern Look) ---
st.set_page_config(
    page_title="Legal Outcome Predictor",
    page_icon="⚖️",
    layout="wide", # Use wide layout for more space
    initial_sidebar_state="expanded"
)

# --- HELPER FUNCTIONS (Model and Database) ---

@st.cache_resource
def init_connection():
    """Initializes and caches the MongoDB client connection."""
    MONGO_URI = st.secrets.get("mongo", {}).get("uri") 
    
    if not MONGO_URI:
        MONGO_URI = "mongodb://localhost:27017/" 
        
    client = None

    try:
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('ping') 
        return client
        
    except ConnectionFailure as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        return None
        
    except Exception as e:
        print(f"❌ An unexpected error occurred during connection: {e}")
        return None

@st.cache_resource
def load_ml_model():
    """Loads and caches the ML model."""
    if not os.path.exists(MODEL_FILE):
        return None
    try:
        return joblib.load(MODEL_FILE)
    except Exception as e:
        print(f"Error loading ML model: {e}")
        return None

def predict_and_explain(model, case_facts: str) -> tuple[str, str]:
    """Makes a prediction and provides a simple, hardcoded explanation."""
    if model is None:
        return "Model Error", "Cannot run prediction because the model is not loaded."
        
    # Simulate processing time for a "real-time" feel
    time.sleep(1.5) 
        
    prediction = model.predict([case_facts])[0]

    # Simple Explanation Logic
    if 'Petitioner Wins' in prediction:
        explanation = (
            "The model detected features highly correlated with success for the petitioner, "
            "such as terms related to **'violation,'** **'breach of contract,'** or **'overwhelming proof.'** "
            "This suggests the facts strongly support the legal standard for a claim, based on historical data."
        )
    else:
        explanation = (
            "The prediction leans towards the respondent, likely due to language associated with "
            "**'insufficient evidence,'** **'self-defense,'** or **'procedural error,'** which often leads to dismissal. "
            "Consider strengthening the presentation of core evidence."
        )

    return prediction, explanation

def save_message_to_db(collection, role: str, content: str, prediction: str = None):
    """Saves a message to the MongoDB collection."""
    try:
        message_doc = {
            "timestamp": datetime.now(),
            "role": role,
            "content": content,
            "prediction": prediction
        }
        collection.insert_one(message_doc)
    except Exception as e:
        st.warning(f"DB save failed. Error: {e}")

# --- STREAMING FUNCTION ---
def stream_response(content: str):
    """Generates the streaming effect for the assistant's response."""
    for chunk in content.split(" "):
        yield chunk + " "
        time.sleep(0.04)

# --- MAIN APP LOGIC ---

# 1. Title and Header
st.markdown("<h1>Legal AI Predictor <span style='font-size:0.8em; color:gray;'>Beta</span></h1>", unsafe_allow_html=True)
st.markdown("---")


# 2. Connection Initialization (Display Status in Sidebar)
with st.sidebar:
    st.subheader("⚙️ System Status")
    client = init_connection()

    if client is not None:
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        st.success("MongoDB: Connected")
    else:
        db = None
        collection = None
        st.error("MongoDB: Disconnected (History will not be saved)")

    ml_model = load_ml_model()
    if ml_model is not None:
        st.success(f"ML Model: Loaded ({MODEL_FILE})")
    else:
        st.error(f"ML Model: Failed to Load. Predictions disabled.")
        
    st.markdown("---")
    st.info("💡 **Instructions:** Enter detailed facts of a case (e.g., 'Defendant was in violation of rule X and plaintiff showed documented losses.')")


# 3. Load and Initialize Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    
    # Load past history from DB if connection is active
    if collection is not None:
        try:
            db_messages = collection.find().sort("timestamp", pymongo.DESCENDING).limit(10)
            for msg in reversed(list(db_messages)): 
                st.session_state["messages"].append({"role": msg["role"], "content": msg["content"]})
        except Exception:
            pass # Ignore read errors, start fresh
    
    # If history is empty, add a welcoming message
    if not st.session_state["messages"]:
         st.session_state["messages"].append({"role": "assistant", "content": "Hello! I am your Legal AI. Please describe the core facts of your case for an instant prediction."})


# 4. Display Chat History
chat_container = st.container(height=500, border=False) # Fixed height container for modern chat feel

with chat_container:
    for message in st.session_state["messages"]:
        # Use custom avatars for a nicer look
        avatar = "🧑‍⚖️" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# 5. Handle User Input
prompt = st.chat_input("Enter the case facts here...")

if prompt:
    # a. Add user message to history and display
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    # Re-display the new user message immediately
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

    # b. Save user message to DB (Only if collection is active)
    if collection is not None:
        save_message_to_db(collection, "user", prompt)

    # c. Get prediction and stream response
    with chat_container:
        with st.chat_message("assistant", avatar="🧑‍⚖️"):
            # Placeholder for streaming
            placeholder = st.empty() 

            if ml_model is not None:
                # 1. Get Prediction
                prediction, explanation = predict_and_explain(ml_model, prompt)
                
                # 2. Format content
                header = f"### ⚖️ Predicted Outcome: `{prediction}`\n"
                explanation_section = f"**🔎 Model Rationale:** {explanation}\n\n"
                response_content = header + explanation_section

                # 3. Stream the content
                full_response = ""
                for chunk in stream_response(response_content):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌") # '▌' simulates a typing cursor
                
                # Final response cleanup
                placeholder.markdown(full_response)
                
            else:
                placeholder.markdown("⚠️ **System Error:** Cannot generate prediction. ML Model failed to load.")

            # d. Save assistant message to history and DB
            st.session_state["messages"].append({"role": "assistant", "content": full_response})
            if collection is not None:
                save_message_to_db(collection, "assistant", full_response, prediction=prediction if 'prediction' in locals() else "Error")

# --- Footer/Deployment Notes ---
st.sidebar.markdown("---")
st.sidebar.caption("App powered by Streamlit, PyMongo, and scikit-learn.")