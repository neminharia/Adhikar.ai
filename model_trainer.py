import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

MODEL_FILE = 'court_case_predictor.pkl'

def train_and_save_model():
    """
    Trains a simple text classification model and saves it.
    This simulates your existing ML model setup.
    """
    # --- MOCK DATA: Replace with your actual case data ---
    data = {
        'facts': [
            "The defendant was clearly in violation of section A and lacked any valid permit for the action.",
            "The court determined the evidence was circumstantial and legally insufficient for conviction.",
            "A clear breach of the written contract was demonstrated, with extensive documented financial losses.",
            "The defense successfully argued self-defense based on multiple independent eyewitness accounts.",
            "Lack of proper legal procedure by the state led to the dismissal of all charges.",
            "Overwhelming proof of negligence and failure to adhere to safety standards was presented."
        ],
        'outcome': ['Petitioner Wins', 'Respondent Wins', 'Petitioner Wins', 'Respondent Wins', 'Respondent Wins', 'Petitioner Wins']
    }
    df = pd.DataFrame(data)

    # Create a classification pipeline
    text_model = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=1000)),
        ('clf', MultinomialNB())
    ])

    # Train the model
    X_train, _, y_train, _ = train_test_split(df['facts'], df['outcome'], test_size=0.2, random_state=42)
    text_model.fit(X_train, y_train)

    # Save the trained model to a file
    joblib.dump(text_model, MODEL_FILE)
    print(f"✅ Model trained and saved as {MODEL_FILE}")
    print("Run this script first, then run 'streamlit run app.py'")

if __name__ == "__main__":
    train_and_save_model()