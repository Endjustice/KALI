#!/usr/bin/env python3
import os
import platform
import subprocess
import sys
import time
from colorama import init, Fore, Style

init(autoreset=True)

# Map variant+arch -> (URL, SHA256)
TARBALLS = {
    "minimal": {
        "arm64": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-minimal-arm64.tar.xz",
                  "8dd42a9c8eb6cb7efcb169a6824b2cdc61ff0f999e87b30effa11832c528916e"),
        "armhf": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-minimal-armhf.tar.xz",
                  "709f131a7b8ca25073553b8ac8065cf9f9d113e764d1f5f4c03c54cb47fc4475"),
        "i386":  ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-minimal-i386.tar.xz",
                  "8c58f2330cbf926c70dd17e34bbaab6a5e0ab618841c948ca1f59e277bc99466"),
        "amd64": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-minimal-amd64.tar.xz",
                  "ae4040e0dc7c61171be8ec677fd92c3d22748cf23edd3e1f6d7d220c55897c09"),
    },
    "nano": {
        "arm64": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-nano-arm64.tar.xz",
                  "771f511202c28074a1756859ac8211bed9d85a1cf4eddba19416b12e05492d24"),
        "armhf": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-nano-armhf.tar.xz",
                  "ae1c75b78dd1c70f37fd748561a5272015a1ae054335d78de9f0a6ed49dc1bdb"),
        "i386":  ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-nano-i386.tar.xz",
                  "5f9f73583a4343f100bc1a6b7f10e5e123c8fcb5d028c2fbfaa25c31d137fd9a"),
        "amd64": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-nano-amd64.tar.xz",
                  "aa6f55cb5f7d39613d3af56d75b2373d0778a01e1db42b525a8e0c262bbfe808"),
    },
    "full": {
        "arm64": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-full-arm64.tar.xz",
                  "b7c60dd5a1db33b399afcecc40be39415f5593f7302b6573aece1265dae44d73"),
        "armhf": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-full-armhf.tar.xz",
                  "11ee09de068493a6f7a2c8f6b1e0d5a18cb3cc511f25aca7db99e1ede82c0e15"),
        "i386":  ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-full-i386.tar.xz",
                  "bcad19f1f2b68cdae0a6d773aa1fa21655e57889729c3e15b395d768ae0e33b7"),
        "amd64": ("https://old.kali.org/nethunter-images/kali-2025.3/rootfs/kali-nethunter-2025.3-rootfs-full-amd64.tar.xz",
                  "5ef7aebd3ac19ada2fdf8301d19096bc63f7e29c3aeb1d8b1b64491347e35c8d"),
    },
}

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

def verify_sha(file_path, expected_sha):
    info("Verifying SHA256...")
    # Avoid HTML/error downloads
    size = os.path.getsize(file_path)
    if size < 50_000_000:  # 50MB threshold
        err("Downloaded file too small; likely not a valid archive.")
        sys.exit(1)
    result = subprocess.run(f"sha256sum '{file_path}'", shell=True, capture_output=True, text=True)
    actual = result.stdout.strip().split()[0] if result.stdout else ""
    if actual != expected_sha:
        err("SHA mismatch!")
        sys.exit(1)
    ok("SHA256 matched.")

def extract_rootfs(archive_path, target_dir):
    info("Extracting rootfs...")
    os.makedirs(target_dir, exist_ok=True)
    run(f"proot --link2symlink tar -xf '{archive_path}' -C '{target_dir}' --strip-components=1")
    ok("Extraction complete.")

def banner():
    clear()
    time.sleep(0.5)
    art = """
███    ███ ██ ███████ ████████  █████  ██   ██ ███████  █████  ██████  ████████ ███████ 
████  ████ ██ ██         ██    ██   ██ ██   ██ ██      ██   ██ ██   ██    ██    ██      
██ ████ ██ ██ ███████    ██    ███████ ███████ █████   ███████ ██████     ██    ███████ 
██  ██  ██ ██      ██    ██    ██   ██ ██   ██ ██      ██   ██ ██         ██         ██ 
██      ██ ██ ███████    ██    ██   ██ ██   ██ ███████ ██   ██ ██         ██    ███████ 
    """
    print(Fore.YELLOW + Style.BRIGHT + art)
    print(Fore.GREEN + Style.BRIGHT + "MISTAKE619")

def main():
    clear()
    # Ensure deps
    info("Preparing environment (Termux)...")
    run("pkg update -y && pkg upgrade -y || true")
    run("pkg install -y wget proot tar || true")

    arch = get_arch()
    variant = ask_variant()
    url, sha = TARBALLS[variant][arch]
    filename = url.split("/")[-1]

    info(f"Downloading with wget: {filename}")
    run(f"wget -O '{filename}' '{url}'")

    verify_sha(filename, sha)
    extract_rootfs(filename, ROOTFS_DIR)
    banner()

if __name__ == "__main__":
    main()
