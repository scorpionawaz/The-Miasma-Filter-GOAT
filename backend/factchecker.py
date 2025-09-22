import re
import json
from google import genai
from google.genai import types
def checkfact(claim):
    client = genai.Client(
        api_key="AIzaSyDAS7l4ju1cDGx5BjIS3qgb7Cx0X5LwtdY",
    )
    model = "gemini-2.5-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=f"""SYS INSTRUCTION ::: YOU ARE A TRUE OR FALSE VALIDATOR, GOOGLE SEARCH ACROSS WEB AND RETURN WITH CONFIDENCE SCORE 0.0 - 0.9 (0.9 INDICATES HIGHLY TRUE). you dont talk anything you just return the fucntion call dont say anything just check all the claims rapidly.;; 
Claim: {claim}. ;;;
You can ONLY return the JSON containing true/false, confidence_score and a small statement(very very small only return the imp points and simple like only required to convery any messgae). 
Example: 
{{
  "is_true": true,
  "confidence_score": 0.9,
  "statement": "Paris is indeed the capital of France."
}};;  ONLY RETURN PURE JSON IN ANY CASE.""" ),
            ],
        ),
    ]
    tools = [types.Tool(googleSearch=types.GoogleSearch())]

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
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
        tools=tools,
        temperature=0.0,
    )

    chunk = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    response_text = chunk.text.strip()

    # --- Regex to capture JSON ---
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {"error": "Invalid JSON returned", "raw": response_text}
    else:
        return {"error": "No JSON found", "raw": response_text}



