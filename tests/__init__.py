import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVICE_SRC = PROJECT_ROOT / "services" / "tts-gateway" / "src"

if str(SERVICE_SRC) not in sys.path:
    sys.path.insert(0, str(SERVICE_SRC))
