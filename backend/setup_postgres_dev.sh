#!/bin/bash
# ============================================================================
# PostgreSQL Development Setup Script
# ============================================================================
#
# This script sets up PostgreSQL for local development of the Feedback API.
# 
# Prerequisites:
# - PostgreSQL 12+ installed and running
# - psql command available in PATH
#
# Usage:
#   bash setup_postgres_dev.sh
#
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "PostgreSQL Development Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_HOST="localhost"
POSTGRES_PORT="5432"
APP_DB="feedbackdb"
APP_USER="feedbackuser"
APP_PASSWORD="feedbackpass"

# Function to print colored output
print_info() {
    echo -e "${BLUE}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if PostgreSQL is running
print_info "Checking if PostgreSQL is running..."
if ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT > /dev/null 2>&1; then
    print_error "PostgreSQL is not running on $POSTGRES_HOST:$POSTGRES_PORT"
    echo "Please start PostgreSQL and try again."
    echo ""
    echo "macOS (Homebrew): brew services start postgresql"
    echo "Linux (systemd): sudo systemctl start postgresql"
    echo "Docker: docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15"
    exit 1
fi
print_success "PostgreSQL is running"

# Create database
print_info "Creating database '$APP_DB'..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -tc "SELECT 1 FROM pg_database WHERE datname = '$APP_DB';" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "CREATE DATABASE $APP_DB;"
print_success "Database '$APP_DB' is ready"

# Create application user (optional, for production-like setup)
print_info "Creating application user '$APP_USER' (optional)..."
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -tc "SELECT 1 FROM pg_user WHERE usename = '$APP_USER';" | grep -q 1 || \
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "CREATE USER $APP_USER WITH PASSWORD '$APP_PASSWORD';"

# Grant privileges to application user
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -c "GRANT ALL PRIVILEGES ON DATABASE $APP_DB TO $APP_USER;"
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -p $POSTGRES_PORT -d $APP_DB -c "GRANT ALL ON SCHEMA public TO $APP_USER;"
print_success "User '$APP_USER' created and granted privileges"

echo ""
echo "=========================================="
echo "✓ PostgreSQL Setup Complete!"
echo "=========================================="
echo ""
echo "Connection Details:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $APP_DB"
echo "  User (admin): $POSTGRES_USER"
echo "  User (app): $APP_USER"
echo ""
echo "Updated .env file:"
echo "  DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$APP_DB"
echo ""
echo "Or use application user:"
echo "  DATABASE_URL=postgresql://$APP_USER:$APP_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$APP_DB"
echo ""
echo "Next steps:"
echo "  1. Copy .env_postgres to .env:"
echo "     cp .env_postgres .env"
echo "  2. Install dependencies:"
echo "     pip install -r requirements.txt"
echo "  3. Start the backend:"
echo "     uvicorn app:app --reload"
echo ""
