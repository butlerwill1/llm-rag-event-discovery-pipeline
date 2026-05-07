# Summary: Backward-compatible root entrypoint for the RAG query utility.

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from llm_rag_event_discovery_pipeline.rag_query import main


if __name__ == "__main__":
    main()

