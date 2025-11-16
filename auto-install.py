import os
import subprocess
import time
from colorama import init, Fore, Style

init(autoreset=True)

REPO_URL = "https://github.com/Endjustice/KALI.git"
CLONE_DIR = "KALI_repo"

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

def run_cmd(cmd):
    try: subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError: exit(1)

def main():
    clear()
    run_cmd(f"git clone {REPO_URL} {CLONE_DIR}")
    run_cmd(f"cd {CLONE_DIR} && bash install.sh")
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

if __name__ == "__main__":
    main()
