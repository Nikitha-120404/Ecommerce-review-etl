# Project: E-Commerce Reviews ETL (Flipkart → MongoDB → CSV)
# Task: Extract (Scrape) reviews from Flipkart and Load into MongoDB
# Store data in MongoDB and save output as CSV

import requests                 # to send HTTP requests
from bs4 import BeautifulSoup as bs  # to parse HTML content
import csv                      # to write data into CSV file
import time                     # to add delay between page requests
from pymongo import MongoClient # to connect to MongoDB
import os                       # to handle file paths and folders

# Flipkart product reviews URL
base_review_url = "https://www.flipkart.com/samsung-galaxy-s24-ultra-5g-titanium-gray-256-gb/product-reviews/itm12ef5ea0212ed?pid=MOBGX2F3RQKKKTAW&lid=LSTMOBGX2F3RQKKKTAWNDZUYP&marketplace=FLIPKART"

# Fetch the first page to find total number of review pages
response = requests.get(base_review_url)
response.encoding = "utf-8"
soup = bs(response.text, "html.parser")

# Extract total number of pages
try:
    total_pages_tag = soup.find("div", {"class": "_1G0WLw mpIySA"}).find("span")
    total_pages = int(total_pages_tag.get_text(strip=True).split()[-1]) if total_pages_tag else 1
except Exception as e:
    print(f"Error extracting total pages: {e}")
    total_pages = 1

# List to store all reviews
all_reviews = []

# Loop through each review page
for page in range(1, total_pages + 1):
    print(f"Fetching reviews from page {page}/{total_pages}...")
    page_url = f"{base_review_url}&page={page}"

    try:
        page_response = requests.get(page_url)
        page_response.encoding = "utf-8"
        page_soup = bs(page_response.text, "html.parser")

        # Find all review containers
        review_boxes = page_soup.find_all("div", {"class": "col EPCmJX Ma1fCG"})

        # Extract data from each review
        for box in review_boxes:
            try:
                rating = box.find("div", {"class": "XQDdHH Ga3i8K"})
                title = box.find("p", {"class": "z9E0IG"})
                review_text = box.find("div", {"class": "ZmyHeo"})
                reviewer_name = box.find("p", {"class": "_2NsDsF AwS1CA"})
                location = box.find("p", {"class": "MztJPv"})
                date = box.find_all("p", {"class": "_2NsDsF"})[-1]

                all_reviews.append({
                    "rating": rating.get_text(strip=True) if rating else "N/A",
                    "title": title.get_text(strip=True) if title else "N/A",
                    "review_text": review_text.get_text(strip=True) if review_text else "N/A",
                    "reviewer_name": reviewer_name.get_text(strip=True) if reviewer_name else "N/A",
                    "location": location.get_text(strip=True) if location else "N/A",
                    "date": date.get_text(strip=True) if date else "N/A"
                })

            except Exception as e:
                print(f"Error processing a review: {e}")

        # Delay to avoid sending too many requests quickly
        time.sleep(1)

    except Exception as e:
        print(f"Error fetching page {page}: {e}")

# Create outputs folder if it does not exist
os.makedirs("outputs", exist_ok=True)

# Save reviews to CSV file
csv_path = "outputs/flip_review.csv"
with open(csv_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["rating", "title", "review_text", "reviewer_name", "location", "date"]
    )
    writer.writeheader()
    writer.writerows(all_reviews)

print(f"Reviews saved to {csv_path}")

# Upload reviews to MongoDB
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["flipkart"]
    collection = db["flipkart_review"]
    collection.insert_many(all_reviews)
    print(f"Inserted {len(all_reviews)} reviews into MongoDB")
except Exception as e:
    print(f"Error uploading to MongoDB: {e}")
