# Social-Media-Data-Collection-and-Analysis
Full-stack data analysis pipeline designed to collect, classify, and visualize user-generated political content from Reddit and 4chan.

## 🛠️ Tech Stack
- **Python 3.12** - Core language used for development and testing
- **PostgreSQL v17** - Relational database system for data storage and management
- **SQL** - Used for querying and manipulating data in PostgreSQL
- **python-dotenv** - Python-dotenv reads key-value pairs from a .env file and set them as environment variables
- **Faktory** - Background job processing system used to manage asynchronous tasks and queues
- **Docker** - Containerization platform used to package and deploy the application with its dependencies for consistent environments

## 📊 Dashboard
- **JavaScript** - Used for building interactive and dynamic user interface components
- **Chart.js** – JavaScript library used to create responsive and customizable visualizations for post trends  
- **HTML5** – Provides the structural layout of the dashboard, including dropdowns and canvas elements  
- **Flask** – Lightweight Python web framework used to serve backend APIs and render dashboard views  

# Reddit
- Leveraged Reddit’s public API to scrape posts from a curated list of political and neutral subreddits (e.g., r/politics, r/PoliticalDiscussion, r/NeutralPolitics)
- Extracted post metadata including timestamp, subreddit, upvotes, and comment count to analyze posting trends over time
- Used the data to measure engagement volume, detect post surges, and correlate with external events

# 4chan
 Parsed archived threads from 4chan’s /pol/ board to study unfiltered political discourse
- Normalized thread structure and extracted individual posts along with timestamps and content
- Enabled cross-platform toxicity comparison using the Moderate Hatespeech API

# Toxicity Collection
- **Moderate Hatespeech API** – Retrieves a moderation score by analyzing a string of text and returning the predicted class (e.g., toxic, non-toxic) along with a confidence score  
  - [API Documentation](https://moderatehatespeech.com/docs/)

