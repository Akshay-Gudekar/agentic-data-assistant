import requests
import json

def ask_ollama(prompt, model="llama3.2"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

if __name__ == "__main__":
    code_prompt = """Write Python pandas code to load a CSV file called 'data.csv' 
and print the average of a column called 'age'. 
Only output the code, no explanation."""
    
    code = ask_ollama(code_prompt, model="codellama")
    print(code)