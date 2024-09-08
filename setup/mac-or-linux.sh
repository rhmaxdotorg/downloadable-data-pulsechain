#!/bin/bash
# Installs dependencies to run the python scripts on macOS or Linux

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Starting installation of dependencies..."

# Detect the operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"

    # Check for sudo access
    if sudo -n true 2>/dev/null; then
        echo "Script has sudo access."
    else
        echo "This script may require sudo access for some operations (e.g., Chrome installation)."
        echo "You may be prompted for your password during installation."
    fi

    if ! command_exists brew; then
        echo "Homebrew is not installed. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH
        if [[ $(uname -m) == "arm64" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> $HOME/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> $HOME/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    else
        echo "Homebrew is already installed."
    fi

    echo "Note: You may be prompted for your password when installing Google Chrome later in the script."

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"

    # Check for sudo access
    if sudo -n true 2>/dev/null; then
        echo "Script has sudo access."
    else
        echo "This script requires sudo access for package management and installations."
        echo "You will be prompted for your password during installation."
    fi

    if command_exists apt-get; then
        PKG_MANAGER="apt-get"
    elif command_exists dnf; then
        PKG_MANAGER="dnf"
    elif command_exists yum; then
        PKG_MANAGER="yum"
    else
        echo "Unsupported Linux distribution. Please install the required packages manually."
        exit 1
    fi

    echo "Note: This script will use sudo to install packages and perform system-wide operations."

else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Detected operating system: $OS"

# Install Python 3 if not already installed
if ! command_exists python3; then
    echo "Installing Python 3..."
    if [[ "$OS" == "macOS" ]]; then
        brew install python
    else
        sudo $PKG_MANAGER update
        sudo $PKG_MANAGER install -y python3 python3-pip
    fi
else
    echo "Python 3 is already installed."
fi

# Ensure pip is installed and up to date
echo "Updating pip..."
python3 -m pip install --upgrade pip

# Install required Python packages
echo "Installing required Python packages..."
python3 -m pip install requests tqdm beautifulsoup4 matplotlib numpy playwright web3

# Install Playwright browsers
echo "Installing Playwright browsers..."
python3 -m playwright install

# Check if Google Chrome is installed, install if not
if ! command_exists google-chrome && ! command_exists google-chrome-stable; then
    echo "Google Chrome is not installed. Installing Google Chrome..."
    if [[ "$OS" == "macOS" ]]; then
        brew install --cask google-chrome
    else
        if [[ "$PKG_MANAGER" == "apt-get" ]]; then
            wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
            sudo dpkg -i google-chrome-stable_current_amd64.deb
            sudo apt-get install -f
            rm google-chrome-stable_current_amd64.deb
        elif [[ "$PKG_MANAGER" == "dnf" || "$PKG_MANAGER" == "yum" ]]; then
            sudo $PKG_MANAGER install -y google-chrome-stable
        fi
    fi
else
    echo "Google Chrome is already installed."
fi

echo "Installation complete! You can now run the Python scripts without any additional setup."
