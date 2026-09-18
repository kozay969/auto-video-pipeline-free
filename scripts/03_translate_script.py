import os
import google.generativeai as genai

def translate_script():
    input_path = "processed/transcript.txt"
    output_path = "processed/translated_script.txt"

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Gemini API Key ရယူခြင်း
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"Translate the following transcript into Burmese:\n\n{text}"
        response = model.generate_content(prompt)
        translated_text = response.text
    else:
        print("Warning: GEMINI_API_KEY not found. Skipping translation.")
        translated_text = text

    os.makedirs("processed", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(translated_text)

    print(f"Saved translated script to {output_path}")

if __name__ == "__main__":
    translate_script()
  
