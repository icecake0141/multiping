#!/usr/bin/env python3

import argparse
import queue
import shutil
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from scapy.all import ICMP, IP, sr

# A handler for command line options
def handle_options():

    parser = argparse.ArgumentParser(description="MultiPing - Perform ICMP ping operations to multiple hosts concurrently")
    parser.add_argument('-t', '--timeout', type=int, default=1, help='Timeout in seconds for each ping (default: 1)')
    parser.add_argument('-c', '--count', type=int, default=4, help='Number of ping attempts per host (default: 4)')
    parser.add_argument('--slow-threshold', type=float, default=0.5, help='Threshold in seconds for slow ping (default: 0.5)')
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
def ping_host(host, timeout, count, slow_threshold, verbose):
    """
    Ping a single host with the specified parameters.
    
    Args:
        host: The hostname or IP address to ping
        timeout: Timeout in seconds for each ping
        count: Number of ping attempts
        verbose: Whether to show detailed output
    
    Yields:
        A dict with host, sequence, status, and rtt
    """
    if verbose:
        print(f"\n--- Pinging {host} ---")

    for i in range(count):
        try:
            # Create ICMP packet
            icmp = IP(dst=host)/ICMP()
            
            # Send ICMP packet
            ans, unans = sr(icmp, timeout=timeout, verbose=0)

            if ans:
                sent, received = ans[0]
                rtt = received.time - sent.time
                status = "slow" if rtt >= slow_threshold else "success"
                if verbose:
                    print(f"Reply from {host}: seq={i+1} rtt={rtt:.3f}s")
                    for r in ans:
                        r[1].show()
                yield {"host": host, "sequence": i + 1, "status": status, "rtt": rtt}
            else:
                if verbose:
                    print(f"No reply from {host}: seq={i+1}")
                yield {"host": host, "sequence": i + 1, "status": "fail", "rtt": None}
        except OSError as e:
            if verbose:
                print(f"Network error pinging {host}: {e}")
            yield {"host": host, "sequence": i + 1, "status": "fail", "rtt": None}
        except Exception as e:
            if verbose:
                print(f"Error pinging {host}: {e}")
            yield {"host": host, "sequence": i + 1, "status": "fail", "rtt": None}

def compute_layout(hosts, header_lines=2):
    term_size = shutil.get_terminal_size(fallback=(80, 24))
    width = term_size.columns
    height = term_size.lines

    max_host_len = max((len(host) for host in hosts), default=4)
    label_width = min(max_host_len, max(10, width // 3))
    timeline_width = max(1, width - label_width - 3)
    visible_hosts = max(1, height - header_lines)

    return width, label_width, timeline_width, visible_hosts


def format_status_line(host, timeline, label_width):
    return f"{host:<{label_width}} | {timeline}"


def resize_buffers(buffers, timeline_width, symbols):
    for host, host_buffers in buffers.items():
        if host_buffers["timeline"].maxlen != timeline_width:
            host_buffers["timeline"] = deque(host_buffers["timeline"], maxlen=timeline_width)
        for status in symbols:
            if host_buffers["categories"][status].maxlen != timeline_width:
                host_buffers["categories"][status] = deque(
                    host_buffers["categories"][status], maxlen=timeline_width
                )


def render_display(hosts, buffers, stats, symbols, header_lines=2):
    width, label_width, timeline_width, visible_hosts = compute_layout(hosts, header_lines)
    truncated_hosts = hosts[:visible_hosts]

    resize_buffers(buffers, timeline_width, symbols)

    lines = []
    lines.append("MultiPing - Live results")
    lines.append("".join("-" for _ in range(width)))
    for host in truncated_hosts:
        timeline = "".join(buffers[host]["timeline"]).rjust(timeline_width)
        lines.append(format_status_line(host, timeline, label_width))

    if len(hosts) > len(truncated_hosts):
        remaining = len(hosts) - len(truncated_hosts)
        lines.append(f"... ({remaining} host(s) not shown)")

    print("\x1b[2J\x1b[H" + "\n".join(lines), end="", flush=True)


def worker_ping(host, timeout, count, slow_threshold, verbose, result_queue):
    for result in ping_host(host, timeout, count, slow_threshold, verbose):
        result_queue.put(result)
    result_queue.put({"host": host, "status": "done"})

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
    
    symbols = {"success": ".", "fail": "x", "slow": "!"}
    _, _, timeline_width, _ = compute_layout(all_hosts)
    buffers = {
        host: {
            "timeline": deque(maxlen=timeline_width),
            "categories": {status: deque(maxlen=timeline_width) for status in symbols},
        }
        for host in all_hosts
    }
    stats = {
        host: {"success": 0, "fail": 0, "slow": 0, "total": 0}
        for host in all_hosts
    }
    result_queue = queue.Queue()

    print(
        f"MultiPing - Pinging {len(all_hosts)} host(s) with timeout={args.timeout}s, "
        f"count={args.count}, slow-threshold={args.slow_threshold}s"
    )

    with ThreadPoolExecutor(max_workers=min(len(all_hosts), 10)) as executor:
        for host in all_hosts:
            executor.submit(
                worker_ping,
                host,
                args.timeout,
                args.count,
                args.slow_threshold,
                args.verbose,
                result_queue,
            )

        completed_hosts = 0
        render_display(all_hosts, buffers, stats, symbols)
        while completed_hosts < len(all_hosts):
            result = result_queue.get()
            host = result["host"]
            if result.get("status") == "done":
                completed_hosts += 1
                continue

            status = result["status"]
            buffers[host]["timeline"].append(symbols[status])
            buffers[host]["categories"][status].append(result["sequence"])
            stats[host][status] += 1
            stats[host]["total"] += 1
            render_display(all_hosts, buffers, stats, symbols)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for host in all_hosts:
        success = stats[host]["success"]
        slow = stats[host]["slow"]
        fail = stats[host]["fail"]
        total = stats[host]["total"]
        percentage = (success / total * 100) if total > 0 else 0
        status = "OK" if success > 0 else "FAILED"
        print(
            f"{host:30} {success}/{total} replies, {slow} slow, {fail} failed "
            f"({percentage:.1f}%) [{status}]"
        )

if __name__ == "__main__":
    # Handle command line options
    options = handle_options()
    main(options)
