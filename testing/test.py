import winreg
import subprocess
import os

def get_open_with_apps(ext):
    """
    Returns a list of programs (exe filenames and ProgIDs) that appear in the 'Open with' dialog
    for the specified file type (.ext) and can actually open the files.
    """
    apps = set()
    # User-specific OpenWithList
    try:
        key_path = fr"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{ext}\OpenWithList"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    if name != 'MRUList' and value.lower().endswith('.exe'):
                        # Check if the program exists and is executable
                        program_path = get_program_path(value)
                        if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
                            apps.add(value)
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass

    # User-specific OpenWithProgids
    try:
        key_path = fr"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{ext}\OpenWithProgids"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    # For ProgIDs, resolve to actual executable and filter
                    program_path = get_program_path(name)
                    if os.path.isfile(program_path) and os.access(program_path, os.X_OK):
                        apps.add(name)
                    i += 1
                except OSError:
                    break
    except FileNotFoundError:
        pass

    return list(apps)





def open_with_app(app, file_path):
    # Falls nur der Programmname (z.B. "chrome.exe") gegeben ist, versuche ihn direkt zu starten
    try:
        subprocess.Popen([app, file_path])
    except FileNotFoundError:
        print(f"Programm {app} nicht gefunden. Bitte vollständigen Pfad angeben.")

def get_program_path(app_name):
    """Get the full path of a program from the Windows registry."""
    try:
        # Check App Paths registry
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\\" + app_name) as key:
            return winreg.QueryValue(key, None)
    except WindowsError:
        return app_name
print(get_open_with_apps('.png'))
print(get_program_path("pngfile"))
open_with_app(get_program_path("pngfile"), r"C:\\Users\\benne\\OneDrive\\Projekte\\ai-file-manager\\icon2.png")