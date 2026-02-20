#!/bin/bash
# StudyHub Setup Script
# Run this script to set up the complete environment

echo "========================================="
echo "  StudyHub Setup Script"
echo "========================================="
echo ""

# Step 1: Create virtual environment
echo "Step 1: Creating virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""

# Step 2: Activate virtual environment
echo "Step 2: Activating virtual environment..."
echo "Run: source venv/bin/activate (Linux/Mac)"
echo "Run: venv\\Scripts\\activate (Windows)"
echo ""

# Step 3: Install dependencies
echo "Step 3: Installing dependencies..."
echo "After activating venv, run: pip install -r requirements.txt"
echo ""

# Step 4: Initialize database
echo "Step 4: Initialize the database..."
echo "Run: python -c \"from app import create_app; app = create_app(); app.app_context().push(); from app.extensions import db; db.create_all()\""
echo "Or simply run the app once: python run.py"
echo ""

# Step 5: Run the application
echo "Step 5: Start the application..."
echo "Run: python run.py"
echo "Visit: http://localhost:5000"
echo ""

echo "========================================="
echo "  Alternative: Quick Test"
echo "========================================="
echo ""
echo "To test immediately (if packages installed):"
echo "  python3 run.py"
echo ""
echo "For production deployment:"
echo "  gunicorn run:app"
echo ""
echo "========================================="
