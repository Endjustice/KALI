import os
import subprocess
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "https://kali.download/nethunter-images/kali-2025.11/rootfs"
ARCHIVE_NAME = "kali-nethunter-rootfs-full-arm64.tar.xz"
SHA_EXPECTED = "b7c60dd5a1db33b399afcecc40be39415f5593f7302b6573aece1265dae44d73"
ROOTFS_DIR = "/data/data/com.termux/files/kali"

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

def run_cmd(cmd, fail=True):
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        if fail:
            print(Fore.RED + "[ERROR]" + Style.RESET_ALL, "Command failed:", cmd)
            exit(1)

def download_rootfs():
    print(Fore.CYAN + "[INFO]" + Style.RESET_ALL, "Downloading rootfs archive...")
    run_cmd(f"curl -LO {BASE_URL}/{ARCHIVE_NAME}")

def verify_sha():
    print(Fore.CYAN + "[INFO]" + Style.RESET_ALL, "Verifying SHA256 checksum...")
    result = subprocess.run(f"sha256sum {ARCHIVE_NAME}", shell=True, capture_output=True, text=True)
    actual_sha = result.stdout.strip().split()[0]
    if actual_sha != SHA_EXPECTED:
        print(Fore.RED + "[ERROR]" + Style.RESET_ALL, "SHA mismatch!")
        exit(1)
    print(Fore.GREEN + "[OK]" + Style.RESET_ALL, "SHA256 verified.")

def extract_rootfs():
    print(Fore.CYAN + "[INFO]" + Style.RESET_ALL, "Extracting rootfs...")
    os.makedirs(ROOTFS_DIR, exist_ok=True)
    run_cmd(f"proot --link2symlink tar -xf {ARCHIVE_NAME} -C {ROOTFS_DIR} --strip-components=1")

def configure_locale():
    locale_gen = f"{ROOTFS_DIR}/etc/locale.gen"
    if os.path.exists(locale_gen):
        run_cmd(f"sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' {locale_gen}")
        run_cmd(f"proot -0 -r {ROOTFS_DIR} /sbin/dpkg-reconfigure locales")

def install_gui():
    print(Fore.CYAN + "[INFO]" + Style.RESET_ALL, "Installing GUI...")
    run_cmd(f"proot -0 -r {ROOTFS_DIR} apt update")
    run_cmd(f"proot -0 -r {ROOTFS_DIR} apt install -y tigervnc-standalone-server dbus-x11 kali-desktop-xfce")

def install_browser():
    print(Fore.CYAN + "[INFO]" + Style.RESET_ALL, "Installing browser...")
    run_cmd(f"proot -0 -r {ROOTFS_DIR} apt install -y chromium")

def show_banner():
    clear()
    time.sleep(1)
    banner = """
███    ███ ██ ███████ ████████  █████  ██   ██ ███████  █████  ██████  ████████ ███████ 
████  ████ ██ ██         ██    ██   ██ ██   ██ ██      ██   ██ ██   ██    ██    ██      
██ ████ ██ ██ ███████    ██    ███████ ███████ █████   ███████ ██████     ██    ███████ 
██  ██  ██ ██      ██    ██    ██   ██ ██   ██ ██      ██   ██ ██         ██         ██ 
██      ██ ██ ███████    ██    ██   ██ ██   ██ ███████ ██   ██ ██         ██    ███████ 
    """
    print(Fore.YELLOW + Style.BRIGHT + banner)
    print(Fore.GREEN + Style.BRIGHT + "MISTAKE619")

def main():
    clear()
    download_rootfs()
    verify_sha()
    extract_rootfs()
    configure_locale()
    install_gui()
    install_browser()
    show_banner()

if __name__ == "__main__":
    main()
