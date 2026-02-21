# Netmiko Script Output Examples

## Lab Topology

- Router1 (IOL) - 192.168.1.10
- Router2 (IOL) - 192.168.1.11
- Switch1 (IOL-L2) - 192.168.1.12
- External Connector (Bridge mode)
- CML Free + WSL2 + Python 3 + Netmiko

## show_interfaces.py

Connects to a single device and runs `show ip interface brief`.

```
Interface              IP-Address      OK? Method Status                Protocol
Ethernet0/0            192.168.1.10    YES NVRAM  up                    up
Ethernet0/1            unassigned      YES NVRAM  administratively down down
Ethernet0/2            unassigned      YES NVRAM  administratively down down
Ethernet0/3            unassigned      YES NVRAM  administratively down down
```

## show_interfaces_multi.py

Loops through all lab devices and runs `show ip interface brief` on each.

```
========================================
Device: hostname Router1
========================================
Interface              IP-Address      OK? Method Status                Protocol
Ethernet0/0            192.168.1.10    YES NVRAM  up                    up
Ethernet0/1            unassigned      YES NVRAM  administratively down down
Ethernet0/2            unassigned      YES NVRAM  administratively down down
Ethernet0/3            unassigned      YES NVRAM  administratively down down

========================================
Device: hostname Router2
========================================
Interface              IP-Address      OK? Method Status                Protocol
Ethernet0/0            192.168.1.11    YES NVRAM  up                    up
Ethernet0/1            unassigned      YES NVRAM  administratively down down
Ethernet0/2            unassigned      YES NVRAM  administratively down down
Ethernet0/3            unassigned      YES NVRAM  administratively down down

========================================
Device: hostname Switch1
========================================
Interface              IP-Address      OK? Method Status                Protocol
Ethernet0/0            unassigned      YES unset  up                    up
Ethernet0/1            unassigned      YES unset  up                    up
Ethernet0/2            unassigned      YES unset  up                    up
Ethernet0/3            unassigned      YES unset  up                    up
Ethernet1/0            unassigned      YES unset  up                    up
Ethernet1/1            unassigned      YES unset  up                    up
Ethernet1/2            unassigned      YES unset  up                    up
Ethernet1/3            unassigned      YES unset  up                    up
Vlan1                  192.168.1.12    YES NVRAM  up                    up
```

## Requirements

- Python 3.x
- Netmiko (`pip install netmiko`)
- SSH-enabled Cisco devices (CML Free works great for this)
