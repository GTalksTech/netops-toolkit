from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "192.168.1.10",
    "username": "admin",
    "password": "cisco123",
}

connection = ConnectHandler(**device)
output = connection.send_command("show ip interface brief")
print(output)
connection.disconnect()
