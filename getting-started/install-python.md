# Installing Python 3

Python is required to run the automation scripts in this repo. This guide
covers installing Python 3, pip, and setting up a virtual environment.

## Check If Python Is Already Installed

```bash
python3 --version
pip3 --version
```

If both commands return version numbers (Python 3.8 or higher), skip to
[Create a Virtual Environment](#create-a-virtual-environment).

## Install on WSL2 / Ubuntu (Recommended)

Ubuntu comes with Python 3 pre-installed in most cases. If it is missing
or you need a newer version:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

Verify:

```bash
python3 --version
pip3 --version
```

## Install on macOS

Using Homebrew:

```bash
brew install python3
```

If you do not have Homebrew, install it first from [brew.sh](https://brew.sh).

## Install on Windows (Native)

If you are not using WSL2, download the installer from
[python.org/downloads](https://www.python.org/downloads/).

During installation:

1. Check "Add python.exe to PATH" on the first screen
2. Click "Install Now"
3. Verify in a new terminal: `python --version`

WSL2 is the recommended path for this repo. Native Windows works but you
may run into path and line-ending issues with some scripts.

## Create a Virtual Environment

A virtual environment keeps each project's dependencies isolated so they
do not conflict with other Python projects on your system.

```bash
# Navigate to the project directory
cd netops-toolkit/scripts/netmiko/ai-network-documentation

# Create the virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Your prompt will change to show (venv)
```

To deactivate when you are done:

```bash
deactivate
```

## Install Project Dependencies

With your virtual environment activated:

```bash
pip install -r requirements.txt
```

This installs Netmiko and everything else the scripts need.

## Common Issues

| Problem | Fix |
|---------|-----|
| `python3: command not found` | Run `sudo apt install python3` (Ubuntu) or check your PATH |
| `pip3: command not found` | Run `sudo apt install python3-pip` |
| `No module named venv` | Run `sudo apt install python3-venv` |
| Permission errors with pip | Use a virtual environment instead of installing globally |

## Next Steps

- [Installing Netmiko](install-netmiko.md)
