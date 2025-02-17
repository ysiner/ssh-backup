import serial
from time import sleep
from datetime import datetime
import os
import zipfile

def send_to_console(ser: serial.Serial, command: str, wait_time: float = 0.5):
    command_to_send = command + "\r"
    ser.write(command_to_send.encode('utf-8'))
    sleep(wait_time)
    
    output = ""
    while True:
        if ser.inWaiting() > 0:
            part = ser.read(ser.inWaiting()).decode('utf-8')
            if "--More--" in part:
                ser.write(b" ")  # Send space to get more output
                part = part.replace("--More--", "")
            output += part
            sleep(wait_time)
        else:
            break
    
    return output

def get_hostname(connection):
    try:
        hostname_output = send_to_console(connection, "show startup")
        for line in hostname_output.splitlines():
            if "hostname" in line.lower():
                return line.split()[-1].strip()
    except Exception as e:
        print(f"Failed to retrieve hostname: {e}")
    return "unknown"

def perform_console_backup(com_port, baudrate, username=None, password=None, backup_directory='./backups'):
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
        with serial.Serial(com_port, baudrate=int(baudrate), timeout=1) as connection:
            send_to_console(connection, "")
            if username and password:
                send_to_console(connection, f"username {username}")  
                send_to_console(connection, f"password {password}")  
            send_to_console(connection, "enable")
            send_to_console(connection, "terminal length 0")
            hostname = get_hostname(connection)
            if hostname == "unknown":
                hostname = "console_device"

            device_backup_dir = os.path.join(backup_directory, f"{hostname}_{timestamp}")
            os.makedirs(device_backup_dir, exist_ok=True)

            for command, description in zip(commands, command_descriptions):
                filepath = os.path.join(device_backup_dir, f"{description}.txt")
                with open(filepath, "w") as f:
                    f.write(f"{hostname}#{command}\n")
                    command_output = send_to_console(connection, command, wait_time=2)
                    f.write(command_output)
                    f.write("\nEnd of File")
                zip_file.write(filepath, os.path.basename(filepath))

    return zip_filepath if success else None

# Example usage
if __name__ == "__main__":
    backup_path = perform_console_backup(
        com_port="COM3",
        baudrate=9600,
        username="your_username",
        password="your_password",
        backup_directory="./backups"
    )
    print(f"Backup saved to {backup_path}")
