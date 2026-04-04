# Installing WSL2 (Windows Subsystem for Linux)

WSL2 (Windows Subsystem for Linux 2) lets you run a full Linux environment directly on Windows without a separate VM or dual-boot setup. It is the recommended way to run the Python scripts in this repo.

---

## System Requirements

- Windows 10 version 2004 or later (Build 19041+), or Windows 11
- 64-bit processor with virtualization support enabled in BIOS/UEFI
- At least 4 GB of RAM (8 GB+ recommended)

If you are unsure about your Windows version, open PowerShell and run:

```powershell
winver
```

---

## Step 1: Enable WSL

Open PowerShell **as Administrator** and run:

```powershell
wsl --install
```

This single command enables the required Windows features (Virtual Machine Platform and Windows Subsystem for Linux) and installs Ubuntu as the default distro.

If WSL is already installed and you just need to add Ubuntu:

```powershell
wsl --install -d Ubuntu
```

Restart your machine when prompted.

---

## Step 2: Complete Ubuntu Setup

After the reboot, Ubuntu will launch automatically (or open it from the Start menu). It will ask you to create a Linux username and password. These are local to WSL and do not need to match your Windows credentials.

Pick something simple you will remember. You will need this password for `sudo` commands.

---

## Step 3: Update Your System

Once you are at the Ubuntu prompt, update the package lists and installed packages:

```bash
sudo apt update && sudo apt upgrade -y
```

This ensures you are starting with current packages.

---

## Step 4: Verify the Installation

Confirm WSL2 is running correctly:

```powershell
wsl --list --verbose
```

You should see output like:

```
  NAME      STATE           VERSION
* Ubuntu    Running         2
```

The `VERSION` column should show `2`. If it shows `1`, upgrade it:

```powershell
wsl --set-version Ubuntu 2
```

From inside WSL, verify you have a working Linux environment:

```bash
uname -a
cat /etc/os-release
```

---

## Choosing a Distro

The `wsl --install` command defaults to Ubuntu, which is what we recommend. It has the widest community support, the most tutorials, and the best compatibility with Python tooling.

If you want to see other available distros:

```powershell
wsl --list --online
```

For the purposes of this repo, stick with Ubuntu unless you have a specific reason not to.

---

## Accessing Windows Files from WSL

Your Windows drives are mounted under `/mnt/`. For example, your C: drive is at `/mnt/c/`.

```bash
ls /mnt/c/Users/
```

You can work with files on either side, but for best performance, keep your project files inside the WSL filesystem (your home directory) rather than on `/mnt/c/`.

---

## Common Gotchas

**Virtualization not enabled.** If the install fails with a virtualization error, you need to enable Intel VT-x or AMD-V in your BIOS/UEFI settings. The exact steps vary by motherboard manufacturer. Look for "Virtualization Technology" or "SVM Mode" in the BIOS.

**WSL version stuck on 1.** If `wsl --list --verbose` shows version 1, make sure the Virtual Machine Platform feature is enabled:

```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

Then restart and run `wsl --set-version Ubuntu 2`.

**Windows Defender or antivirus interference.** Some endpoint protection software can slow down or block WSL operations. If WSL is unusually slow, check whether your security software has exclusions for the WSL process.

**Copy/paste in the terminal.** Right-click pastes in the default Windows Terminal. You can also use `Ctrl+Shift+V` to paste and `Ctrl+Shift+C` to copy.

**Line ending differences.** Windows uses `\r\n` line endings while Linux uses `\n`. If you edit files on Windows and run them in WSL, you may hit issues. Configure git inside WSL to handle this:

```bash
git config --global core.autocrlf input
```

---

## Next Steps

With WSL2 running, you are ready to set up Python. See [install-python.md](install-python.md) for the next step.
