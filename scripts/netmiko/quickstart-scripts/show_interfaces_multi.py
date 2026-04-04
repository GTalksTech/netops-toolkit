from netmiko import ConnectHandler

devices = [
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.10",
        "username": "admin",
        "password": "cisco123",
    },
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.11",
        "username": "admin",
        "password": "cisco123",
    },
    {
        "device_type": "cisco_ios",
        "host": "192.168.1.12",
        "username": "admin",
        "password": "cisco123",
    },
]

for device in devices:
    connection = ConnectHandler(**device)
    hostname = connection.send_command("show run | include hostname")
    print(f"\n{'='*40}")
    print(f"Device: {hostname}")
    print(f"{'='*40}")
    output = connection.send_command("show ip interface brief")
    print(output)
    connection.disconnect()
