import sys
from pathlib import Path

# Add src to pythonpath when running from source code
if not getattr(sys, "frozen", False):
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

from repertorio.cli import main as cli_main
from repertorio.ui import run_app


def entrypoint() -> None:
    # If explicit CLI arguments or flags are passed, invoke CLI; otherwise launch GUI
    cli_flags = {"-i", "--input", "-o", "--output", "-c", "--cache-dir", "--cli", "-h", "--help"}
    if len(sys.argv) > 1 and any(arg in cli_flags for arg in sys.argv[1:]):
        cli_main()
    else:
        run_app()


if __name__ == "__main__":
    entrypoint()
