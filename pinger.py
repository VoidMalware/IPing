import subprocess
import platform
import ipaddress
import argparse
import concurrent.futures
import re
import sys
from datetime import datetime
from colorama import Fore, Style, init
import logging

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(filename='ping_scan.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def ping_ip(ip, count=4, timeout=1000):
    """
    Ping an IP address and return the packet loss percentage.
    """
    system = platform.system().lower()
    if system == 'windows':
        param = '-n'
        timeout_param = '-w'  # timeout in milliseconds per ping
        timeout_val = str(timeout)
    else:
        param = '-c'
        timeout_param = '-W'  # timeout in seconds per ping
        # Convert milliseconds to seconds rounded up
        timeout_val = str(max(1, int(timeout / 1000)))

    command = ['ping', param, str(count), timeout_param, timeout_val, str(ip)]
    logging.debug(f"Pinging {ip} with command: {' '.join(command)}")

    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True, timeout=(count * (timeout/1000 + 1)))
        logging.debug(f"Ping output for {ip}:\n{output}")

        if system == 'windows':
            # Regex to find packet loss percentage
            match = re.search(r"Lost = \d+ \((\d+)% loss\)", output)
            if match:
                loss = int(match.group(1))
                return loss
        else:
            # Regex to find packet loss percentage
            match = re.search(r"(\d+)% packet loss", output)
            if match:
                loss = int(match.group(1))
                return loss
    except subprocess.CalledProcessError as e:
        logging.error(f"Ping failed for {ip}: {e}")
        return 100
    except subprocess.TimeoutExpired:
        logging.error(f"Ping timed out for {ip}")
        return 100
    except Exception as e:
        logging.error(f"Unexpected error pinging {ip}: {e}")
        return 100

    # If parsing failed, assume 100% loss
    logging.warning(f"Could not parse ping output for {ip}, assuming 100% loss")
    return 100

def print_result(ip, loss):
    if loss == 0:
        color = Fore.GREEN
        status = "Success"
    elif 0 < loss < 100:
        color = Fore.YELLOW
        status = f"Partial ({loss}% loss)"
    else:
        color = Fore.RED
        status = "Failed"
    print(f"{color}{ip} - {status}{Style.RESET_ALL}")

def parse_ip_range(ip_range_str):
    """
    Parse IP range string in format 'start-end' or CIDR notation.
    Returns a list of IP addresses.
    """
    if '-' in ip_range_str:
        start_str, end_str = ip_range_str.split('-')
        start_ip = ipaddress.ip_address(start_str.strip())
        end_ip = ipaddress.ip_address(end_str.strip())
        if start_ip.version != end_ip.version:
            raise ValueError("Start and end IP must be of the same version")
        if int(end_ip) < int(start_ip):
            raise ValueError("End IP must be greater than or equal to start IP")
        return [ipaddress.ip_address(ip) for ip in range(int(start_ip), int(end_ip) + 1)]
    else:
        # Assume CIDR notation
        net = ipaddress.ip_network(ip_range_str, strict=False)
        return list(net.hosts())

def main():
    parser = argparse.ArgumentParser(description="Ping multiple IP addresses concurrently.")
    parser.add_argument('ip_range', help="IP range to scan. Format: startIP-endIP or CIDR (e.g. 192.168.1.1-192.168.1.10 or 192.168.1.0/28)")
    parser.add_argument('-c', '--count', type=int, default=4, help="Number of ping packets to send (default: 4)")
    parser.add_argument('-t', '--timeout', type=int, default=1000, help="Timeout per ping in milliseconds (default: 1000)")
    parser.add_argument('-w', '--workers', type=int, default=20, help="Number of concurrent workers (default: 20)")
    parser.add_argument('-o', '--output', type=str, help="Output file to save results")
    args = parser.parse_args()

    try:
        ip_list = parse_ip_range(args.ip_range)
    except Exception as e:
        print(f"{Fore.RED}Error parsing IP range: {e}{Style.RESET_ALL}")
        sys.exit(1)

    print(f"Starting ping scan on {len(ip_list)} IPs with {args.workers} workers...")

    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_ip = {executor.submit(ping_ip, ip, args.count, args.timeout): ip for ip in ip_list}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_ip), 1):
            ip = future_to_ip[future]
            try:
                loss = future.result()
            except Exception as exc:
                logging.error(f"Error pinging {ip}: {exc}")
                loss = 100
            print_result(ip, loss)
            results[str(ip)] = loss

    # Summary
    success_count = sum(1 for loss in results.values() if loss == 0)
    partial_count = sum(1 for loss in results.values() if 0 < loss < 100)
    failed_count = sum(1 for loss in results.values() if loss == 100)

    print("\nScan Summary:")
    print(f"{Fore.GREEN}Success: {success_count}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Partial: {partial_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {failed_count}{Style.RESET_ALL}")

    if args.output:
        try:
            with open(args.output, 'w') as f:
                f.write(f"Ping scan results - {datetime.now()}\n")
                for ip, loss in results.items():
                    status = "Success" if loss == 0 else f"Partial ({loss}%)" if loss < 100 else "Failed"
                    f.write(f"{ip} - {status}\n")
            print(f"Results saved to {args.output}")
        except Exception as e:
            print(f"{Fore.RED}Failed to write output file: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
  
