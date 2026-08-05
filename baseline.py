import requests
import pandas as pd
import re

def ask_ollama(prompt, model="llama3.2"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

def generate_code(question, df):
    prompt = f"""You are a data analyst. Given a pandas DataFrame called 'df' with columns: {list(df.columns)}

Write Python pandas code to answer this question: "{question}"

Rules:
- Assume 'df' already exists, do not reload it
- Store your final answer in a variable called 'result'
- Only output code, no explanation, no markdown fences

Code:"""
    code = ask_ollama(prompt, model="codellama")
    # strip markdown fences if the model adds them anyway
    code = re.sub(r"```python|```", "", code).strip()
    return code

def run_baseline(question, csv_path="data.csv"):
    df = pd.read_csv(csv_path)
    code = generate_code(question, df)
    print("--- Generated code ---")
    print(code)
    print("--- Executing ---")
    
    local_vars = {"df": df, "pd": pd}
    try:
        exec(code, {}, local_vars)
        print("--- Result ---")
        print(local_vars.get("result", "No 'result' variable was set"))
    except Exception as e:
        print(f"--- Execution failed ---\n{e}")

if __name__ == "__main__":
    run_baseline("Predict whether a 30 year old male in 2nd class would survive")