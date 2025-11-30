#!/bin/bash
# Download Source Serif 4 fonts for EPUB generation
# These fonts are needed for proper EPUB rendering

set -e

echo "Downloading Source Serif 4 fonts..."

# Source Serif 4 Regular
if [ ! -f "SourceSerif4-Regular.ttf" ]; then
    echo "Downloading SourceSerif4-Regular.ttf..."
    curl -L -o SourceSerif4-Regular.ttf \
        "https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005R-regular.ttf"
fi

# Source Serif 4 Semibold
if [ ! -f "SourceSerif4-Semibold.ttf" ]; then
    echo "Downloading SourceSerif4-Semibold.ttf..."
    curl -L -o SourceSerif4-Semibold.ttf \
        "https://github.com/adobe-fonts/source-serif/releases/download/4.005R/source-serif-4.005R-semibold.ttf"
fi

echo "Font download complete."
echo "Verifying fonts..."

# Basic verification
for font in SourceSerif4-Regular.ttf SourceSerif4-Semibold.ttf; do
    if [ -f "$font" ] && [ -s "$font" ]; then
        echo "✓ $font downloaded successfully"
    else
        echo "✗ Failed to download $font"
        exit 1
    fi
done

echo "All fonts ready for EPUB generation."

