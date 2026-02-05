'''
Loading Flipkart reviews data from MongoDB into Python for transformation
and loading the cleaned data into MySQL.
'''

import pymongo
import pandas as pd
import os
import re
from datetime import datetime

# -----------------------------
# Connect to MongoDB
# -----------------------------
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["flipkart"]
collection = db["flipkart_review"]

# Retrieve all documents from MongoDB
data = list(collection.find())

# Convert MongoDB documents to pandas DataFrame
df = pd.DataFrame(data)

# Preview data
print(df.head())

# Save raw MongoDB data to CSV (optional backup)
df.to_csv("output_file.csv", index=False)

# -----------------------------
# Text preprocessing libraries
# -----------------------------
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK resources
nltk.download("stopwords")
nltk.download("punkt")
nltk.download("wordnet")

# -----------------------------
# Preprocess review_text column
# -----------------------------
def preprocess_review(text):
    if pd.isna(text):
        return text

    # Convert text to lowercase
    text = text.lower()

    # Remove "read more" text
    text = re.sub(r"\s*(read\s*more)[^\w]*$", "", text, flags=re.IGNORECASE)

    # Remove emoticons
    text = re.sub(r"[:;=8][\-o\*\']?[\)\]\(\[dDpP/\\:\}\{@\|]+", "", text)

    # Remove punctuation
    text = re.sub(r"[^\w\s]", "", text)

    # Tokenize text
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    tokens = [word for word in tokens if word not in stop_words]

    # Join tokens back into a string
    cleaned_text = " ".join(tokens)
    return cleaned_text

# Apply preprocessing
df["processed_review"] = df["review_text"].apply(preprocess_review)

# -----------------------------
# Process location column
# -----------------------------
def split_location(location_str):
    if pd.isna(location_str):
        return pd.Series([pd.NA, pd.NA])

    parts = [part.strip() for part in location_str.split(",")]

    if len(parts) >= 2:
        return pd.Series([parts[0], parts[1]])
    else:
        return pd.Series([parts[0], pd.NA])

df[["buyer_status", "location_clean"]] = df["location"].apply(split_location)

# -----------------------------
# Process date column
# -----------------------------
def process_date(date_val):
    try:
        parsed_date = pd.to_datetime(date_val, errors="coerce")
        if pd.isna(parsed_date):
            return datetime.now()
        return datetime.now()
    except Exception:
        return datetime.now()

df["processed_date"] = df["date"].apply(process_date)

# Preview transformed data
print(df.head())

# Drop unused columns
df.drop(columns=["_id", "review_text", "location", "date"], inplace=True)

print("Final columns:", df.columns.tolist())

# -----------------------------
# Load transformed data into MySQL
# -----------------------------
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://{user}:{pw}@localhost/{db}".format(
        user="your_mysql_user",
        pw="your_mysql_password",
        db="reviews_db"
    )
)

# Load data into MySQL table
df.to_sql(
    "flipkart_reviews_transformed",
    con=engine,
    if_exists="replace",
    chunksize=100,
    index=False
)

print("Transformed data successfully loaded into MySQL database.")
