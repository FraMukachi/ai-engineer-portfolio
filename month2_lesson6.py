from groq import Groq
import os
import json

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def ask_json(prompt):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a data extraction assistant. Always respond with valid JSON only. No explanation. No markdown. No code blocks."},
            {"role": "user", "content": prompt}
        ]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

# Example 1 — extract structured data from text
print("=== EXTRACT DATA FROM TEXT ===")
result = ask_json("""
Extract information from this text and return as JSON:
'Fra is a 28 year old Full Stack developer from South Africa. 
He knows Python, React, and Django. He is learning AI Engineering and Kubernetes.'

Return this structure:
{
  "name": "",
  "age": 0,
  "country": "",
  "current_skills": [],
  "learning": []
}
""")
print(json.dumps(result, indent=2))

# Example 2 — generate structured content
print("\n=== GENERATE STRUCTURED CONTENT ===")
result2 = ask_json("""
Generate a 30-day learning plan for someone learning Python.
Return as JSON with this structure:
{
  "title": "",
  "total_days": 30,
  "weeks": [
    {
      "week": 1,
      "focus": "",
      "topics": []
    }
  ]
}
Include 4 weeks. Keep topics list to 3 items per week.
""")
print(json.dumps(result2, indent=2))
