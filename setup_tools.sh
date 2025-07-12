#!/bin/bash

echo "Setting up SQL Analysis Tools..."

# Install SQLFluff
echo "Installing SQLFluff..."
pip install sqlfluff

# Install Semgrep
echo "Installing Semgrep..."
pip install semgrep

# Install SQLCheck (if available)
echo "Installing SQLCheck..."
pip install sqlcheck

# Alternative: Install SQLCheck from source if pip version not available
if ! command -v sqlcheck &> /dev/null; then
    echo "SQLCheck not found in pip, trying alternative installation..."
    # You might need to install from source or use a different package
    echo "Note: SQLCheck might need manual installation from source"
fi

# Verify installations
echo "Verifying installations..."

if command -v sqlfluff &> /dev/null; then
    echo "✅ SQLFluff installed successfully"
    sqlfluff --version
else
    echo "❌ SQLFluff installation failed"
fi

if command -v semgrep &> /dev/null; then
    echo "✅ Semgrep installed successfully"
    semgrep --version
else
    echo "❌ Semgrep installation failed"
fi

if command -v sqlcheck &> /dev/null; then
    echo "✅ SQLCheck installed successfully"
    sqlcheck --help
else
    echo "⚠️  SQLCheck not found - will use fallback analysis"
fi

echo "Setup complete!" 