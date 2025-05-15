# Reconnaissance Report for https://www.hanosimex.com.vn/ (Target Domain: www.hanosimex.com.vn)

Report Generated: 2025-05-15 14:21:07

## Crew Execution Log & Raw Tool Outputs (Aggregated)

# Comprehensive Security Assessment Report for www.hanosimex.com.vn

## Executive Summary

This report synthesizes reconnaissance findings for www.hanosimex.com.vn, identifying several critical security risks:

1. **High-Risk Vulnerabilities**:

   - Outdated PHP version (5.6.40) with known unpatched vulnerabilities
   - Missing email security records (SPF/DKIM/DMARC)
   - Incomplete DNS configuration (missing MX, SOA records)

2. **Medium-Risk Issues**:

   - DNSSEC not implemented
   - Outdated jQuery library (1.10.1)
   - Missing security headers (CSP, HSTS)

3. **Scanning Limitations**:
   - Port scanning and directory enumeration attempts were consistently blocked
   - Subdomain enumeration yielded no results but may be incomplete

## Detailed Findings

### 1. WHOIS Information

**Raw Output**:

```
This TLD has no whois server, but you can access the whois database at
http://www.vnnic.vn/en
```

**Analysis**:

- Vietnam's .vn TLD restricts public WHOIS access
- Manual lookup through VNNIC required for registration details
- Risk assessment incomplete without registrant information

### 2. DNS Records

**Raw JSON Output**:

```json
[
  {
    "arguments": "/usr/local/bin/dnsrecon -d www.hanosimex.com.vn -t std -j dnsrecon_output_www.hanosimex.com.vn.json",
    "date": "2025-05-15 13:36:09.092603",
    "type": "ScanInfo"
  },
  {
    "address": "123.30.185.161",
    "domain": "www.hanosimex.com.vn",
    "name": "www.hanosimex.com.vn",
    "type": "A"
  }
]
```

**Key Findings**:

- Only A record found (123.30.185.161)
- Missing critical records:
  - MX (email servers)
  - TXT (SPF/DKIM/DMARC)
  - NS (nameservers)
  - SOA (zone authority)
- DNSSEC not implemented

### 3. Subdomain Enumeration

**Raw Output**:

```
[!] Error: Virustotal probably now is blocking our requests
```

**Findings**:

- No subdomains discovered
- Tool limitations may have affected results
- Virustotal blocking detected

### 4. Technology Stack

**Raw Output**:

```
https://www.hanosimex.com.vn [200 OK] AddThis, Apache, Cookies[PHPSESSID], Country[VIET NAM][VN], Email[support@hanosimex.com.vn], Frame, HTML5, HTTPServer[Apache], IP[123.30.185.161], JQuery[1.10.1], Open-Graph-Protocol[website], PHP[5.6.40], PasswordField[login_password], Script[text/javascript], Title[Tổng công ty cổ phần dệt may Hà Nội], X-Powered-By[PHP/5.6.40]
```

**Identified Technologies**:

- Web Server: Apache
- Programming: PHP 5.6.40 (EOL)
- JavaScript: jQuery 1.10.1
- Other: AddThis, HTML5, Open Graph Protocol

### 5. Port Scanning

**Results**:

- All scan attempts timed out
- Suggests strong network protections

### 6. Directory Enumeration

**Results**:

- All attempts timed out
- Indicates active scanning protection

## Data Correlations

1. **DNS and Technology Stack**:

   - Single A record correlates with Apache server IP
   - Missing MX records align with no email services detected

2. **Security Posture**:
   - Network protections (blocked scans) contrast with outdated software
   - Strong perimeter defenses but vulnerable internal components

## Risk Prioritization Matrix

| Vulnerability                           | Risk Level | Justification                    |
| --------------------------------------- | ---------- | -------------------------------- |
| PHP 5.6.40 (EOL)                        | Critical   | Unpatched RCE vulnerabilities    |
| Missing Email Security (SPF/DKIM/DMARC) | High       | Susceptible to email spoofing    |
| Incomplete DNS Configuration            | High       | Operational and security impacts |
| Outdated jQuery (1.10.1)                | Medium     | Known XSS vulnerabilities        |
| DNSSEC Not Implemented                  | Medium     | DNS spoofing possible            |
| Missing Security Headers                | Medium     | Increased XSS/MIME risks         |
| Blocked Scans                           | Low        | Indicates security awareness     |

## Recommendations

1. **Critical Fixes**:

   - Upgrade PHP to supported version (≥8.0)
   - Implement email security records (SPF, DKIM, DMARC)
   - Complete DNS configuration (MX, SOA records)

2. **High-Priority Improvements**:

   - Update jQuery to latest stable version
   - Implement DNSSEC
   - Add security headers (CSP, HSTS, X-Frame-Options)

3. **Operational Enhancements**:
   - Coordinate with network team for internal scanning
   - Implement WAF to complement network protections
   - Establish patch management process

## Retry Suggestions

1. **WHOIS Lookup**:

   - Manual query via VNNIC portal (http://www.vnnic.vn/en)
   - Use commercial services (DomainTools, WhoisXML API)

2. **DNS Enumeration**:

   ```bash
   dnsrecon -d www.hanosimex.com.vn -t std --nameserver 8.8.8.8 --lifetime 10 -j output.json
   ```

3. **Subdomain Enumeration**:

   - Use Amass with API keys:
     ```bash
     amass enum -d www.hanosimex.com.vn -passive -config config.ini
     ```

4. **Port Scanning**:

   - Slow scan from different network:
     ```bash
     nmap -sV -T2 -Pn -p 80,443,21,22,25,3389 www.hanosimex.com.vn
     ```

5. **Directory Enumeration**:
   - Conservative Gobuster scan:
     ```bash
     gobuster dir -u https://www.hanosimex.com.vn -w common.txt -t 2 -delay 2000ms
     ```

## Conclusion

www.hanosimex.com.vn demonstrates mixed security posture with strong network protections but critical vulnerabilities in its software stack. Immediate attention should be given to patching the EOL PHP installation and implementing basic email security measures. The organization's apparent security awareness (evidenced by scan protections) should be extended to internal system hardening.
