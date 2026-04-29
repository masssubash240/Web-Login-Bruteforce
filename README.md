# Web-Login-Bruteforce
# Web Login Brute‑Force Tool (Educational)
#  CYBER SUBASH- Tool development
A Python script to demonstrate how brute‑force attacks work against web login forms.  
**For authorized testing and educational purposes only.**

## Features

- Multi‑threading for speed
- Proxy support (HTTP/HTTPS/SOCKS)
- Configurable delay between attempts
- Flexible success detection (text, status code, redirect)
- Single username/password or wordlist mode
- Custom form field names
- Output file for valid credentials
- Logging of all attempts
- Colored output (if `colorama` is installed)

## Installation

```bash
# 1. Install required Python packages
sudo apt update
sudo apt install python3-pip -y
pip3 install requests colorama

# 2. Clone your repository (or manually copy the script)
git clone https://github.com/masssubash240/Web-Login-Bruteforce.git
cd Web-Login-Bruteforce

# 3. Make the script executable
chmod +x web-bruteforce.py

# 4. (Optional) Install as a system command
sudo cp web-bruteforce.py /usr/local/bin/passcrack
# Now you can run it from anywhere using: passcrack [options]

# 5. Test the tool
python3 web-bruteforce.py -h




---

## 4. Final Notes

- The script is **ready for Kali** – it runs without `sudo` unless you install it globally.
- The **logo** appears every time you run the tool (you can remove the `show_logo()` call if you prefer).
- For **CSRF tokens**, you’d need to modify the script to first GET the login page and extract the token – I can help with that if you want an advanced version.

Let me know if you want me to adjust the logo design or add any extra feature (e.g., CSRF token support, random User‑Agent rotation, or SOCKS5 proxy).
