#!/usr/bin/env python3
import os
import platform
import subprocess
import sys
import time
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "https://old.kali.org/nethunter-images/kali-2025.3/rootfs"
ROOTFS_DIR = "/data/data/com.termux/files/kali"

def info(msg): print(Fore.CYAN + "[INFO]" + Style.RESET_ALL, msg)
def ok(msg):   print(Fore.GREEN + "[OK]" + Style.RESET_ALL, msg)
def err(msg):  print(Fore.RED + "[ERROR]" + Style.RESET_ALL, msg)

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

def run(cmd):
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        err(f"Command failed: {cmd}")
        sys.exit(1)

def get_arch():
    m = platform.machine().lower()
    return {
        "aarch64": "arm64",
        "armv7l": "armhf",
        "i686": "i386",
        "x86_64": "amd64",
    }.get(m, "arm64")

def ask_variant():
    print(Fore.CYAN + "[SELECT]" + Style.RESET_ALL, "Choose installation type:")
    print("  1. full    - GUI + All packages")
    print("  2. minimal - Essential only")
    print("  3. nano    - Essential++")
    choice = input(Fore.YELLOW + "Enter 1/2/3: " + Style.RESET_ALL).strip()
    return {"1": "full", "2": "minimal", "3": "nano"}.get(choice, "minimal")

def pick_url(variant, arch):
    # دو الگوی نام‌گذاری را امتحان می‌کنیم: با و بدون پیشوند نسخه
    names = [
        f"kali-nethunter-rootfs-{variant}-{arch}.tar.xz",
        f"kali-nethunter-2025.3-rootfs-{variant}-{arch}.tar.xz",
    ]
    for name in names:
        url = f"{BASE_URL}/{name}"
        # wget --spider برای بررسی دسترسی بدون دانلود
        try:
            subprocess.check_call(f"wget --spider --no-check-certificate '{url}'", shell=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return url, name
        except subprocess.CalledProcessError:
            continue
    err("No valid URL found for selected variant/arch.")
    sys.exit(1)

def download(url, filename):
    info(f"Downloading with wget: {filename}")
    # نکته: ترتیب صحیح استفاده از -O: اول نام فایل خروجی، سپس URL
    run(f"wget --no-check-certificate --continue -O '{filename}' '{url}'")
    # بررسی حداقل اندازه برای جلوگیری از دانلود HTML
    size = os.path.getsize(filename)
    if size < 50_000_000:
        err("Downloaded file too small; likely HTML/error instead of archive.")
        sys.exit(1)

def extract_rootfs(archive_path, target_dir):
    info("Extracting rootfs...")
    os.makedirs(target_dir, exist_ok=True)
    run(f"proot --link2symlink tar -xf '{archive_path}' -C '{target_dir}' --strip-components=1")
    ok("Extraction complete.")

def banner():
    clear()
    time.sleep(0.5)
    art = """ __  __ ___ ____ _____  _    _  _______ __   _  ___
|  \/  |_ _/ ___|_   _|/ \  | |/ / ____/ /_ / |/ _ \
| |\/| || |\___ \ | | / _ \ | ' /|  _|| '_ \| | (_) |
| |  | || | ___) || |/ ___ \| . \| |__| (_) | |\__, |
|_|  |_|___|____/ |_/_/   \_\_|\_\_____\___/|_|  /_/"""
    print(Fore.YELLOW + Style.BRIGHT + art)
    print(Fore.GREEN + Style.BRIGHT + "MISTAKE619")

def main():
    clear()
    info("Preparing Termux environment...")
    run("pkg update -y && pkg upgrade -y || true")
    run("pkg install -y wget proot tar || true")

    arch = get_arch()
    variant = ask_variant()
    url, filename = pick_url(variant, arch)
    download(url, filename)
    extract_rootfs(filename, ROOTFS_DIR)
    write_launcher(ROOTFS_DIR)
    banner()

if __name__ == "__main__":
    main()
def write_launcher(target_dir):
    info("Writing launcher 'nh'...")
    launcher = os.path.expanduser("~/../usr/bin/nh")
    os.makedirs(os.path.dirname(launcher), exist_ok=True)
    script = f"""#!/data/data/com.termux/files/usr/bin/bash
proot -0 \\
  -r "{target_dir}" \\
  -b /dev:/dev -b /proc:/proc -b /sys:/sys \\
  -b "$TMPDIR":/tmp \\
  -w /root \\
  /usr/bin/env -i HOME=/root TERM="$TERM" PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \\
  /bin/bash -l
"""
    with open(launcher, "w") as f:
        f.write(script)
    run(f"chmod +x '{launcher}'")
    ok("Launcher installed. Run: nh")
