# Contributing to GramSort

Thank you for your interest in contributing to GramSort!

## How Can I Contribute?

### Reporting Bugs
If you find an unhandled file format, an unexpected filename crash on your operating system, or metadata that fails to parse:
1. Check existing GitHub Issues first to ensure it has not already been reported.
2. Open a new issue with:
   - Your OS (Windows, macOS, or Linux)
   - The export format you received (HTML or JSON)
   - A sanitized snippet of the offending filename or metadata entry

### Suggesting Enhancements
Feature requests are welcome! Please open an issue outlining:
- The proposed capability (e.g., date-based subfolder grouping, GUI interface)
- Why it would benefit users archiving their media

### Code Contributions
1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Keep dependencies minimal: GramSort aims to remain a zero-dependency standard library tool where possible.
3. Add unit tests for any new sanitization or parsing logic in `tests/`.
4. Ensure the test suite passes before submitting:
   ```bash
   python -m unittest discover tests -v
   ```
5. Open a Pull Request with a clear description of your changes.
