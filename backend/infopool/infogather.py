from .googlenews import get_google_news_json
from .googlenewslocation import get_google_news_json_location
from .youtubelivecheck import extract_youtube_live_streams
from .youtubelivechecklocation import extract_youtube_live_streams_location
import re
import json
from datetime import datetime
import time

def save_clean_json(raw_text, filename="cache.json", timestamp=False):
    """
    Extracts clean JSON from model output (removes ```json``` blocks)
    and saves it one directory above the current script.
    """
    # Remove markdown-style ```json ... ``` wrappers if present
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if match:
        clean_json_text = match.group(1)
    else:
        clean_json_text = raw_text.strip()
    
    # Optionally add timestamp to filename
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"cache_{timestamp_str}.json"

    # Build path to parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(parent_dir, filename)

    # Validate and save JSON
    try:
        parsed = json.loads(clean_json_text)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved clean JSON to {file_path}")
    except json.JSONDecodeError as e:
        print("❌ JSON decode error:", e)
        print("Raw content:\n", clean_json_text)
    """
    Extracts clean JSON from model output (removes ```json``` blocks)
    and saves it to a file.
    """
    # Remove markdown-style ```json ... ``` wrappers if present
    match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
    if match:
        clean_json_text = match.group(1)
    else:
        clean_json_text = raw_text.strip()
    
    # Optionally add timestamp to filename
    if timestamp:
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"cache_{timestamp_str}.json"

    # Validate and save JSON
    try:
        parsed = json.loads(clean_json_text)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved clean JSON to {filename}")
    except json.JSONDecodeError as e:
        print("❌ JSON decode error:", e)
        print("Raw content:\n", clean_json_text)




def fetch_all_data(location):
    
    #general news data
    news_data = get_google_news_json()
    youtube_data = extract_youtube_live_streams()
    
    news_data_location = get_google_news_json_location(location)
    youtube_data_location = extract_youtube_live_streams_location(location)
    
    combined_data = f"""
    General News Data and Live Channels Data in India := 
    1. News Data: {news_data};;
    2. YouTube Live Channels Data: {youtube_data};;;;
    ----------------------------------------------------
    
    News Data and Live Channels Data for {location} :=
    1. News Data: {news_data_location}  ;;
    2. YouTube Live Channels Data: {youtube_data_location};;;;
    
    End of the Data;;;;;
    
    """
    return combined_data

# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate(location):
    if not location:
        location = "Delhi"
    data = fetch_all_data(location)
    client = genai.Client(
        api_key="paste your API key here",
    )

    model = "gemini-2.5-pro"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text = f"""
You are a Trend Intelligence Agent that analyzes multi-source live data — including Google News (India, Regional, Global), YouTube Trending India, and Regional news headlines — to identify and summarize the most trending topics in India.

You will receive structured text or lists containing:
- Google News India headlines (highest priority)
- YouTube Trending India headlines and viewer counts (second priority)
- Region-specific Indian headlines (lower priority)
- (Optional) Global headlines that may influence Indian discussions

Your goal is to identify the **top 10–12 trending topics** across these sources with the following priority:
1. **Google News India** → Select the **top 5** most discussed or repeated national stories.
2. **YouTube Trending India** → Select **3–5** topics that are repeated or have massive live viewership (e.g., entertainment, politics, major incidents). Merge duplicates with Google News if overlapping.
3. **Regional or city-level headlines** → Select **2–3** topics that are significant locally or linked to above trends.
4. If the same story appears in multiple sources, merge it and increase the repetition count accordingly.

---
### Core Tasks
1. **Analyze all input data** to find recurring topics, high viewer counts, and high repetition across the above sources.
2. **Prioritize** topics following the source importance (Google News > YouTube India > Regional).
3. **Compute a trend probability (0–1)** based on repetition and viewership momentum.
4. For each topic, produce:
   - **Metadata Summary:** include repetition count, total viewers, trend probability, and a short reason for selection (e.g., “Top story in Google News India,” “Massively trending on YouTube,” “Repeated regional reports”).
   - **Detailed Facts:** short factual overview and 2–3 sub-headlines or verified related lines.
5. You may **perform Google Searches** to verify or enrich factual accuracy for the final topics.
6. All responses must be concise, factual, and relevant to India.
7. **Important:** Output strictly **only JSON** — do not include any extra text or commentary.

---
### JSON Output Format
{{
  "metadata_summary": [
    {{
      "topic": "string",
      "repeated_count": "integer",
      "total_viewers": "integer",
      "trend_probability": "float (0.0 - 1.0)",
      "reason_for_selection": "string (why this topic was chosen — e.g., top Google News India story, trending on YouTube, repeated across regional outlets)"
    }}
  ],
  "detailed_facts": [
    {{
      "topic": "string",
      "related_headlines": [
        "string (short headline 1)",
        "string (short headline 2)",
        "string (short headline 3)"
      ],
      "summary": "string (minimum 10 to 15 numbered sentence factual summary in neutral tone)"
    }}
  ]
}}

---
### Example Output
{{
  "metadata_summary": [
    {{
      "topic": "Delhi Air Quality Deteriorates",
      "repeated_count": 25,
      "total_viewers": 0,
      "trend_probability": 0.91,
      "reason_for_selection": "Top Google News India story with repeated coverage across 20+ headlines."
    }},
    {{
      "topic": "India vs Australia ODI highlights",
      "repeated_count": 14,
      "total_viewers": 5200000,
      "trend_probability": 0.88,
      "reason_for_selection": "Trending on YouTube India and widely discussed in Google News sports section."
    }},
    {{
      "topic": "Heavy rains flood Pune city",
      "repeated_count": 6,
      "total_viewers": 350000,
      "trend_probability": 0.64,
      "reason_for_selection": "Reported by multiple regional outlets; rising public attention."
    }}
  ],
  "detailed_facts": [
    {{
      "topic": "Delhi Air Quality Deteriorates",
      "related_headlines": [
        "Delhi's AQI crosses 450; schools shut for two days",
        "Smog covers NCR region; health experts issue warnings"
      ],
      "summary": "Delhi continues to face severe air pollution as AQI levels exceed 450. Authorities have advised residents to stay indoors and restricted construction activities."
    }}
  ]
}}

Return **only JSON** following the format above — no explanations or extra text.

Below is the actual data you need to analyze:
Return the Output in JSON format only:
{data}
-----
"""

),
            ],
        ),
    ]
    tools = [
        types.Tool(googleSearch=types.GoogleSearch(
        )),
    ]
    generate_content_config = types.GenerateContentConfig(
        #safety_settings are below
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.OFF,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ],
        temperature=0.1,
        tools=tools,
    )
    print("Generating content with Gemini 2.5 Flash model...")
    chunk = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    
    cache = chunk.text
    print(cache)
    save_clean_json(cache, timestamp=False)

