# Welcome to IPing

IPing is a fast and easy-to-use multi-IP ping scanner. Quickly scan entire ranges or networks right from your terminal. Whether you are a network administrator, security professional, or just want to check which devices are online, IPing makes the process simple.

---

## Quick Start

### 1. Clone the Repository

```sh
git clone https://github.com/VoidMalware/IPing.git
cd IPing
```

### 2. Install Requirements

Make sure you have Python 3.7 or later.

Install required dependencies:

```sh
pip install -r requirements.txt
```

If you just need the basics:

```sh
pip install colorama
```

For a progress bar (optional but recommended):

```sh
pip install tqdm
```

### 3. Run Your First Scan

You can scan a range or an entire subnet using either dash or CIDR notation:

```sh
python pinger.py 192.168.1.1-192.168.1.10
```

or

```sh
python pinger.py 192.168.1.0/28
```

---

## Usage and Options

Basic usage:

```sh
python pinger.py <IP_RANGE> [options]
```

Examples:

- Scan a range:
  ```sh
  python pinger.py 10.0.0.1-10.0.0.100
  ```
- Scan a subnet:
  ```sh
  python pinger.py 192.168.0.0/24
  ```
- Save results to a file:
  ```sh
  python pinger.py 192.168.1.0/28 -o results.txt
  ```
- Change ping count, timeout, or worker threads:
  ```sh
  python pinger.py 10.0.0.1-10.0.0.10 -c 2 -t 500 -w 10
  ```

Options:

- `-c, --count` : Number of ping packets per host (default: 4)
- `-t, --timeout` : Timeout per ping in milliseconds (default: 1000)
- `-w, --workers` : Number of concurrent workers (default: 20)
- `-o, --output` : Save results to a file

---

## Additional Information

- Results are color-coded and summarized automatically in your terminal.
- Logs are saved in `ping_scan.log` for troubleshooting.
- Cross-platform: works on Windows, Linux, and macOS.

---

## Need Help?

- If you find a bug or have a feature request, open an issue on GitHub or join our discord server, link will be below.
- Contributions and pull requests are welcome.

---
# Notes

For the best experience, install tqdm for a progress bar:

```sh
pip install tqdm
```

Also make sure to join our discord server and get updated once a new repository or project is out or in development!
```
https://discord.gg/r89mbJH232
```
---

Happy scanning.
