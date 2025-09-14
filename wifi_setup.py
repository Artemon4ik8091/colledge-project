from flask import Flask, request, render_template
import subprocess
import time

app = Flask(__name__)

# Параметры точки доступа
HOTSPOT_SSID = "MySetupAP"
HOTSPOT_PASSWORD = "SetupPass123"
INTERFACE = "wlp3s0"  # Интерфейс WiFi
CONNECTION_NAME = "MyWIFI"

def is_interface_available():
    """Проверяет, существует ли интерфейс."""
    try:
        result = subprocess.run(['nmcli', '-t', '-f', 'DEVICE', 'device'],
                              capture_output=True, text=True, check=True)
        return INTERFACE in result.stdout
    except subprocess.CalledProcessError:
        return False

def setup_hotspot():
    """Создаёт точку доступа, если она не активна."""
    if not is_interface_available():
        print(f"Интерфейс {INTERFACE} не найден. Не могу создать точку доступа.")
        return False

    try:
        # Проверяем, активна ли точка доступа
        result = subprocess.run(['nmcli', '-t', '-f', 'NAME', 'con', 'show', '--active'],
                              capture_output=True, text=True, check=True)
        if HOTSPOT_SSID in result.stdout:
            print(f"Точка доступа {HOTSPOT_SSID} уже активна.")
            return True

        # Отключаем существующее соединение Hotspot, если есть
        subprocess.run(['nmcli', 'con', 'down', 'Hotspot'], check=False)
        
        # Создаём точку доступа
        subprocess.run(['nmcli', 'd', 'wifi', 'hotspot', 'ifname', INTERFACE,
                       'ssid', HOTSPOT_SSID, 'password', HOTSPOT_PASSWORD], check=True)
        print(f"Точка доступа {HOTSPOT_SSID} создана.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании точки доступа: {e}")
        return False

@app.route('/', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        ssid = request.form['ssid']
        psk = request.form['psk']
        
        try:
            # Отключим точку доступа
            subprocess.run(['nmcli', 'con', 'down', 'Hotspot'], check=True)
            
            # Удалим старое подключение, если существует
            subprocess.run(['nmcli', 'con', 'delete', CONNECTION_NAME], check=False)
            
            # Настроим новое подключение через nmcli
            subprocess.run([
                'nmcli', 'con', 'add',
                'type', 'wifi',
                'ifname', INTERFACE,
                'con-name', CONNECTION_NAME,
                'ssid', ssid,
                'wifi-sec.key-mgmt', 'wpa-psk',
                'wifi-sec.psk', psk
            ], check=True)
            
            # Активируем подключение
            subprocess.run(['nmcli', 'con', 'up', CONNECTION_NAME], check=True)
            
            return '''
            <h1>Успех!</h1>
            <p>Orange Pi подключён к WiFi. Отключитесь от точки доступа MySetupAP.</p>
            '''
        except subprocess.CalledProcessError as e:
            return f'<h1>Ошибка</h1><p>Не удалось настроить WiFi: {str(e)}</p>'
    
    return render_template('setup_form.html')

if __name__ == '__main__':
    # Создаём точку доступа при запуске
    setup_hotspot()
    # Запускаем Flask
    app.run(host='0.0.0.0', port=80)