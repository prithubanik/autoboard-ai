import sys
import ollama

# Force UTF-8 encoding for Windows terminal output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def test_ollama():
    print("[+] Connecting to Ollama (gemma4:31b)...")
    
    prompt = "Hallo! Du bist mein deutscher Sprachlehrer. Begrüße mich kurz auf Deutsch und frage, wie mein Tag war."

    try:
        response = ollama.chat(
            model="gemma4:31b-cloud",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        print("\n--- Ollama Response ---")
        print(response['message']['content'])
        print("-----------------------")
        print("SUCCESS! Gemma 4 is working correctly.")

    except Exception as e:
        print(f"\n[-] Connection Error: {e}")
        print("Tip: Make sure the Ollama desktop application is running in the background!")

if __name__ == "__main__":
    test_ollama()