#!/bin/bash

# ╔══════════════════════════════════════════════════════════════╗
# ║         TrendsPro Clean Architecture Setup Script             ║
# ╚══════════════════════════════════════════════════════════════╝

set -e  # Exit on error

echo "🚀 TrendsPro Clean Architecture Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "ℹ️  $1"; }

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.8"

if [ $(echo "$python_version >= $required_version" | bc -l) -eq 1 ]; then
    print_success "Python $python_version is installed (>= $required_version required)"
else
    print_error "Python $python_version is too old. Please install Python >= $required_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate 2>/dev/null || {
    print_error "Failed to activate virtual environment"
    exit 1
}
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip -q
print_success "pip upgraded"

# Install requirements
print_info "Installing requirements (this may take a few minutes)..."
pip install -r requirements.txt -q
print_success "All requirements installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found"
    
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_success ".env file created from template"
        print_warning "Please edit .env and add your configuration:"
        echo "  - OPENAI_API_KEY"
        echo "  - DB_TRENDS_URL (MySQL connection)"
        echo "  - MONGO_LUDAFARMA_URL (MongoDB connection)"
    else
        print_error "No .env.example found. Please create a .env file with:"
        echo "OPENAI_API_KEY=your-key-here"
        echo "DB_TRENDS_URL=mysql://user:pass@host:port/database"
        echo "MONGO_LUDAFARMA_URL=mongodb://user:pass@host:port/database"
        echo "ARCHITECTURE_MODE=clean"
        exit 1
    fi
else
    print_success ".env file exists"
    
    # Update ARCHITECTURE_MODE to clean
    if grep -q "ARCHITECTURE_MODE=" .env; then
        sed -i.bak 's/ARCHITECTURE_MODE=.*/ARCHITECTURE_MODE=clean/' .env
        print_success "ARCHITECTURE_MODE set to 'clean'"
    else
        echo "ARCHITECTURE_MODE=clean" >> .env
        print_success "ARCHITECTURE_MODE added and set to 'clean'"
    fi
fi

# Create necessary directories if they don't exist
directories=("logs" "data" "cache" "uploads")
for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Created directory: $dir"
    fi
done

# Run validation
print_info "Running system validation..."
python scripts/validate_migration.py 2>/dev/null || {
    print_warning "Validation script not available or failed"
    print_info "You can run it manually later: python scripts/validate_migration.py"
}

echo ""
echo "======================================"
print_success "Setup completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your configuration (if needed)"
echo "2. Start the application:"
echo "   python start_clean.py"
echo ""
echo "Or manually:"
echo "   source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "   python start_clean.py"
echo ""
echo "📚 Documentation available at:"
echo "   http://localhost:8000/docs (after starting)"
echo ""
print_success "Ready to run in Clean Architecture mode! 🚀"
