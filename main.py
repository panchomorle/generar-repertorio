import sys
from pathlib import Path

# Add src to pythonpath
sys.path.insert(0, str(Path(__file__).parent / "src"))

from repertorio.cli import main

if __name__ == "__main__":
    main()
