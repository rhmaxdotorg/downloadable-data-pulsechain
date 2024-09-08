:: Chocolatey script to install dependencies for the Python scripts

@echo off
setlocal enabledelayedexpansion

echo Starting installation of dependencies...

:: Check if running with administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges.
) else (
    echo This script requires administrator privileges.
    echo Please run this script as an administrator.
    pause
    exit /b 1
)

:: Check if Chocolatey is installed, install if not
where choco >nul 2>&1
if %errorLevel% neq 0 (
    echo Chocolatey is not installed. Installing Chocolatey...
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
) else (
    echo Chocolatey is already installed.
)

:: Refresh environment variables
call refreshenv

:: Install Python
echo Installing Python 3.x...
choco install python -y --params "/AddToPath:1"

:: Refresh environment variables again
call refreshenv

:: Verify Python installation
echo Verifying Python installation...
python --version
if %errorLevel% neq 0 (
    echo Python installation failed or PATH is not set correctly.
    echo Please try running the script again or manually add Python to your PATH.
    pause
    exit /b 1
)

:: Install pip packages
echo Installing required Python packages...
python -m pip install --upgrade pip
pip install requests tqdm beautifulsoup4 matplotlib numpy playwright

:: Install Playwright browsers
echo Installing Playwright browsers...
python -m playwright install

:: Check if Google Chrome is installed, install if not
where chrome >nul 2>&1
if %errorLevel% neq 0 (
    echo Google Chrome is not installed. Installing Google Chrome...
    choco install googlechrome -y
) else (
    echo Google Chrome is already installed.
)

:: Add Python Scripts folder to PATH
echo Adding Python Scripts folder to PATH...
setx PATH "%PATH%;%USERPROFILE%\AppData\Local\Programs\Python\Python3x\Scripts" /M
if %errorLevel% neq 0 (
    echo Failed to add Python Scripts folder to PATH.
    echo You may need to add it manually: %USERPROFILE%\AppData\Local\Programs\Python\Python3x\Scripts
)

echo Installation complete! Python and all required dependencies have been installed.
echo You should now be able to run Python scripts from any new command prompt window.
echo If you encounter any issues, try restarting your computer to ensure all PATH changes take effect.
pause
