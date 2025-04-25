import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    uvicorn.run(
        "market_sim.api.app:app",
        host=os.getenv("API_HOST"),
        port=int(os.getenv("API_PORT")),
        reload=True
    )