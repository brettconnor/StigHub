# IOS-XE IPsec ESP anti-replay

Cisco sources reviewed **23 November 2026** for
SRG-NET-000147-VPN-000530.

## What the sources establish

- Cisco's [IOS XE IPsec Data Plane Configuration Guide, release 16.12](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_dplane/configuration/xe-16-12/sec-ipsec-data-plane-xe-16-12-book/sec-ipsec-antireplay.html)
  describes ESP anti-replay using monotonically increasing sequence numbers
  and a receive window. It documents 64 packets as the default window and
  the global command
  `crypto ipsec security-association replay window-size <N>` to explicitly
  set the window. The command is mutually exclusive with
  `crypto ipsec security-association replay disable`.
- Cisco's [Troubleshoot IPsec Anti-Replay Check Failures](https://www.cisco.com/c/en/us/support/docs/ip/internet-key-exchange-ike/116858-problem-replay-00.html),
  updated 14 September 2026, describes dropping duplicate or out-of-window
  packets and inspecting the active SA's replay state. Where supported, its
  platform-level verification example is
  `show crypto ipsec sa peer <ip-address> platform`.
- IKEv2 message-ID replay protection is separate control-plane behavior;
  this SRG's discussion concerns anti-replay protection for ESP packets.

The local SRG fix explicitly sets the global replay window to 64 packets,
matching the documented default. This changes the window setting for all
IPsec SAs on the router, not just a named VTI. Do not combine it with the
replay-disable command. Inspect the active `show crypto ipsec sa` output for
each IPv4/IPv6 SA and verify effective behavior on the actual PID/release.

These are Cisco documentation sources, not evidence that every in-scope
router supports identical syntax or that any router has been configured or
tested. No live-device validation was performed.
