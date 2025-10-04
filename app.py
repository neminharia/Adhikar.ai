import streamlit as st
import pymongo
from pymongo.errors import ConnectionFailure
import joblib
import os
from datetime import datetime

# --- CONFIGURATION ---
DATABASE_NAME = "court_chat_db"
COLLECTION_NAME = "chat_messages"
MODEL_FILE = 'court_case_predictor.pkl'

# --- HELPER FUNCTIONS (Model and Database) ---

@st.cache_resource
def init_connection():
    """
    Initializes and caches the MongoDB client connection.
    Crucially, it contains NO Streamlit UI calls (st.xyz) to avoid CacheReplayClosureError.
    """
    # 1. Securely fetch the URI from secrets.toml (or provide a local fallback)
    # The structure st.secrets.get("mongo", {}).get("uri") assumes the key is [mongo] in secrets.toml
    MONGO_URI = st.secrets.get("mongo", {}).get("uri") 
    
    if not MONGO_URI:
        # Fallback for local development if secrets are not configured
        MONGO_URI = "mongodb://localhost:27017/" 
        
    client = None  # Ensure 'client' is defined in the function scope

    try:
        # Attempt connection
        client = pymongo.MongoClient(MONGO_URI)
        client.admin.command('ping') 
        return client
        
    except ConnectionFailure as e:
        # Use print() for internal logging since st.error() is not allowed here
        print(f"❌ MongoDB Connection Failed: {e}")
        return None
        
    except Exception as e:
        # Catch other errors (like bad URI formatting)
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
        
    prediction = model.predict([case_facts])[0]

    # Simple Explanation Logic
    if 'Petitioner Wins' in prediction:
        explanation = (
            "The model detected features highly correlated with success for the petitioner, "
            "such as terms related to **'violation,'** **'breach of contract,'** or **'overwhelming proof.'** "
        )
    else:
        explanation = (
            "The prediction leans towards the respondent, likely due to language associated with "
            "**'insufficient evidence,'** **'self-defense,'** or **'procedural error,'** which often leads to dismissal."
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
        st.warning(f"Could not save message to DB. (Check permissions/network) Error: {e}")


# --- STREAMLIT APP LOGIC ---

st.title("⚖️ Legal Case Outcome Predictor Chatbot")
st.caption("Full-Stack ML App with Streamlit and MongoDB")

# 1. Initialize Connections and Database Objects
client = init_connection()

# Determine DB/Collection objects based on successful client connection
if client is not None:
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    st.toast("✅ Connected to MongoDB!") # UI element moved here
else:
    db = None
    collection = None
    st.error("❌ MongoDB Connection Failed. Chat history is disabled.") # UI element moved here

ml_model = load_ml_model()
if ml_model is None:
     st.warning(f"⚠️ Prediction model ({MODEL_FILE}) not loaded. Predictions will be disabled.")


# 2. Load and Initialize Chat History
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    
    # Load past history from DB if connection is active
    if collection is not None:
        try:
            # Load last 5 messages
            db_messages = collection.find().sort("timestamp", pymongo.DESCENDING).limit(5)
            for msg in reversed(list(db_messages)): 
                st.session_state["messages"].append({"role": msg["role"], "content": msg["content"]})
        except Exception:
            # This covers empty collection or unexpected DB read errors
            st.session_state["messages"].append({"role": "assistant", "content": "Welcome! Please describe the core facts of your court case for a predicted outcome and explanation."})
    else:
        # DB disconnected - use generic welcome message
        st.session_state["messages"].append({"role": "assistant", "content": "Welcome! (DB disconnected) Please describe the core facts of your court case."})


# 3. Display Chat History
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if prompt := st.chat_input("Enter the case facts here..."):
    # a. Add user message to history and display
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # b. Save user message to DB (Only if collection is active)
    if collection is not None:
        save_message_to_db(collection, "user", prompt)

    # c. Get prediction and explanation
    with st.spinner("Analyzing case facts..."):
        prediction, explanation = predict_and_explain(ml_model, prompt)

    # d. Format and display assistant response
    response_content = (
        f"**⚖️ Predicted Outcome:** `{prediction}`\n\n"
        f"**🔎 Model Explanation:** {explanation}"
    )

    st.session_state["messages"].append({"role": "assistant", "content": response_content})
    with st.chat_message("assistant"):
        st.markdown(response_content)

    # e. Save assistant message to DB (Only if collection is active)
    if collection is not None:
        save_message_to_db(collection, "assistant", response_content, prediction=prediction)