#!/bin/bash
# PyPI Publication Script
# Run this after setting up your .pypirc file

set -e  # Exit on error

echo "============================================================"
echo "PyPI Publication Script for ecommerce-ux-guidelines v1.0.0"
echo "============================================================"
echo ""

# Check if .pypirc exists
if [ ! -f ~/.pypirc ]; then
    echo "❌ ERROR: ~/.pypirc not found"
    echo ""
    echo "Please create ~/.pypirc using the template:"
    echo "  cp .pypirc.template ~/.pypirc"
    echo "  # Edit ~/.pypirc and add your API tokens"
    echo ""
    exit 1
fi

# Check if distribution files exist
if [ ! -f dist/ecommerce_ux_guidelines-1.0.0-py3-none-any.whl ]; then
    echo "❌ ERROR: Distribution files not found"
    echo "Run: python3 -m build"
    exit 1
fi

echo "✅ Distribution files found:"
ls -lh dist/
echo ""

# Validate with twine
echo "🔍 Validating package with twine..."
python3 -m twine check dist/*
if [ $? -ne 0 ]; then
    echo "❌ Validation failed"
    exit 1
fi
echo "✅ Validation passed"
echo ""

# Ask user which repository
echo "Choose upload destination:"
echo "  1) Test PyPI (recommended first)"
echo "  2) Production PyPI"
echo "  3) Both (Test PyPI first, then Production)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "📤 Uploading to Test PyPI..."
        python3 -m twine upload --repository testpypi dist/*

        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Upload to Test PyPI successful!"
            echo ""
            echo "Test installation with:"
            echo "  pip install --index-url https://test.pypi.org/simple/ ecommerce-ux-guidelines"
        fi
        ;;
    2)
        echo ""
        read -p "⚠️  Upload to PRODUCTION PyPI? This cannot be undone! (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo ""
            echo "📤 Uploading to Production PyPI..."
            python3 -m twine upload dist/*

            if [ $? -eq 0 ]; then
                echo ""
                echo "✅ Upload to Production PyPI successful!"
                echo ""
                echo "🎉 Package published! Install with:"
                echo "  pip install ecommerce-ux-guidelines"
                echo ""
                echo "View on PyPI: https://pypi.org/project/ecommerce-ux-guidelines/"
            fi
        else
            echo "Upload cancelled"
        fi
        ;;
    3)
        # Upload to Test PyPI first
        echo ""
        echo "📤 Step 1: Uploading to Test PyPI..."
        python3 -m twine upload --repository testpypi dist/*

        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Upload to Test PyPI successful!"
            echo ""
            echo "Please test the installation:"
            echo "  pip install --index-url https://test.pypi.org/simple/ ecommerce-ux-guidelines"
            echo ""
            read -p "Press ENTER after testing to continue with Production upload..."

            # Upload to Production PyPI
            echo ""
            read -p "⚠️  Upload to PRODUCTION PyPI? This cannot be undone! (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                echo ""
                echo "📤 Step 2: Uploading to Production PyPI..."
                python3 -m twine upload dist/*

                if [ $? -eq 0 ]; then
                    echo ""
                    echo "✅ Upload to Production PyPI successful!"
                    echo ""
                    echo "🎉 Package published! Install with:"
                    echo "  pip install ecommerce-ux-guidelines"
                    echo ""
                    echo "View on PyPI: https://pypi.org/project/ecommerce-ux-guidelines/"
                fi
            else
                echo "Production upload cancelled"
            fi
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "============================================================"
echo "Done!"
echo "============================================================"
