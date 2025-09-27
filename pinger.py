import argparse
import sys
import logging
from datetime import datetime

from colorama import Fore, Style, init
try:
    from tqdm import tqdm
    USE_TQDM = True
except ImportError:
    USE_TQDM = False

import pingcore

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(
    filename='ping_scan.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Ping multiple IP addresses concurrently.")
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
        ip_list = pingcore.parse_ip_range(args.ip_range)
    except Exception as e:
        print(f"{Fore.RED}Error parsing IP range: {e}{Style.RESET_ALL}")
        sys.exit(1)

    if not ip_list:
        print(f"{Fore.RED}No valid hosts found in the specified range.{Style.RESET_ALL}")
        sys.exit(1)

    print(f"Starting ping scan on {len(ip_list)} IPs with {args.workers} workers...")
    results = {}
    start_time = datetime.now()

    progress_iter = tqdm(ip_list, desc="Pinging") if USE_TQDM else ip_list

    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_ip = {executor.submit(pingcore.ping_ip, str(ip), args.count, args.timeout): str(ip) for ip in ip_list}
        completed = 0
        for future in as_completed(future_to_ip):
            ip = future_to_ip[future]
            try:
                loss = future.result()
            except Exception as exc:
                logging.error(f"Error pinging {ip}: {exc}")
                loss = 100
            pingcore.print_result(ip, loss)
            results[ip] = loss
            completed += 1
            if USE_TQDM:
                progress_iter.update(1)

    pingcore.print_summary(results)
    print(f"Elapsed time: {datetime.now() - start_time}")

    if args.output:
        pingcore.save_results(results, args.output)

if __name__ == "__main__":
    main()
