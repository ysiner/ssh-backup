from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from datetime import datetime
import os
import platform
import subprocess
import concurrent.futures
import zipfile
import ipaddress

def is_device_reachable(ip):
    try:
        if platform.system() == "Windows":
            response = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            response = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        return response.returncode == 0
    except Exception as e:
        print(f"Ping error for {ip}: {e}")
        return False

def scan_subnet(subnet):
    ip_addresses = []
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(is_device_reachable, str(ip)): str(ip) for ip in network.hosts()}
            for future in concurrent.futures.as_completed(futures):
                ip = futures[future]
                if future.result():
                    ip_addresses.append(ip)
    except ValueError:
        ip_addresses = [ip.strip() for ip in subnet.split(',')]
    return ip_addresses

def get_hostname(connection):
    try:
        output = connection.send_command("show startup")
        for line in output.splitlines():
            if "hostname" in line.lower():
                return line.split()[-1].strip()
    except Exception as e:
        print(f"Failed to retrieve hostname: {e}")
    return "unknown"

def perform_backup(ip_addresses, username, password, enable_password, backup_directory='/mnt/backup'):
    commands = [
        "sh env all", "sh startup", "sh access-lists", "sh arp", "sh boot", 
        "sh cdp neighbors", "sh flash: ", "sh int status", "sh int trunk", 
        "sh inv", "sh ip int br", "sh ip route", "sh lldp neighbors", 
        "sh mac address-table", "show vlan brief", "dir"
    ]
    command_descriptions = [
        "env_all", "run", "access_lists", "arp", "boot", "cdp_neighbors", 
        "flash", "int_status", "int_trunk", "inv", "ip_int_br", "ip_route", 
        "lldp_neighbors", "mac_address_table", "vlan_br", "dir"
    ]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{timestamp}.zip"
    zip_filepath = os.path.join(backup_directory, zip_filename)
    os.makedirs(backup_directory, exist_ok=True)

    success = True
    with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
        for ip_address in ip_addresses:
            device = {
                "host": ip_address,
                "username": username,
                "password": password,
                "device_type": "cisco_ios",
                "secret": enable_password,
            }

            try:
                connection = ConnectHandler(**device)
                connection.send_command("terminal length 0")
                if enable_password:
                    connection.enable()

                hostname = get_hostname(connection)
                hostname = hostname if hostname != "unknown" else ip_address
                device_backup_dir = os.path.join(backup_directory, f"{hostname}_{timestamp}")
                os.makedirs(device_backup_dir, exist_ok=True)

                for command, description in zip(commands, command_descriptions):
                    filepath = os.path.join(device_backup_dir, f"{description}.txt")
                    with open(filepath, "w") as f:
                        f.write(f"{hostname}#{command}\n")
                        command_output = connection.send_command(command)
                        f.write(command_output)
                        f.write("\nEnd of File")

                    zip_file.write(filepath, os.path.basename(filepath))

                connection.disconnect()

            except NetmikoAuthenticationException:
                print(f"Authentication failed for {ip_address}. Possible causes include:")
                print("1. Invalid username and password.")
                print("2. Incorrect SSH-key file.")
                print("3. Attempting to connect to an incompatible device.")
                success = False
            except NetmikoTimeoutException:
                print(f"Connection to {ip_address} timed out. The device may be unreachable.")
                success = False
            except Exception as e:
                print(f"Unexpected error for {ip_address}: {e}")
                success = False

    return zip_filepath if success else None
