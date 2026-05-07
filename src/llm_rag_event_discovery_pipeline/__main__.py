# Summary: Package entrypoint for running the LLM RAG Event Discovery Pipeline with `python -m llm_rag_event_discovery_pipeline`.

import sys

from .main import interactive_mode, main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()

