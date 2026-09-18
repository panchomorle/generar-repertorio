# 02: Local Settings Persistence Module

**What to build:** A local settings management component that stores and retrieves the user's Repertoire generation preferences (column layout choice and chord color) from disk in `.cache_cifras/settings.json`. The module loads persisted preferences on application startup, writes updates when settings change, and transparently provides safe defaults (2 columns, orange `#E65100`) if the file does not exist, cannot be read, or contains invalid data.

**Blocked by:** None (can start immediately).

**Status:** ready-for-agent

- [x] Loading settings when `.cache_cifras/settings.json` does not exist creates or returns default values (2 columns, `#E65100`).
- [x] Saving settings persists the chosen column count (1 or 2) and chord color hex string cleanly to disk.
- [x] Persisted settings are accurately reloaded in subsequent calls or application sessions.
- [x] Corrupt, malformed, or partial JSON files are handled gracefully without raising unhandled exceptions, safely falling back to defaults.
- [x] Automated unit tests verify loading, saving, corruption recovery, and default values.

