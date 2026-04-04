# Installing VMware Workstation Pro

VMware Workstation Pro is a Type 2 hypervisor that runs virtual machines on your Windows or Linux desktop. As of late 2024, Broadcom made VMware Workstation Pro free for personal use, so there is no license cost for home lab work.

CML Free (Cisco Modeling Labs) runs as a VM inside VMware Workstation. This guide gets VMware installed so you are ready to deploy CML.

---

## System Requirements

- Windows 10 or 11 (64-bit)
- CPU with hardware virtualization support (Intel VT-x or AMD-V) enabled in BIOS/UEFI
- 8 GB RAM minimum (16 GB+ recommended if you plan to run CML alongside other VMs)
- ~2 GB disk space for the VMware install itself, plus whatever your VMs need

---

## Step 1: Create a Broadcom Account

VMware downloads now live on the Broadcom support portal. You need a free Broadcom account to access them.

1. Go to [support.broadcom.com](https://support.broadcom.com)
2. Click **Register** and create an account using your personal email
3. Complete any email verification steps

If you already have a Broadcom account from a previous VMware download, skip this step.

---

## Step 2: Download VMware Workstation Pro

1. Log in to [support.broadcom.com](https://support.broadcom.com)
2. Navigate to **VMware Cloud Foundation** > **My Downloads** > **VMware Workstation Pro**
3. Select the latest version available for your platform (Windows or Linux)
4. Download the installer

The Broadcom portal layout changes periodically. If the navigation path above does not match exactly, search for "VMware Workstation Pro" from the portal's search bar.

---

## Step 3: Enable Hardware Virtualization (if needed)

VMware requires Intel VT-x or AMD-V to be enabled at the BIOS/UEFI level. Most modern systems ship with this on by default, but if VMware throws a virtualization error on first launch, you will need to toggle it.

The setting is typically under **Advanced** > **CPU Configuration** in your BIOS. Look for:

- **Intel Virtualization Technology (VT-x)** on Intel systems
- **SVM Mode** on AMD systems

Enable it, save, and reboot. The exact menu location varies by motherboard vendor.

---

## Step 4: Install VMware Workstation Pro

1. Run the downloaded installer
2. Accept the license agreement
3. Choose the default install path unless you have a reason to change it
4. When prompted for a license type, select **Use VMware Workstation Pro for Personal Use** (or similar wording for the free personal license)
5. Uncheck the boxes for customer experience programs and update checks if you prefer
6. Click **Install** and let it finish
7. Restart your machine if prompted

---

## Step 5: Verify the Installation

1. Open VMware Workstation Pro from the Start menu
2. Confirm it launches to the home screen without any license errors or trial warnings
3. Check **Help** > **About VMware Workstation** to confirm the version number

If you see a license prompt asking for a key, go back through the setup and make sure you selected the personal use option. You should not need a paid license key for home lab use.

---

## Common Gotchas

**Hyper-V conflicts.** If you have Hyper-V, WSL2, or Windows Sandbox enabled, VMware may warn about compatibility. Recent versions of VMware Workstation Pro support running alongside Hyper-V, but performance can be affected. If you run into issues, check VMware's documentation on Hyper-V coexistence for your specific version.

**Windows Defender SmartScreen.** Windows may flag the installer as unrecognized. Click **More info** > **Run anyway** if you downloaded it directly from the Broadcom portal.

**Broadcom portal navigation.** The download portal is not the most intuitive. If you cannot find the download link, search directly for "VMware Workstation Pro" within the portal or check the VMware Flings page as a fallback.

---

## Next Steps

With VMware Workstation Pro installed, you are ready to deploy Cisco Modeling Labs. See [install-cml-free.md](install-cml-free.md) for the next step.
