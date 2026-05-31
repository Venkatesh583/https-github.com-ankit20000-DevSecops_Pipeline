@echo off
REM Healthcare Microservices Testing Script for Windows
REM Run all tests, integration tests, or specific service tests

setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "USER_SERVICE_DIR=%PROJECT_ROOT%user-service"
set "APPOINTMENT_SERVICE_DIR=%PROJECT_ROOT%appointment-service"
set "REPORT_SERVICE_DIR=%PROJECT_ROOT%report-service"

REM Default options
set "RUN_COVERAGE=false"
set "RUN_INTEGRATION=false"
set "RUN_UNIT=true"
set "VERBOSE=true"
set "SPECIFIC_SERVICE="

REM Parse arguments
:parse_args
if "%1"=="" goto args_done
if "%1"=="-a" goto all_tests
if "%1"=="--all" goto all_tests
if "%1"=="-u" goto unit_tests
if "%1"=="--unit" goto unit_tests
if "%1"=="-i" goto integration_tests
if "%1"=="--integration" goto integration_tests
if "%1"=="-c" goto coverage
if "%1"=="--coverage" goto coverage
if "%1"=="-s" goto service
if "%1"=="--service" goto service
if "%1"=="-h" goto help
if "%1"=="--help" goto help
goto invalid_arg

:all_tests
set "RUN_INTEGRATION=true"
set "RUN_UNIT=true"
shift
goto parse_args

:unit_tests
set "RUN_UNIT=true"
set "RUN_INTEGRATION=false"
shift
goto parse_args

:integration_tests
set "RUN_UNIT=false"
set "RUN_INTEGRATION=true"
shift
goto parse_args

:coverage
set "RUN_COVERAGE=true"
shift
goto parse_args

:service
set "SPECIFIC_SERVICE=%2"
shift
shift
goto parse_args

:invalid_arg
echo ERROR: Unknown option: %1
echo.
goto help

:help
echo Usage: run_tests.bat [OPTIONS]
echo.
echo Options:
echo   -a, --all            Run all tests (unit + integration)
echo   -u, --unit           Run only unit tests (default)
echo   -i, --integration    Run only integration tests
echo   -c, --coverage       Include coverage report
echo   -s, --service NAME   Run tests for specific service (user^|appointment^|report)
echo   -h, --help           Show this help message
echo.
echo Examples:
echo   run_tests.bat                      # Run all unit tests
echo   run_tests.bat --coverage           # Run with coverage report
echo   run_tests.bat --service user -c    # Run user service tests with coverage
echo   run_tests.bat --all                # Run all tests
echo.
exit /b 0

:args_done
REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pytest not found. Please install it with:
    echo pip install pytest pytest-cov pytest-mock
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

REM Run tests based on options
if not "!SPECIFIC_SERVICE!"=="" (
    call :run_service_tests
    exit /b !errorlevel!
) else (
    if "!RUN_UNIT!"=="true" (
        call :run_unit_tests
        if !errorlevel! neq 0 exit /b !errorlevel!
    )
    if "!RUN_INTEGRATION!"=="true" (
        call :run_integration_tests
        if !errorlevel! neq 0 exit /b !errorlevel!
    )
    if "!RUN_COVERAGE!"=="true" (
        call :run_coverage
        if !errorlevel! neq 0 exit /b !errorlevel!
    )
)

echo.
echo ✓ All tests completed successfully!
echo.
exit /b 0

:run_unit_tests
echo.
echo ========================================
echo Running Unit Tests
echo ========================================
echo.

echo.
echo Running User Service Tests...
cd /d "%USER_SERVICE_DIR%"
python -m pytest test_app.py -v --tb=short
if !errorlevel! neq 0 exit /b !errorlevel!
echo ✓ User service tests passed
echo.

echo Running Appointment Service Tests...
cd /d "%APPOINTMENT_SERVICE_DIR%"
python -m pytest test_app.py -v --tb=short
if !errorlevel! neq 0 exit /b !errorlevel!
echo ✓ Appointment service tests passed
echo.

echo Running Report Service Tests...
cd /d "%REPORT_SERVICE_DIR%"
python -m pytest test_app.py -v --tb=short
if !errorlevel! neq 0 exit /b !errorlevel!
echo ✓ Report service tests passed
echo.
exit /b 0

:run_integration_tests
echo.
echo ========================================
echo Running Integration Tests
echo ========================================
echo.

cd /d "%PROJECT_ROOT%"
python -m pytest test_integration.py -v --tb=short
if !errorlevel! neq 0 exit /b !errorlevel!
echo ✓ Integration tests passed
echo.
exit /b 0

:run_coverage
echo.
echo ========================================
echo Generating Coverage Report
echo ========================================
echo.

cd /d "%PROJECT_ROOT%"
python -m pytest -v --cov=. --cov-report=html --cov-report=term-missing
if !errorlevel! neq 0 exit /b !errorlevel!
echo ✓ Coverage report generated (htmlcov/index.html)
echo.
exit /b 0

:run_service_tests
if /i "!SPECIFIC_SERVICE!"=="user" (
    echo.
    echo ========================================
    echo Running User Service Tests
    echo ========================================
    echo.
    
    cd /d "%USER_SERVICE_DIR%"
    if "!RUN_COVERAGE!"=="true" (
        python -m pytest test_app.py -v --cov --cov-report=html
    ) else (
        python -m pytest test_app.py -v
    )
    if !errorlevel! neq 0 exit /b !errorlevel!
    echo ✓ User service tests completed
    exit /b 0
)

if /i "!SPECIFIC_SERVICE!"=="appointment" (
    echo.
    echo ========================================
    echo Running Appointment Service Tests
    echo ========================================
    echo.
    
    cd /d "%APPOINTMENT_SERVICE_DIR%"
    if "!RUN_COVERAGE!"=="true" (
        python -m pytest test_app.py -v --cov --cov-report=html
    ) else (
        python -m pytest test_app.py -v
    )
    if !errorlevel! neq 0 exit /b !errorlevel!
    echo ✓ Appointment service tests completed
    exit /b 0
)

if /i "!SPECIFIC_SERVICE!"=="report" (
    echo.
    echo ========================================
    echo Running Report Service Tests
    echo ========================================
    echo.
    
    cd /d "%REPORT_SERVICE_DIR%"
    if "!RUN_COVERAGE!"=="true" (
        python -m pytest test_app.py -v --cov --cov-report=html
    ) else (
        python -m pytest test_app.py -v
    )
    if !errorlevel! neq 0 exit /b !errorlevel!
    echo ✓ Report service tests completed
    exit /b 0
)

echo ERROR: Unknown service: !SPECIFIC_SERVICE!
echo Available services: user, appointment, report
exit /b 1
