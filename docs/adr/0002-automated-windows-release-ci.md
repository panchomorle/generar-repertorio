# Automated Windows Release CI with GitHub Actions

To deliver standalone Windows executables (.exe) reliably without manual packaging steps or local environment interference, we adopted a GitHub Actions CI workflow triggering on semantic version tags (`v*.*.*`). The workflow checks out the repository on a clean `windows-latest` runner, runs the test suite, bundles the application into a single-file executable using PyInstaller, and publishes a GitHub Release with the binary attached. A local build script is provided alongside for development smoke testing.
