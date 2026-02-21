from netmiko import ConnectHandler

devices = [
    {
        "device_type": "cisco_ios",
        "host": "ip_address_goes_here",
        "username": "users_goes_here",
        "password": "password_goes_here",
    },
    {
        "device_type": "cisco_ios",
        "host": "ip_address_goes_here",
        "username": "users_goes_here",
        "password": "password_goes_here",
    },
    {
        "device_type": "cisco_ios",
        "host": "ip_address_goes_here",
        "username": "users_goes_here",
        "password": "password_goes_here",,
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
