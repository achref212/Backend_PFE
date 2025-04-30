import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("TOGETHER_API_KEY")
print("🟢 API KEY =", api_key if api_key else "❌ NON TROUVÉE")