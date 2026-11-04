"""GPL-3.0-or-later. Per-user installation and Windows notification-area UI."""
import ctypes
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time

LOG = logging.getLogger('ProCon2Bridge')
INSTALL = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Programs' / 'ProCon2Bridge'
STARTUP = Path(os.environ.get('APPDATA', str(Path.home()))) / 'Microsoft/Windows/Start Menu/Programs/Startup/ProCon2Bridge.lnk'


def message(text, error=False):
    ctypes.windll.user32.MessageBoxW(None, str(text), 'ProCon2Bridge', 0x10 if error else 0x40)


def spawn(exe, *args):
    return subprocess.Popen([str(exe), *args], cwd=str(Path(exe).parent), creationflags=0x08000000)


def send_control(command):
    try:
        with socket.create_connection(('127.0.0.1', 26759), timeout=2) as stream:
            stream.sendall(command.encode() + b'\n')
            return stream.recv(16) == b'OK\n'
    except OSError:
        return False


def register_startup(exe):
    # A normal Startup shortcut is visible and can be disabled by Task Manager.
    # Do not edit StartupApproved: Windows owns the user's enabled/disabled choice.
    def literal(value):
        return "'" + str(value).replace("'", "''") + "'"
    script = ("$ErrorActionPreference='Stop'; $w=New-Object -ComObject WScript.Shell; "
              "$s=$w.CreateShortcut(" + literal(STARTUP) + "); "
              "$s.TargetPath=" + literal(exe) + "; $s.Arguments='--background'; "
              "$s.WorkingDirectory=" + literal(Path(exe).parent) + "; "
              "$s.Description='ProCon2Bridge Bluetooth controller bridge'; $s.Save()")
    subprocess.run(['powershell.exe', '-NoProfile', '-Command', script], check=True,
                   creationflags=0x08000000, capture_output=True)
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
        try: winreg.DeleteValue(key, 'ProCon2Bridge')
        except FileNotFoundError: pass


def driver_setup(root):
    import winreg
    driver = Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'USBip/usbip.exe'
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\usbip2_ude'): pass
        installed = driver.is_file()
    except FileNotFoundError:
        installed = False
    if installed: return
    script = root / 'scripts/ProCon2Bridge-Install-Driver.ps1'
    if not script.is_file():
        raise RuntimeError('USB/IP driver is missing. Extract the complete release ZIP and run ProCon2Bridge.exe.')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)],
                            creationflags=0x08000000, capture_output=True, text=True)
    if result.returncode not in (0, 3010):
        raise RuntimeError('USB/IP driver setup failed. See driver-install.log in the extracted folder.\n' + result.stderr[-1000:])
    if result.returncode == 3010:
        message('Driver installed. Restart Windows to finish setup, then press a button on your controller.')


def prepare(root, options):
    """Return True when this launcher has delegated to the installed copy."""
    installed_exe = INSTALL / 'ProCon2Bridge.exe'
    is_installed = root.resolve() == INSTALL.resolve()
    if options.stop:
        return False
    if not is_installed:
        INSTALL.mkdir(parents=True, exist_ok=True)
        source_exe = root / 'ProCon2Bridge.exe'
        changed = not installed_exe.exists() or source_exe.read_bytes() != installed_exe.read_bytes()
        if changed:
            send_control('stop')
            # Wait for the old process to detach the virtual controller and unload its EXE.
            for attempt in range(100):
                try:
                    shutil.copy2(source_exe, installed_exe)
                    break
                except PermissionError:
                    time.sleep(.1)
            else:
                raise RuntimeError('The previous ProCon2Bridge is still running. Exit it from the tray and try again.')
        for name in ('config.example.json', 'README.md', 'SECURITY.md', 'LICENSE.md'):
            if (root/name).is_file(): shutil.copy2(root/name, INSTALL/name)
        if not (INSTALL/'config.json').exists() and (root/'config.json').is_file():
            shutil.copy2(root/'config.json', INSTALL/'config.json')
        for folder in ('docs', 'dependency-licenses', 'src', 'scripts', 'drivers'):
            if (root/folder).is_dir(): shutil.copytree(root/folder, INSTALL/folder, dirs_exist_ok=True)
    marker = INSTALL / 'desktop.json'
    if not marker.exists():
        register_startup(installed_exe)
        marker.write_text(json.dumps({'startup_registered': True}), encoding='utf-8')
    if not is_installed:
        args = [arg for arg in sys.argv[1:] if arg != '--background']
        spawn(installed_exe, '--background', *args)
        return True
    if not options.settings:
        driver_setup(INSTALL)
    return False


class SingleInstance:
    def __init__(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.CreateMutexW.restype = ctypes.c_void_p
        kernel.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
        self.kernel = kernel
        self.handle = kernel.CreateMutexW(None, False, 'Local\\ProCon2Bridge.Desktop')
        if not self.handle: raise ctypes.WinError(ctypes.get_last_error())
        self.existing = ctypes.get_last_error() == 183

    def close(self):
        self.kernel.CloseHandle.argtypes = (ctypes.c_void_p,)
        self.kernel.CloseHandle(self.handle)


class Tray:
    def __init__(self, root, shutdown):
        import pystray
        from PIL import Image, ImageDraw
        self.root, self.shutdown = root, shutdown
        image = Image.new('RGBA', (64,64), (0,0,0,0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((3,12,61,53), radius=16, fill='#1976D2')
        draw.rectangle((13,25,31,31), fill='white'); draw.rectangle((19,19,25,37), fill='white')
        draw.ellipse((42,22,50,30), fill='white'); draw.ellipse((35,32,43,40), fill='white')
        def settings(*_): spawn(root/'ProCon2Bridge.exe', '--settings')
        def calibrate(*_):
            if send_control('calibrate'): self.icon.notify('Keep the controller flat and still for a few seconds.', 'Gyro calibration')
        def quit_app(*_): shutdown.set()
        self.icon = pystray.Icon('ProCon2Bridge', image, 'ProCon2Bridge - starting', pystray.Menu(
            pystray.MenuItem('Back buttons / Settings', settings, default=True),
            pystray.MenuItem('Calibrate motion', calibrate),
            pystray.MenuItem('Windows Startup settings', lambda *_: os.startfile('ms-settings:startupapps')),
            pystray.MenuItem('Open app folder / logs', lambda *_: os.startfile(str(root))),
            pystray.MenuItem('Exit ProCon2Bridge', quit_app)))
        self.icon.run_detached()
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while not self.shutdown.wait(1):
            try:
                state = json.loads((self.root/'status.json').read_text())['state']
                self.icon.title = 'ProCon2Bridge - ' + state
            except (OSError, ValueError, KeyError): pass

    def close(self):
        self.icon.stop()
