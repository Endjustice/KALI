import os
import re
import sys
import time
import shutil
import subprocess
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from colorama import init, Fore, Style

init(autoreset=True)

# Mirrors and endpoints
MIRRORS = [
    "https://kali.download/nethunter-images",
    "https://old.kali.org/nethunter-images"
]

# Desired variant & arch
VARIANT = "full"       # full | minimal | nano
ARCH   = "arm64"       # arm64 | armhf

ROOTFS_DIR = "/data/data/com.termux/files/kali"
CLONE_DIR  = "kali_repo"

def info(msg): print(Fore.CYAN   + "[INFO]"  + Style.RESET_ALL, msg)
def ok(msg):   print(Fore.GREEN  + "[OK]"    + Style.RESET_ALL, msg)
def err(msg):  print(Fore.RED    + "[ERROR]" + Style.RESET_ALL, msg)
def warn(msg): print(Fore.YELLOW + "[WARN]"  + Style.RESET_ALL, msg)

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

def http_head(url):
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as r:
            size = int(r.headers.get("Content-Length", "0"))
            return r.status, size
    except (HTTPError, URLError) as e:
        return None, 0

def http_get(url):
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req) as r:
            return r.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError):
        return None

def run(cmd):
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        err(f"Command failed: {cmd}")
        sys.exit(1)

def detect_latest_version():
    # Try finding latest “kali-YYYY.X” directory with rootfs/
    pattern = re.compile(r'href="kali-(\d{4}\.\d+)/"', re.I)
    for base in MIRRORS:
        index_html = http_get(base + "/")
        if not index_html: continue
        versions = pattern.findall(index_html)
        # Sort lexicographically which works for YYYY.X
        for ver in sorted(set(versions), reverse=True):
            status, _ = http_head(f"{base}/kali-{ver}/rootfs/")
            if status == 200:
                ok(f"Detected version: {ver} at {base}")
                return base, ver
    err("Failed to detect latest NetHunter rootfs version.")
    sys.exit(1)

def build_archive_name(variant, arch):
    # minimal vs mini mapping
    v = variant.replace("mini", "minimal")
    return f"kali-nethunter-rootfs-{v}-{arch}.tar.xz"

def fetch_sha256(base, version, archive_name):
    sha_url = f"{base}/kali-{version}/rootfs/SHA256SUMS"
    info(f"Fetching checksums: {sha_url}")
    content = http_get(sha_url)
    if not content:
        err("Unable to download SHA256SUMS.")
        sys.exit(1)
    # Lines like: <sha>  kali-nethunter-rootfs-full-arm64.tar.xz
    for line in content.splitlines():
        line = line.strip()
        if line.endswith(archive_name):
            sha = line.split()[0]
            ok("Matched SHA256 from official list.")
            return sha
    err("Archive name not found in SHA256SUMS.")
    sys.exit(1)

def download_archive(url, out_name):
    info(f"Downloading archive: {url}")
    status, size = http_head(url)
    if status != 200 or size < 50_000_000:
        err("Archive not available or too small (likely HTML/error).")
        sys.exit(1)
    run(f"curl -fL --retry 3 --retry-delay 2 -o '{out_name}' '{url}'")
    if os.path.getsize(out_name) < size * 0.9:
        warn("Downloaded size is smaller than expected head size.")

def verify_sha(file_path, expected_sha):
    info("Verifying SHA256 checksum...")
    result = subprocess.run(f"sha256sum '{file_path}'", shell=True, capture_output=True, text=True)
    actual = result.stdout.strip().split()[0] if result.stdout else ""
    if actual != expected_sha:
        err("SHA mismatch!")
        sys.exit(1)
    ok("SHA256 verified.")

def extract_rootfs(archive_path, target_dir):
    info("Extracting rootfs...")
    os.makedirs(target_dir, exist_ok=True)
    # Use proot to avoid symlink issues in Termux
    run(f"proot --link2symlink tar -xf '{archive_path}' -C '{target_dir}' --strip-components=1")
    ok("Extraction complete.")

def configure_locale(target_dir):
    locale_gen = os.path.join(target_dir, "etc/locale.gen")
    if os.path.exists(locale_gen):
        info("Configuring locale...")
        run(f"sed -i 's/^# *en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' '{locale_gen}'")
        run(f"proot -0 -r '{target_dir}' /sbin/dpkg-reconfigure locales")
        ok("Locale configured.")

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
    # Optional: update Termux first
    info("Updating Termux packages...")
    run("pkg update -y && pkg upgrade -y || true")
    # Ensure curl, proot, tar
    info("Installing dependencies...")
    run("pkg install -y curl proot tar || true")

    # Detect latest version and build URLs
    base, version = detect_latest_version()
    archive_name = build_archive_name(VARIANT, ARCH)
    archive_url  = f"{base}/kali-{version}/rootfs/{archive_name}"

    # Fetch correct SHA for this archive
    sha_expected = fetch_sha256(base, version, archive_name)

    # Download and verify
    download_archive(archive_url, archive_name)
    verify_sha(archive_name, sha_expected)

    # Extract and basic config
    extract_rootfs(archive_name, ROOTFS_DIR)
    configure_locale(ROOTFS_DIR)

    # Optional: add nh shortcut (if termux-distro not present)
    # You can customize this part or leave it minimal

    banner()

if __name__ == "__main__":
    try:
        main()
    finally:
        # Cleanup (optional)
        pass
