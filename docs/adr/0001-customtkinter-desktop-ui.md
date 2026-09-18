# CustomTkinter for Desktop GUI

To distribute a standalone Windows executable (.exe) without requiring external browser runtimes or heavy C++ bindings, we chose CustomTkinter paired with PyInstaller over PyQt6 and PyWebView. This provides a modern dark/light UI on top of Python's standard Tkinter while keeping binary size under 30MB with near-instant cold startup.
