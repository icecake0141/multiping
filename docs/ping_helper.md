<!--
Copyright 2025 icecake0141
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Review required for correctness, security, and licensing.
-->

# ping_helper Documentation

## Overview

`ping_helper` is a minimal, capability-based ICMP ping utility written in C. It sends a single ICMP echo request and waits for a reply, printing the round-trip time (RTT) and TTL on success or exiting with a specific error code on failure.

## Design Philosophy

The helper is intentionally minimal and designed to run with `cap_net_raw` capability (on Linux) rather than requiring root privileges for the entire application. Each invocation:
- Sends exactly **one ICMP echo request**
- Waits for a matching reply or times out
- Exits immediately after receiving a valid reply or on timeout/error

This design is optimized for **one helper process per ping**, which is the current usage pattern in ParaPing.

## Command-Line Interface

### Usage

```bash
ping_helper <host> <timeout_ms> [icmp_seq]
```

### Arguments

- `<host>` (required): Hostname or IPv4 address to ping
- `<timeout_ms>` (required): Timeout in milliseconds (1-60000)
- `[icmp_seq]` (optional): ICMP sequence number (0-65535, default: 1)

### Examples

```bash
# Basic ping with 1 second timeout (default icmp_seq=1)
./ping_helper google.com 1000

# Ping with custom sequence number
./ping_helper 8.8.8.8 2000 42

# Ping with minimum timeout
./ping_helper 1.1.1.1 100 1
```

## Output Format

### Success

On successful ping, the helper outputs to stdout:

```
rtt_ms=<value> ttl=<value>
```

Where:
- `rtt_ms`: Round-trip time in milliseconds (floating-point, 3 decimal places)
- `ttl`: Time-to-live from the IP header of the reply (integer)

**Example:**
```
rtt_ms=12.345 ttl=64
```

### Timeout

On timeout (no reply received within timeout_ms), the helper:
- Outputs nothing to stdout
- Exits with code **7**

### Errors

On errors, the helper:
- Outputs an error message to stderr
- Exits with a non-zero, non-7 exit code

## Exit Codes

| Code | Meaning | Notes |
|------|---------|-------|
| 0 | Success | Valid reply received |
| 1 | Invalid arguments | Wrong number of arguments |
| 2 | Argument validation error | Invalid timeout_ms or icmp_seq |
| 3 | Host resolution failed | Cannot resolve hostname |
| 4 | Socket error | Cannot create socket or insufficient privileges |
| 5 | Send error | Failed to send ICMP packet |
| 6 | Select error | Internal select() failure |
| 7 | **Timeout** | No reply within timeout_ms |
| 8 | Receive error | Failed to receive packet |

**Exit code 7 is reserved exclusively for timeouts** and should be treated as "no response" rather than an error.

## Packet Validation

The helper implements robust packet validation to avoid misattribution and handle corrupt packets:

### Reply Matching Criteria

A received packet is considered a valid reply only if **all** of these conditions are met:

1. **Minimum packet size**: At least 20 bytes (minimal IP header)
2. **IP header validation**:
   - IP header length between 20-60 bytes
   - IP version is 4
   - IP protocol is ICMP (1)
3. **ICMP header validation**:
   - Packet is long enough for IP header + 8-byte ICMP header
   - ICMP type is ECHOREPLY (0)
   - ICMP code is 0
4. **Identity matching**:
   - ICMP ID matches `getpid() & 0xFFFF`
   - ICMP sequence number matches the sent sequence
   - Source IP address matches the destination we sent to

Packets that don't match **any** of these criteria are silently discarded, and the helper continues waiting for a valid reply until timeout.

### Defense Against Edge Cases

- **Short packets**: Validated before accessing any fields
- **Corrupt IP headers**: Header length bounds-checked
- **Wrong protocol**: IP protocol field validated
- **Other processes' pings**: ID and sequence number filtering
- **Replies from wrong hosts**: Source address validation

## Assumptions and Limitations

### Current Design Assumptions

1. **One request per process**: Each helper instance sends exactly one ICMP echo request
2. **Process ID as identifier**: Uses `getpid() & 0xFFFF` for ICMP ID
   - Collision possible if multiple helpers run with recycled PIDs
   - Mitigated by sequence number matching and source address validation
3. **IPv4 only**: No IPv6 support
4. **Single host**: Each invocation targets exactly one host
5. **No retries**: Does not retry on packet loss; exits with timeout

### Safe Usage Constraints

- **One helper per ping**: Do not attempt to reuse a single helper process for multiple pings
- **Sequential invocations**: If running multiple helpers with the same host, ensure different sequence numbers or stagger timing to avoid ID collisions
- **Capability-based security (Linux)**: Use `cap_net_raw` on the binary, **never** on interpreters
- **Platform-specific**: Optimized for Linux; macOS/BSD may require different privilege handling

### Multi-Process and Batch Scenarios

When running multiple ping_helper processes concurrently (e.g., monitoring many hosts):

**Recommended practices:**
- Use different `icmp_seq` values for concurrent pings to the same host to avoid reply confusion
- Monitor system limits: check file descriptor limits (`ulimit -n`) and ICMP rate limits
- Consider process spawn overhead (~1-5ms per invocation) in high-frequency scenarios

**Example: Monitoring multiple hosts in parallel**
```bash
# Ping multiple hosts with unique sequence numbers
./ping_helper 8.8.8.8 1000 1 &
./ping_helper 1.1.1.1 1000 2 &
./ping_helper 9.9.9.9 1000 3 &
wait
```

**Example: Sequential pings with controlled sequence numbers**
```bash
# Useful for scripted monitoring loops
for i in {1..10}; do
  ./ping_helper example.com 1000 $i
  sleep 1
done
```

### Known Limitations

1. **Fixed packet size**: Uses 64-byte packets (cannot be configured)
2. **No payload customization**: Sends zero-filled payload
3. **No ICMP filtering on non-Linux**: `ICMP_FILTER` socket option is Linux-specific
4. **Process ID wrap**: Very long-running systems with rapid process creation might see PID recycling
5. **Process spawn overhead**: Each invocation creates a new process; not optimized for sub-millisecond intervals

## Security Considerations

### Privilege Separation

The helper is designed for **capability-based privilege separation**:

```bash
# Build and set capabilities (Linux)
make build
sudo make setcap

# Verify capabilities
getcap ping_helper
# Output: ping_helper = cap_net_raw+ep
```

**Never** grant `cap_net_raw` to Python interpreters or other general-purpose tools.

### Input Validation

All inputs are validated:
- Hostname: Resolved via `getaddrinfo()` with proper error handling
- `timeout_ms`: Range-checked (1-60000), validated as integer
- `icmp_seq`: Range-checked (0-65535), validated as integer

### Attack Surface

The helper:
- Does **not** parse user-controlled data from packets (beyond standard headers)
- Does **not** allocate based on packet contents
- Does **not** perform unbounded operations
- Implements **strict bounds checking** on all packet field access

## Future Extension Points

While the helper is intentionally minimal, potential future enhancements include:

1. **Configurable packet size**: Add optional argument for packet size
2. **Multiple requests**: Support sending multiple pings in one invocation (batch mode)
3. **IPv6 support**: Dual-stack ping capability
4. **Payload patterns**: Customizable payload for detecting corruption
5. **Statistics mode**: Send multiple pings and output aggregate stats
6. **Raw output mode**: Include full ICMP header details in output
7. **Persistent worker mode**: Accept multiple ping requests without process restart
8. **Shared socket pool**: Reuse raw sockets for multiple pings to reduce overhead

**Performance-oriented extensions:**
- **Batch mode example**: `./ping_helper --batch hosts.txt` to ping multiple hosts in one process
- **Persistent worker**: Helper accepts commands via stdin for rapid-fire pings without spawn overhead
- **Output streaming**: JSON-lines format for programmatic consumption

**Note**: Any extensions must maintain backward compatibility with the current CLI contract.

## Troubleshooting

### Common Issues and Solutions

#### Exit Code 4: Socket Error / Insufficient Privileges

**Symptoms:**
```
Error: cannot create raw socket: Operation not permitted
Note: This program requires cap_net_raw capability or root privileges
```

**Solutions:**
1. Verify capabilities are set (Linux):
   ```bash
   getcap ./ping_helper
   # Should show: ping_helper = cap_net_raw+ep
   ```

2. Re-set capabilities if missing:
   ```bash
   sudo make setcap
   ```

3. Verify the binary hasn't been moved or rebuilt (capabilities are per-inode)

4. On non-Linux systems, run with `sudo` or set setuid bit (not recommended)

#### Exit Code 7: Timeout (Not an Error)

**Symptoms:**
- No output on stdout
- Exit code 7

**Context:**
Exit code 7 is **not an error**; it indicates a normal timeout (no ICMP reply received within timeout_ms). This is expected behavior when:
- Target host is unreachable or firewalled
- Network is experiencing packet loss
- Timeout is too short for the network conditions

**Solutions:**
- Increase `timeout_ms` value if network RTT is high
- Verify target host is reachable: `ping <host>` (using system ping)
- Check firewall rules blocking ICMP

#### Exit Code 2: Argument Validation Error

**Symptoms:**
```
Error: timeout_ms must be positive
Error: icmp_seq must be between 0 and 65535
```

**Solutions:**
- Verify arguments are integers in valid ranges:
  - `timeout_ms`: 1-60000 milliseconds
  - `icmp_seq`: 0-65535 (optional, default: 1)
- Check for typos or invalid characters in arguments

#### Exit Code 3: Host Resolution Failed

**Symptoms:**
```
Error: cannot resolve host example.invalid: Name or service not known
```

**Solutions:**
- Verify hostname is correct and resolvable: `nslookup <host>`
- Check DNS configuration: `/etc/resolv.conf`
- Use IP address directly to bypass DNS

#### Unexpected Timeouts Under High Load

**Symptoms:**
- Frequent exit code 7 when monitoring many hosts concurrently
- Timeouts on hosts that normally respond quickly

**Possible Causes and Solutions:**
1. **Kernel ICMP rate limiting**:
   ```bash
   # Check current limits (Linux)
   sysctl net.ipv4.icmp_ratelimit
   # Increase limit if needed (requires root)
   sudo sysctl -w net.ipv4.icmp_ratelimit=100
   ```

2. **File descriptor limits**:
   ```bash
   ulimit -n  # Check current limit
   ulimit -n 4096  # Increase limit
   ```

3. **Socket buffer drops** (check system logs):
   ```bash
   # Increase system-wide socket buffer limits (Linux)
   sudo sysctl -w net.core.rmem_max=8388608
   ```

4. **Process spawn overhead**: Consider increasing ping intervals or reducing concurrent host count

## Implementation Details

### Socket Configuration

- **Type**: `SOCK_RAW` with `IPPROTO_ICMP`
- **Connected socket**: Calls `connect()` to filter packets to target host only
- **Receive buffer**: Increased to 256KB to reduce drops under high ICMP volume
- **ICMP filter** (Linux only): Filters to accept only ECHOREPLY packets

### Time Handling

- Uses `gettimeofday()` for microsecond-precision timestamps
- Calculates absolute deadline to avoid time-drift in select() loop
- Recalculates remaining time on each iteration

### Checksum Calculation

Implements standard RFC 1071 Internet checksum:
- 16-bit one's complement sum
- Handles odd-length data correctly

## Testing

The helper is tested via:

1. **Python wrapper tests** (`tests/test_ping_wrapper.py`): Integration tests via `ping_wrapper.py`
2. **Contract tests** (`tests/test_ping_helper_contract.py`): CLI contract verification
   - Output format parsing
   - Exit code behavior
   - Argument validation
   - Error message format

Run tests:
```bash
python3 -m pytest tests/test_ping_wrapper.py tests/test_ping_helper_contract.py -v
```

## References

- RFC 792: Internet Control Message Protocol
- RFC 1071: Computing the Internet Checksum
- `capabilities(7)`: Linux capabilities man page
- `icmp(7)`: Linux ICMP socket programming
