#!/usr/bin/env python3

import argparse
from concurrent.futures import ThreadPoolExecutor

from scapy.all import IP, ICMP, sr

# A handler for command line options
def handle_options():

    parser = argparse.ArgumentParser(description="MultiPing - Perform ICMP ping operations to multiple hosts concurrently")
    parser.add_argument('-t', '--timeout', type=int, default=1, help='Timeout in seconds for each ping (default: 1)')
    parser.add_argument('-c', '--count', type=int, default=4, help='Number of ping attempts per host (default: 4)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output, showing detailed ping results')
    parser.add_argument('-f', '--input', type=str, help='Input file containing list of hosts (one per line)', required=False)
    parser.add_argument('hosts', nargs='*', help='Hosts to ping (IP addresses or hostnames)')

    args = parser.parse_args()
    return args

# Read input file. The file contains a list of hosts (IP addresses or hostnames)
def read_input_file(input_file):

    host_list = []
    try:
        with open(input_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    host_list.append(line)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return []
    except PermissionError:
        print(f"Error: Permission denied reading file '{input_file}'.")
        return []
    except Exception as e:
        print(f"Error reading input file '{input_file}': {e}")
        return []

    return host_list

# Ping a single host
def ping_host(host, timeout, count, verbose):
    """
    Ping a single host with the specified parameters.
    
    Args:
        host: The hostname or IP address to ping
        timeout: Timeout in seconds for each ping
        count: Number of ping attempts
        verbose: Whether to show detailed output
    
    Returns:
        A tuple of (host, success_count, total_count)
    """
    success_count = 0
    
    if verbose:
        print(f"\n--- Pinging {host} ---")
    
    for i in range(count):
        try:
            # Create ICMP packet
            icmp = IP(dst=host)/ICMP()
            
            # Send ICMP packet
            ans, unans = sr(icmp, timeout=timeout, verbose=0)
            
            if ans:
                success_count += 1
                if verbose:
                    print(f"Reply from {host}: seq={i+1}")
                    for r in ans:
                        r[1].show()
            else:
                if verbose:
                    print(f"No reply from {host}: seq={i+1}")
        except OSError as e:
            if verbose:
                print(f"Network error pinging {host}: {e}")
        except Exception as e:
            if verbose:
                print(f"Error pinging {host}: {e}")
    
    return (host, success_count, count)

def main(args):

    # Validate count parameter
    if args.count <= 0:
        print("Error: Count must be a positive number.")
        return
    
    # Collect all hosts to ping
    all_hosts = []
    
    # Add hosts from command line arguments
    if args.hosts:
        all_hosts.extend(args.hosts)
    
    # Add hosts from input file if provided
    if args.input:
        file_hosts = read_input_file(args.input)
        all_hosts.extend(file_hosts)
    
    # Check if we have any hosts to ping
    if not all_hosts:
        print("Error: No hosts specified. Provide hosts as arguments or use -f/--input option.")
        return
    
    print(f"MultiPing - Pinging {len(all_hosts)} host(s) with timeout={args.timeout}s, count={args.count}")
    print("-" * 60)
    
    # Ping all hosts concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=min(len(all_hosts), 10)) as executor:
        futures = [
            executor.submit(ping_host, host, args.timeout, args.count, args.verbose)
            for host in all_hosts
        ]
        
        # Collect results
        results = [future.result() for future in futures]
    
    # Display summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for host, success, total in results:
        percentage = (success / total * 100) if total > 0 else 0
        status = "OK" if success > 0 else "FAILED"
        print(f"{host:30} {success}/{total} replies ({percentage:.1f}%) [{status}]")

if __name__ == "__main__":
    # Handle command line options
    options = handle_options()
    main(options)