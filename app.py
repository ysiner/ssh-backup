from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, jsonify
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from ssh import scan_subnet, perform_backup as perform_backup_ssh
from console import perform_console_backup
from exceptions import AuthenticationError, SSHKeyError, DeviceConnectionError
import paramiko
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_default_secret_key')

# Logging configuration
logging.basicConfig(filename='backup_errors.log', level=logging.ERROR,
                    format='%(asctime)s:%(levelname)s:%(message)s')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/backup_page', methods=['GET', 'POST'])
def backup_page():
    download_link = session.pop('download_link', None)
    return render_template('backup.html', download_link=download_link)

@app.route('/backup', methods=['POST'])
def perform_backup():
    response = {'success': False, 'error': None, 'download_link': None}

    try:
        connection_type = request.form['connection_type']
        
        if connection_type == "SSH":
            ip_input = request.form['ip_input']
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            enable_password = request.form.get('enable_password', '')

            if not ip_input:
                response['error'] = 'IP adresi boş olamaz.'
                return jsonify(response)

            try:
                ip_addresses = scan_subnet(ip_input)
                if not ip_addresses:
                    response['error'] = 'Belirtilen aralıkta aktif cihaz bulunamadı.'
                    return jsonify(response)
            except Exception as e:
                response['error'] = "IP tarama işlemi sırasında hata oluştu."
                logging.error(f"IP tarama hatası: {str(e)}")
                return jsonify(response)

            backup_directory = './backups'
            os.makedirs(backup_directory, exist_ok=True)

            try:
                zip_filepath = perform_backup_ssh(ip_addresses, username, password, enable_password, backup_directory)
                if zip_filepath:
                    response['success'] = True
                    zip_filename = os.path.basename(zip_filepath)
                    response['download_link'] = url_for('download_file', filename=zip_filename)
                else:
                    response['error'] = "Bazı cihazlar için yedekleme başarısız oldu."
            except AuthenticationError as e:
                response['error'] = "Bağlantı hatası: Kimlik doğrulama başarısız. Lütfen kullanıcı adı ve şifrenizi kontrol edin."
                logging.error(f"Kimlik doğrulama hatası - Cihaz: {ip_input}, Hata: {str(e)}")
            except SSHKeyError as e:
                response['error'] = "SSH anahtar doğrulama hatası. Lütfen SSH anahtar dosyanızı kontrol edin."
                logging.error(f"SSH anahtar hatası - Cihaz: {ip_input}, Hata: {str(e)}")
            except DeviceConnectionError as e:
                response['error'] = "Bağlantı başarısız. Cihaza erişim sağlanamıyor."
                logging.error(f"Bağlantı hatası - Cihaz: {ip_input}, Hata: {str(e)}")
            except Exception as e:
                response['error'] = "SSH yedekleme sırasında beklenmeyen bir hata oluştu."
                logging.error(f"SSH yedekleme hatası - IP: {ip_input}, Hata: {str(e)}")

        elif connection_type == "Console":
            com_port = request.form['com_port']
            baudrate = request.form['baudrate']
            username_console = request.form.get('username_console', '')
            password_console = request.form.get('password_console', '')

            if not com_port or not baudrate:
                response['error'] = "Lütfen geçerli bir COM portu ve baudrate sağlayın."
                return jsonify(response)

            try:
                backup_directory = './backups'
                os.makedirs(backup_directory, exist_ok=True)
                zip_filepath = perform_console_backup(com_port, baudrate, username_console, password_console, backup_directory)
                if zip_filepath:
                    response['success'] = True
                    zip_filename = os.path.basename(zip_filepath)
                    response['download_link'] = url_for('download_file', filename=zip_filename)
                else:
                    response['error'] = "Konsol cihazına bağlantı kurarken veya yedekleme sürecinde hata oluştu."
            except Exception as e:
                response['error'] = "Konsol yedekleme sırasında beklenmeyen bir hata oluştu."
                logging.error(f"Konsol yedekleme hatası: {str(e)}")

    except Exception as e:
        response['error'] = "Yedekleme sırasında beklenmedik bir hata oluştu."
        logging.error(f"Genel yedekleme hatası: {str(e)}")

    return jsonify(response)

@app.route('/download/<filename>')
def download_file(filename):
    backup_directory = './backups'
    try:
        return send_from_directory(backup_directory, filename, as_attachment=True)
    except FileNotFoundError:
        return "Dosya bulunamadı", 404

@app.route('/device_code')
def device_code():
    return render_template('device_code.html')

@app.route('/execute_device_code', methods=['POST'])
def execute_device_code():
    ip = request.form.get('ip')
    username = request.form.get('username')
    password = request.form.get('password')
    enable_password = request.form.get('enable_password')
    commands = request.form.get('commands')

    response = {'output': ''}

    if not commands:
        response['output'] = 'Error: No commands provided'
        return jsonify(response)

    commands_list = commands.split('\n')

    device = {
        "host": ip,
        "username": username,
        "password": password,
        "device_type": "cisco_ios",
        "secret": enable_password,
    }

    try:
        connection = ConnectHandler(**device)
        connection.enable()
        output = ""
        if 'conf t' in commands_list:
            config_commands = commands_list[commands_list.index('conf t') + 1:]
            output += connection.send_config_set(config_commands) + "\n"
        else:
            for command in commands_list:
                output += connection.send_command(command, expect_string=r'#', read_timeout=10) + "\n"

        response['output'] = output
        connection.disconnect()
    except Exception as e:
        response['output'] = f"Error: {str(e)}"

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
