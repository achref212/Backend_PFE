from app.sql_agent.sql_generator import client


def summarize_result(result, question):
    context = str(result)
    prompt = f"""
Voici des résultats SQL : {context}
Explique-les simplement à un élève en réponse à : "{question}"
"""
    res = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return res.choices[0].message.content.strip()