# IOS-XE VPN router service inventory — draft

**Draft, not exhaustive or device-validated.** This is a starting inventory
for SRG-NET-000132-VPN-000450, not a platform compatibility matrix, an
approved PPSM CAL, a vulnerability assessment, or proof of compliance.
Expand it as platform, release, feature, and policy evidence is obtained.

## Scope and interpretation

- The assessed product is a site-to-site IOS-XE VPN router. ISR 4000 and
  ASR 1000 remain in scope for their supported IOS-XE releases, although
  the operator says they do not support IOS-XE 26.x.
- The operator's proposed policy prohibits unnecessary or insecure
  functions, ports, protocols, and services by default. Rows labeled
  **review** are candidates for an explicit decision, not an assertion
  that a service is forbidden or unnecessary.
- RESTCONF and NETCONF are supported management options; support does not
  mean they must be enabled or exposed on every deployment. The operator
  subsequently selected a console-only baseline for this SRG's
  remote-management assessment: SSH/VTY, NETCONF, HTTP/HTTPS, and RESTCONF
  are disabled by `iosxe-local-access.cisco`. NETCONF-YANG has a separate
  SSH server; VTY restrictions alone are insufficient. This focused scope
  decision does not resolve the remaining inventory rows.
- The golden VPN template permits peer-specific UDP 500 and native ESP on
  WAN ingress and denies other IP traffic. UDP 4500/NAT-T is **not**
  permitted by that ACL. Management access must use an authorized path
  outside that WAN ingress policy. A WAN ACL is not proof that local
  services are disabled.
- Default state, syntax, support, port, interface binding, image, mode, and
  operational behavior are **unverified for every row and exact PID** unless
  an individual entry explicitly states otherwise. A feature being listed
  below does not mean that every router supports it. Port numbers below are
  common assignments, not evidence of an actual listener or configured port.

The [router release-note candidates](../skills/build-ipsec-vpn-config/references/local-log-access.md#router-release-note-candidates)
identify families with published 17.18.x and/or 26.2.x release notes. Those
notes do not establish support or default state of any particular row below.

## How to use

1. Identify the exact PID, release, image, license, mode, and interfaces.
2. Record the approved management paths and necessary VPN, management, and
   infrastructure dependencies. Apply the PPSM CAL and vulnerability
   assessments when applicable; do not rewrite the shared SRG requirement.
3. Use `show running-config all`, including relevant line and interface
   sections, to inspect settings. Tokens below are **search clues**, not
   complete commands or tests. Missing output is **not** proof of a disabled
   feature; defaults and configuration visibility vary.
4. Where supported, supplement configuration with feature-specific status,
   `show ip sockets`, and tests from authorized and unauthorized network
   locations. Sockets do not cover all services, IP protocols, or Layer 2.
5. Record the observed configuration, effective state, access paths,
   applicable policy, source and date, and platform-specific result. Protect
   and redact device configuration and credentials before sharing evidence.

**Decision key:** **Allow** = established project policy for that path;
**Supported** = an operator-identified option, not mandatory enablement;
**Deny** = proposed baseline for a known insecure service;
**Review** = explicit policy and target validation still needed. These are
proposed authoring decisions, not assertions about router defaults.

## VPN and traffic paths

| Function | Configuration clues | Draft decision | Evidence / caveat |
| --- | --- | --- | --- |
| IKEv2 | `crypto ikev2`, WAN IPv4/IPv6 ACLs | Allow peer-specific UDP 500 on WAN | Golden template; inspect profile, peer and ACL attachment. |
| IPsec ESP | `crypto ipsec`, WAN ACLs | Allow peer-specific native ESP on WAN | ESP is IP protocol 50, not a TCP/UDP port. |
| IPsec NAT traversal | IKEv2 settings; WAN ACLs | Review | UDP 4500 is denied by the current WAN ACL; do not assume NAT-T works. |
| Other WAN IP traffic | WAN ACLs and interface attachments | Deny under current WAN policy | Confirm both address families and actual forwarding. |
| VPN tunnel interfaces | `interface Tunnel`, `tunnel protection` | Allow approved site-to-site tunnels | Validate tunnel source, destination, routing and IPsec state. |
| Inner/decrypted traffic | Tunnel routing and applicable filters | Review | Outer WAN ACL does not define authorization of decrypted traffic. |
| IPv4 ARP | WAN L2 / interface state | Review | ARP is Layer 2 and is not filtered by the WAN IP ACL. |
| IPv6 neighbor discovery and router advertisements | IPv6 interface, `ipv6 nd`, IPv6 ACL | Review | Existing WAN ACL blocks ICMPv6 including ND; validate alternative neighbor resolution. |
| ICMP and path MTU | IPv4/IPv6 ACLs, interface settings | Review | Current WAN ACL blocks ICMP/ICMPv6; validate operational impact. |
| Routing protocols | `router`, interface routing settings, address families | Review | Distinguish tunnel routing from outer WAN control traffic. |
| Other tunnel/encapsulation services | Tunnel interfaces and profiles | Review | Inspect GRE and other enabled tunnels; do not infer from sockets. |

## Management and API servers

| Function | Configuration clues | Draft decision | Evidence / caveat |
| --- | --- | --- | --- |
| Cleartext HTTP server (TCP 80) | `ip http server` | Deny | `iosxe-local-access.cisco` specifies `no ip http server`; inspect actual state. |
| HTTPS server / web UI (TCP 443) | `ip http secure-server` | Deny in console-only baseline | Local-access template disables HTTPS; RESTCONF deployment would require a policy change. |
| RESTCONF | `restconf`, secure HTTP configuration | Supported capability; disabled in baseline | Local-access template uses `no restconf`; support is not enablement. |
| NETCONF (TCP 830 by default) | `netconf-yang`, legacy `netconf ssh` | Supported capability; disabled in baseline | Disable implementations separately where supported; VTY restrictions alone do not disable NETCONF-YANG. |
| SSH interactive management (TCP 22) | `ip ssh`, VTY line `transport input` | Deny in console-only baseline | Local-access template sets `transport input none` on every VTY; verify new connections are rejected. |
| Telnet (TCP 23) and other VTY input | VTY `transport input` | Deny in console-only baseline | Inspect every VTY range and effective defaults for `transport input none`. |
| AUX / TTY remote access | `line aux`, `line`, `transport input` | Review | Check platform ports, effective settings and physical access. |
| Console access | `line con`, login/authorization settings | Allow authorized access | Physical security is a separate dependency; console log output may be visible. |
| SNMP agent (UDP 161; notifications commonly 162) | `snmp-server` users, groups, communities, access | Review | If needed, approve secure v3 authentication/privacy and restrict sources. |
| NETCONF/RESTCONF authorization | AAA, HTTP and SSH authorization | Review | The local admin template is not complete API access control. |
| gRPC / gNMI management | Platform telemetry / gRPC configuration | Review | Check listeners, authentication, TLS and management isolation. |
| SCP server | `ip scp server` | Review | A server is distinct from an SCP client; retain only if authorized. |
| TFTP server (UDP 69) | `tftp-server` | Review; deny insecure use | Server configuration differs from outbound TFTP client settings; transfer ports vary. |
| FTP server (TCP 21 control) | Platform FTP-server configuration | Review; deny insecure use | Check server support and actual listener; data ports vary; do not confuse client settings. |
| RSH / RCP | `ip rcmd` | Deny insecure use | Cisco security-warning reference identifies these as legacy protocols. |
| Finger / ident | `ip finger`, `service finger`, ident settings | Deny insecure use | Syntax and default may vary by target. |
| TCP small servers | `service tcp-small-servers` | Deny unless explicitly authorized | Echo, discard, daytime and chargen; verify default and listeners. |
| UDP small servers | `service udp-small-servers` | Deny unless explicitly authorized | Verify default and listeners independently of TCP. |
| PAD / legacy line transports | `service pad`, line transport settings | Review; deny insecure use | Platform support and remote-line exposure vary. |
| Smart Install / legacy deployment service | `vstack` and applicable platform settings | Review | Primarily platform-specific; do not assume router support or absence. |
| Guest shell / application hosting | IOx, guestshell and app-hosting configuration | Review | Check application listeners and dependencies, not only IOS configuration. |

## Infrastructure, clients, and Layer 2

| Function | Configuration clues | Draft decision | Evidence / caveat |
| --- | --- | --- | --- |
| DNS server (TCP/UDP 53) | DNS server configuration | Review | Separate server functionality from the DNS resolver client. |
| DNS resolver client | `ip domain`, name-server settings | Review | May be required for approved operations; not a listening DNS server. |
| DHCPv4 server (UDP 67/68) | `ip dhcp pool`, DHCP service and interface configuration | Review | Pools alone may not describe every effective DHCP state. |
| DHCPv4 client / relay | Interface addressing, helper addresses | Review | Client, relay and server are distinct. Golden WAN assumes static addressing. |
| DHCPv6 server (UDP 546/547) | `ipv6 dhcp pool`, interface `ipv6 dhcp server` | Review | Inspect interface attachment and IPv6 ACLs. |
| DHCPv6 client / relay | IPv6 interface and relay settings | Review | Not equivalent to enabling a DHCPv6 server. |
| BOOTP | BOOTP server and interface settings | Review | Check whether any legacy service is supported or required. |
| NTP server / peer (UDP 123) | `ntp` configuration and restrictions | Review | Distinguish serving or peering from synchronization client use. |
| NTP client | `ntp server` and authentication settings | Review | May support accurate audit timestamps; do not disable blindly. |
| Syslog export | `logging host`, `logging source-interface` | Review | An outbound logging function, not proof of an inbound listener. |
| Local buffered / persistent logs | `logging buffered`, `logging persistent` | Review | Preserve required audit logging and validate access and retention. |
| CDP | Global and interface CDP settings | Review | Layer 2 discovery; WAN IP ACLs do not filter it. |
| LLDP | Global and interface LLDP settings | Review | Layer 2 discovery; inspect each interface. |
| IP source routing | `ip source-route`, IPv6 source-route settings | Deny insecure use | Inspect IPv4 and IPv6 behavior separately. |
| Proxy ARP | Interface `ip proxy-arp` | Review | Per-interface behavior; consider legitimate L2 requirements. |
| Directed broadcast | Interface `ip directed-broadcast` | Review | Per-interface behavior and default vary by target. |
| Plug and Play / zero-touch provisioning | PnP and platform provisioning settings | Review | Confirm whether onboarding is still needed before disabling. |
| Call-home / Smart Licensing | `call-home`, licensing configuration | Review | Outbound service and licensing dependencies; do not disable blindly. |
| Controller-managed / SD-WAN functions | Platform management mode and controller configuration | Review | This draft does not certify autonomous and controller modes equally. |
| Telemetry / NetFlow export | Telemetry, flow monitors and exporters | Review | Differentiate outbound export from an inbound management endpoint. |
| Routing and first-hop protocols | `router`, interface, first-hop configuration | Review | Check both control-plane exposure and actual dependencies. |
| Other platform / module services | Platform-specific configuration and operational inventory | Review | Industrial, cellular, voice, Wi-Fi and virtual platforms need further rows. |

## Initial evidence and open coverage

- [Cisco IOS device hardening](https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html)
  covers management, control and data plane hardening.
- [Cisco IOS-XE security warnings](https://www.cisco.com/c/en/us/about/trust-center/resilient-infrastructure/resilient-infrastructure-security-warnings-reference.html)
  describes individual insecure features and warnings.
- [Cisco resilient infrastructure guidance](https://www.cisco.com/c/en/us/support/docs/ios-nx-os-software/ios-xe-17181/225978-understand-resilient-infrastructure-on.html)
  describes `show system insecure configuration` from 17.18.2 and the
  security-mode mechanism from 26.1.1. The command reports restriction-phase
  findings, not every warning-phase feature; scanning can lag changes.
- [Cisco RESTCONF guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1717/b_1717_programmability_cg/m_1717_prog_restconf.html)
  and [NETCONF-over-SSH guide](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ntw-servs/b-network-services/m_netconf-sshv2.html)
  describe transport and configuration dependencies; check the target release.
- [Cisco ESR6300 web UI guide](https://www.cisco.com/c/en/us/td/docs/IIOT/routers/embedded/6300/software/config/b_ESR6300_config/b_ESR6300_config_chapter_01110.html)
  says HTTP and HTTPS server configuration should be present by default;
  do not generalize this to all routers or all images.
- [Cisco IP sockets reference](https://www.cisco.com/c/en/us/td/docs/ios/ipapp/command/reference/iap_s3.html)
  documents socket output. Check command availability and coverage on the
  target IOS-XE release.

No platform-by-platform default or support testing has been performed.
PIDs, release-specific exceptions, defaults, approved service decisions,
complete command coverage, module services, and live device results remain
open. Do not copy all candidate disable commands into a device configuration.
