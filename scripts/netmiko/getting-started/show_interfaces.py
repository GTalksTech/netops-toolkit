from netmiko import ConnectHandler

device = {
    "device_type": "cisco_ios",
    "host": "ip_address_goes_here",
    "username": "users_goes_here",
    "password": "password_goes_here",
}

connection = ConnectHandler(**device)
output = connection.send_command("show ip interface brief")
print(output)
connection.disconnect()
