#!/bin/bash

# Healthcare Microservices Testing Script
# Run all tests, integration tests, or specific service tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_SERVICE_DIR="$PROJECT_ROOT/user-service"
APPOINTMENT_SERVICE_DIR="$PROJECT_ROOT/appointment-service"
REPORT_SERVICE_DIR="$PROJECT_ROOT/report-service"

# Default options
RUN_COVERAGE=false
RUN_INTEGRATION=false
RUN_UNIT=true
VERBOSE=true

# Functions
print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

show_usage() {
    echo "Usage: ./run_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --all            Run all tests (unit + integration)"
    echo "  -u, --unit           Run only unit tests (default)"
    echo "  -i, --integration    Run only integration tests"
    echo "  -c, --coverage       Include coverage report"
    echo "  -s, --service NAME   Run tests for specific service (user|appointment|report)"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh                      # Run all unit tests"
    echo "  ./run_tests.sh --coverage           # Run with coverage report"
    echo "  ./run_tests.sh --service user -c    # Run user service tests with coverage"
    echo "  ./run_tests.sh --all                # Run all tests"
}

# Parse arguments
SPECIFIC_SERVICE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            RUN_INTEGRATION=true
            RUN_UNIT=true
            shift
            ;;
        -u|--unit)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            shift
            ;;
        -i|--integration)
            RUN_UNIT=false
            RUN_INTEGRATION=true
            shift
            ;;
        -c|--coverage)
            RUN_COVERAGE=true
            shift
            ;;
        -s|--service)
            SPECIFIC_SERVICE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Please install it with: pip install pytest pytest-cov pytest-mock"
    exit 1
fi

cd "$PROJECT_ROOT"

# Run tests based on options
if [ -n "$SPECIFIC_SERVICE" ]; then
    case $SPECIFIC_SERVICE in
        user)
            print_header "Running User Service Tests"
            cd "$USER_SERVICE_DIR"
            if [ "$RUN_COVERAGE" = true ]; then
                pytest test_app.py -v --cov --cov-report=html
            else
                pytest test_app.py -v
            fi
            print_success "User service tests completed"
            ;;
        appointment)
            print_header "Running Appointment Service Tests"
            cd "$APPOINTMENT_SERVICE_DIR"
            if [ "$RUN_COVERAGE" = true ]; then
                pytest test_app.py -v --cov --cov-report=html
            else
                pytest test_app.py -v
            fi
            print_success "Appointment service tests completed"
            ;;
        report)
            print_header "Running Report Service Tests"
            cd "$REPORT_SERVICE_DIR"
            if [ "$RUN_COVERAGE" = true ]; then
                pytest test_app.py -v --cov --cov-report=html
            else
                pytest test_app.py -v
            fi
            print_success "Report service tests completed"
            ;;
        *)
            print_error "Unknown service: $SPECIFIC_SERVICE"
            echo "Available services: user, appointment, report"
            exit 1
            ;;
    esac
else
    # Run all services' tests
    if [ "$RUN_UNIT" = true ]; then
        print_header "Running Unit Tests"
        
        print_header "User Service Tests"
        cd "$USER_SERVICE_DIR"
        pytest test_app.py -v --tb=short
        print_success "User service tests passed"
        
        print_header "Appointment Service Tests"
        cd "$APPOINTMENT_SERVICE_DIR"
        pytest test_app.py -v --tb=short
        print_success "Appointment service tests passed"
        
        print_header "Report Service Tests"
        cd "$REPORT_SERVICE_DIR"
        pytest test_app.py -v --tb=short
        print_success "Report service tests passed"
    fi
    
    if [ "$RUN_INTEGRATION" = true ]; then
        print_header "Running Integration Tests"
        cd "$PROJECT_ROOT"
        pytest test_integration.py -v --tb=short
        print_success "Integration tests passed"
    fi
    
    if [ "$RUN_COVERAGE" = true ]; then
        print_header "Generating Coverage Report"
        cd "$PROJECT_ROOT"
        pytest -v --cov=. --cov-report=html --cov-report=term-missing
        print_success "Coverage report generated (htmlcov/index.html)"
    fi
fi

print_success "All tests completed successfully!"
echo ""
