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
    names = [
        f"kali-nethunter-rootfs-{variant}-{arch}.tar.xz",
        f"kali-nethunter-2025.3-rootfs-{variant}-{arch}.tar.xz",
    ]
    for name in names:
        url = f"{BASE_URL}/{name}"
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
    run(f"wget --no-check-certificate --continue -O '{filename}' '{url}'")
    size = os.path.getsize(filename)
    if size < 50_000_000:
        err("Downloaded file too small; likely HTML/error instead of archive.")
        sys.exit(1)

def extract_rootfs(archive_path, target_dir):
    info("Extracting rootfs (excluding dev/proc/sys/tmp)...")
    os.makedirs(target_dir, exist_ok=True)
    run(
        f"proot --link2symlink tar -xpf '{archive_path}' -C '{target_dir}' "
        f"--exclude='dev/*' --exclude='proc/*' --exclude='sys/*' --exclude='tmp/*' "
        f"--strip-components=1"
    )
    ok("Extraction complete.")

def post_extract_fixups(target_dir):
    info("Applying post-extract fixups...")
    for d in ["dev", "proc", "sys", "tmp", "var/tmp", "root"]:
        os.makedirs(os.path.join(target_dir, d), exist_ok=True)
    bin_path = os.path.join(target_dir, "bin")
    sbin_path = os.path.join(target_dir, "sbin")
    usr_bin = os.path.join(target_dir, "usr", "bin")
    usr_sbin = os.path.join(target_dir, "usr", "sbin")
    if not os.path.exists(bin_path) and os.path.isdir(usr_bin):
        run(f"ln -sf 'usr/bin' '{bin_path}'")
    if not os.path.exists(sbin_path) and os.path.isdir(usr_sbin):
        run(f"ln -sf 'usr/sbin' '{sbin_path}'")
    for sh in ["bin/bash", "usr/bin/bash", "bin/sh", "usr/bin/sh"]:
        p = os.path.join(target_dir, sh)
        if os.path.exists(p):
            run(f"chmod +x '{p}'")
    ok("Fixups applied.")

def write_launcher(target_dir):
    info("Writing launcher 'nh'...")
    launcher = os.path.expanduser("~/../usr/bin/nh")
    os.makedirs(os.path.dirname(launcher), exist_ok=True)
    script = f"""#!/data/data/com.termux/files/usr/bin/bash
SHELL="/bin/bash"
[ -x "{target_dir}/bin/bash" ] || [ -x "{target_dir}/usr/bin/bash" ] || SHELL="/bin/sh"

exec proot \\
  -S "{target_dir}" \\
  -b /dev -b /proc -b /sys \\
  -b "$TMPDIR":/tmp \\
  -w /root \\
  --link2symlink --kill-on-exit \\
  "$SHELL" -l
"""
    with open(launcher, "w") as f:
        f.write(script)
    run(f"chmod +x '{launcher}'")
    ok("Launcher installed. Run: nh")

def banner():
    clear()
    print(Fore.GREEN + Style.BRIGHT + "\n" + "="*60)
    print(Fore.YELLOW + Style.BRIGHT + "           MISTAKE619 INSTALLATION COMPLETE")
    print(Fore.GREEN + Style.BRIGHT + "="*60 + "\n")

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
    post_extract_fixups(ROOTFS_DIR)
    write_launcher(ROOTFS_DIR)
    banner()
    ok("Installation completed! You can now run 'nh' to start Kali Nethunter")

if __name__ == "__main__":
    main()
