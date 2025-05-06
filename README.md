# LAPTRINHMANG_UTE
network programming
WHOIS:
whois target.com > whois.txt
DNS Enumeration:
dnsrecon -d target.com -t std > dnsrecon.txt
Subdomain Enumeration:
python3 sublist3r.py -d target.com -o subdomains.txt
cat subdomains.txt | httprobe > live_subdomains.txt
Port Scanning:
nmap -sC -sV -p- -oN nmap_scan.txt target.com
Directory Enumeration:
gobuster dir -u https://target.com -w /usr/share/wordlists/dirb/common.txt -o gobuster.txt
Technology Stack:
whatweb -v target.com > whatweb.txt
Search engine: shodan
Wayback machine:
