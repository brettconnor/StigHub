# IOS-XE IPsec anti-replay

Accessed 2026-11-23 for SRG-NET-000147-VPN-000530.

## Cisco references

- [IPsec Data Plane Configuration Guide, Cisco IOS XE 16.12 — Anti-Replay Window](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_dplane/configuration/xe-16-12/sec-ipsec-data-plane-xe-16-12-book/sec-ipsec-antireplay.html)
  documents IPsec replay protection using monotonically increasing ESP
  sequence numbers and a receive window. It identifies 64 packets as the
  default window and documents
  `crypto ipsec security-association replay window-size <N>` to explicitly
  set the window globally. That command is mutually exclusive with
  `crypto ipsec security-association replay disable`.
- [Troubleshoot IPsec Anti-Replay Check Failures](https://www.cisco.com/c/en/us/support/docs/ip/internet-key-exchange-ike/116858-problem-replay-00.html),
  updated 2026-09-14, explains duplicate/out-of-window packet rejection and
  verification of the operational window. It documents
  `show crypto ipsec sa peer <ip-address> platform` for platform-level
  inspection where supported.

## Assessment use

The SRG concerns ESP anti-replay at the data plane, not IKEv2 message-ID
replay protection. The product fix explicitly configures a 64-packet
window globally. This equals Cisco IOS XE's documented default window and
avoids raising the receive window or changing the profile's other policy.
The global command applies to all IPsec SAs, not just the two named VTIs;
confirm that scope is appropriate on the deployed router. Do not configure
it together with a replay-disable command.

Verify the explicit configuration and inspect `show crypto ipsec sa` for
each active IPv4 and IPv6 SA, confirming anti-replay is enabled. Where
supported, supplement with the platform-specific SA output to confirm the
effective replay window. Check both directions and repeat after SA
re-establishment. Exact syntax, support, defaults and operational output
must be verified for the deployed PID and IOS XE release; no device testing
has been performed.
