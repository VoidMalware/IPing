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
from typing import Generator, Dict

try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(
    filename='ping_scan.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ping_ip(ip: str, count: int = 4, timeout: int = 1000) -> int:
    """
    Ping an IP address (IPv4 or IPv6) and return packet loss percentage.
    """
    system = platform.system().lower()
    is_ipv6 = ':' in str(ip)

    if system == 'windows':
        param = '-n'
        timeout_param = '-w'
        timeout_val = str(timeout)
        command = ['ping', param, str(count), timeout_param, timeout_val, str(ip)]
    else:
        param = '-c'
        timeout_param = '-W'
        timeout_val = str(max(1, int(timeout / 1000)))
        if is_ipv6:
            command = ['ping6', param, str(count), timeout_param, timeout_val, str(ip)]
        else:
            command = ['ping', param, str(count), timeout_param, timeout_val, str(ip)]

    logging.debug(f"Pinging {ip} with command: {' '.join(command)}")

    try:
        output = subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=(count * (timeout / 1000 + 1))
        )
        logging.debug(f"Ping output for {ip}:\n{output}")

        if system == 'windows':
            match = re.search(r"Lost = \d+ \((\d+)% loss\)", output)
        else:
            match = re.search(r"(\d+)% packet loss", output)

        if match:
            loss = int(match.group(1))
            return loss
    except subprocess.CalledProcessError as e:
        logging.error(f"Ping failed for {ip}: {e}")
    except subprocess.TimeoutExpired:
        logging.error(f"Ping timed out for {ip}")
    except Exception as e:
        logging.error(f"Unexpected error pinging {ip}: {e}")

    logging.warning(f"Assuming 100% loss for {ip}")
    return 100

def print_result(ip: str, loss: int) -> None:
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

def parse_ip_range(ip_range_str: str) -> Generator[ipaddress._BaseAddress, None, None]:
    """
    Generator for IP range string: 'start-end' or CIDR.
    Yields IP addresses without storing them all in memory.
    """
    ip_range_str = ip_range_str.strip()
    if '-' in ip_range_str:
        start_str, end_str = ip_range_str.split('-')
        start_ip = ipaddress.ip_address(start_str.strip())
        end_ip = ipaddress.ip_address(end_str.strip())
        if start_ip.version != end_ip.version:
            raise ValueError("Start and end IP must be of the same version")
        if int(end_ip) < int(start_ip):
            raise ValueError("End IP must be >= start IP")
        current = int(start_ip)
        while current <= int(end_ip):
            yield ipaddress.ip_address(current)
            current += 1
    else:
        net = ipaddress.ip_network(ip_range_str, strict=False)
        for host in net.hosts():
            yield host

def save_results(results: Dict[str, int], output_file: str) -> None:
    try:
        with open(output_file, 'w') as f:
            f.write(f"Ping scan results - {datetime.now()}\n")
            for ip, loss in results.items():
                if loss == 0:
                    status = "Success"
                elif loss < 100:
                    status = f"Partial ({loss}%)"
                else:
                    status = "Failed"
                f.write(f"{ip} - {status}\n")
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"{Fore.RED}Failed to write output file: {e}{Style.RESET_ALL}")

def print_summary(results: Dict[str, int]) -> None:
    success_count = sum(1 for loss in results.values() if loss == 0)
    partial_count = sum(1 for loss in results.values() if 0 < loss < 100)
    failed_count = sum(1 for loss in results.values() if loss == 100)
    print("\nScan Summary:")
    print(f"{Fore.GREEN}Success: {success_count}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Partial: {partial_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {failed_count}{Style.RESET_ALL}")

def main():
    parser = argparse.ArgumentParser(description="Ping multiple IP addresses concurrently (memory safe).")
    parser.add_argument('ip_range', help="IP range to scan. Format: startIP-endIP or CIDR (e.g. 192.168.1.1-192.168.1.10 or 192.168.1.0/28)")
    parser.add_argument('-c', '--count', type=int, default=4, help="Number of ping packets to send (default: 4)")
    parser.add_argument('-t', '--timeout', type=int, default=1000, help="Timeout per ping in milliseconds (default: 1000)")
    parser.add_argument('-w', '--workers', type=int, default=20, help="Number of concurrent workers (default: 20)")
    parser.add_argument('-o', '--output', type=str, help="Output file to save results")
    args = parser.parse_args()

    if args.count <= 0 or args.timeout <= 0 or args.workers <= 0:
        print(f"{Fore.RED}Count, timeout, and workers must be positive integers.{Style.RESET_ALL}")
        sys.exit(1)

    try:
        ip_iter = parse_ip_range(args.ip_range)  # generator
    except Exception as e:
        print(f"{Fore.RED}Error parsing IP range: {e}{Style.RESET_ALL}")
        sys.exit(1)

    print(f"Starting ping scan with {args.workers} workers...")
    results = {}
    start_time = datetime.now()

    if USE_TQDM:
        ip_iter = tqdm(ip_iter, desc="Pinging")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_ip = {executor.submit(ping_ip, str(ip), args.count, args.timeout): str(ip) for ip in ip_iter}
        for future in concurrent.futures.as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                loss = future.result()
            except Exception as exc:
                logging.error(f"Error pinging {ip}: {exc}")
                loss = 100
            print_result(ip, loss)
            results[ip] = loss

    print_summary(results)
    print(f"Elapsed time: {datetime.now() - start_time}")

    if args.output:
        save_results(results, args.output)

if __name__ == "__main__":
    main()
