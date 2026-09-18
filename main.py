import sys
from pathlib import Path

# Add src to pythonpath
sys.path.insert(0, str(Path(__file__).parent / "src"))

if __name__ == "__main__":
    # If explicit CLI arguments or flags are passed, invoke CLI; otherwise launch GUI
    cli_flags = {"-i", "--input", "-o", "--output", "-c", "--cache-dir", "--cli", "-h", "--help"}
    if len(sys.argv) > 1 and any(arg in cli_flags for arg in sys.argv[1:]):
        from repertorio.cli import main as cli_main
        cli_main()
    else:
        from repertorio.ui import run_app
        run_app()
