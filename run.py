import os
import sys

# Ensure environment safety
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["LOKY_MAX_CPU_COUNT"] = "4"
os.environ["PYTHONIOENCODING"] = "utf-8"

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    
    print("=" * 70)
    print(" [ONLINE] INTELLIGENT CUSTOMER COMPLAINT ROUTING & AI REPLY SYSTEM")
    print("=" * 70)
    print(f" Web Dashboard: http://{host}:{port}")
    print(f" API Documentation (Swagger UI): http://{host}:{port}/docs")
    print(f" Interactive ReDoc: http://{host}:{port}/redoc")
    print("=" * 70)
    
    uvicorn.run("backend.main:app", host=host, port=port, reload=False)
