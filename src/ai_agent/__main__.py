# Summary: Package entrypoint for running the event discovery agent with `python -m ai_agent`.

import sys

from .main import interactive_mode, main


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()

