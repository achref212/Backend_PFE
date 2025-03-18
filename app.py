from flask import Flask, request, jsonify
from indexing.query_vector_search import search

app = Flask(__name__)


@app.route('/query_rag', methods=['POST'])
def query_rag():
    content = request.json
    question = content.get("question")
    if not question:
        return jsonify({"error": "question manquante"}), 400

    results = search(question)
    return jsonify(results)



if __name__ == '__main__':
    app.run()
