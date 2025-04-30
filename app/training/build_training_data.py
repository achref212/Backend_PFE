import json

from app.sql_agent.agent_runner import run_sql_agent

EXAMPLES = [
    "Quels sont les débouchés après un BUT informatique ?",
    "Combien coûte une licence en communication à Paris ?",
    "Quelles formations en STMG à Toulouse ?"
]

dataset = []

for prompt in EXAMPLES:
    response = run_sql_agent(prompt)
    dataset.append({
        "instruction": prompt,
        "input": f"SQL : {response['sql_query']}\nRésultat : {response['raw_result']}",
        "output": response["summary"]
    })

with open("training/dataset_postbac.jsonl", "w") as f:
    for line in dataset:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")

print("✅ Dataset généré.")