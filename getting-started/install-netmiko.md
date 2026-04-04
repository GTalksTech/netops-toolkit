# Installing Netmiko

Netmiko is a Python library that simplifies SSH connections to network devices. It supports Cisco IOS, IOS-XE, NX-OS, Fortinet, Aruba, Palo Alto, and dozens of other vendors out of the box. If you have ever scripted SSH with raw Paramiko and hated it, Netmiko is the fix.

All scripts in this repo use Netmiko for device connectivity.

## Prerequisites

You need Python 3.8+ and pip installed. If you do not have Python yet, start with [install-python.md](install-python.md).

## Install Netmiko

```bash
pip install netmiko
```

If you are working inside a virtual environment (recommended), activate it first:

```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

Then install:

```bash
pip install netmiko
```

### Using requirements.txt

Every script folder in this repo includes a `requirements.txt`. You can install all dependencies at once:

```bash
pip install -r requirements.txt
```

This pulls in Netmiko and anything else the script needs.

## Verify the Install

Run this one-liner to confirm Netmiko is installed and importable:

```bash
python3 -c "from netmiko import ConnectHandler; print('Netmiko ready')"
```

You should see:

```
Netmiko ready
```

If you get an import error, make sure you are in the same environment where you ran `pip install`.

## Common Issues

### Build errors during install (Linux)

Netmiko depends on Paramiko and the cryptography library. On some Linux systems, especially older ones, the install fails because the C extensions cannot compile.

Fix it by installing the build dependencies first:

```bash
sudo apt install build-essential libssl-dev libffi-dev python3-dev
```

Then retry:

```bash
pip install netmiko
```

### Permission errors

If you see permission errors and you are not in a virtual environment, either use a venv (preferred) or add the `--user` flag:

```bash
pip install --user netmiko
```

### Old pip version

If pip complains about metadata or resolver issues, upgrade it:

```bash
pip install --upgrade pip
```

## Next Steps

- [Install VMware Workstation](install-vmware.md) for running your lab environment
- [Install CML Free](install-cml-free.md) to build the lab topology used by these scripts
