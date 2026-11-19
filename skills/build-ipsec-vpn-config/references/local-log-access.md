# IOS-XE local log access

- **Cisco RS-Cookbook IOS-XE starting configuration**:
  <https://wwwin-github.cisco.com/gct-dp/RS-Cookbook/blob/master/Config%20Recipes/IOS-XE/_starting-config.cisco>.
  Accessed 2026-11-19. The operator identifies its local administrator and
  local AAA configuration as the source for this assessment.
- **Cisco Protecting Secrets on Network Devices**:
  <https://www.cisco.com/c/en/us/about/trust-center/resilient-infrastructure/protecting-secrets.html>.
  Explains IOS XE credential types and their security properties.
- **Cisco IOS XE username command reference**:
  <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/security/s1/sec-s1-xe-3se-3850-cr-book/sec-s1-xe-3se-3850-cr-book_chapter_0110.html>.
  Documents separate username privilege and type 8 or type 9 secret commands.
- **ISR 1000 router access guide**, accessed 2026-11-19:
  <https://www.cisco.com/c/en/us/td/docs/routers/access/isr1100/software/configuration/guide/isr1100-sw-config/sec_router_access_pwd_privilege.html>.
  Discusses type 8 or 9 username and enable secrets, and documents type 9
  conversion from IOS XE 17.2.1.
- **8100 Secure Routers access guide**, accessed 2026-11-19:
  <https://www.cisco.com/c/en/us/td/docs/routers/secure-routers/sec-8100-series/software-config-guide/cisco-8100-series-secure-routers-software-configuration-guide/sec_router_access_pwd_privilege.html>.
  Discusses type 8 or 9 username and enable secrets. Check the exact
  platform and release rather than inferring universal command support.

The optional `configs/cli/iosxe-local-access.cisco` template allows selection
of type 8 or type 9 credentials. Use only a type supported by the exact target
platform and release; these options are not a platform compatibility matrix.

The recipe does not specify the local credential's storage algorithm.
Verify a secure method supported by the target platform and release before
selecting the account configuration. Check actual access to both buffered
and persistent logs; the example is not evidence of device behavior.

## Console-only remote-management baseline

For SRG-NET-000132-VPN-000450, the operator selected console management
and assessment of SSH/VTY, NETCONF, HTTP/HTTPS, and RESTCONF entry points.
The local-access template now disables these remote-management paths.
This supersedes its earlier comments retaining HTTPS for RESTCONF.
Product support for NETCONF/RESTCONF is unchanged; enabling them is a
different deployment policy. These are management services, not remote-access
VPN tunnels.

Sources consulted 2026-11-19:

- [Cisco guide to harden Cisco IOS devices](https://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html):
  documents `no ip http server`, `no ip http secure-server`, and line
  transport restrictions.
- [Cisco IOS XE NETCONF protocol guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1717/b_1717_programmability_cg/m_1717_prog_yang_netconf.html):
  NETCONF-YANG has its own SSH server, normally TCP 830; VTY restrictions
  alone must not be used to infer that NETCONF is disabled. Negate
  `netconf-yang` explicitly.
- [Cisco IOS XE NETCONF over SSHv2](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ntw-servs/b-network-services/m_netconf-sshv2.html):
  documents the separate legacy `netconf ssh` enablement. Negate it on
  targets supporting that implementation.
- [Cisco IOS XE RESTCONF protocol guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/prog/configuration/1717/b_1717_programmability_cg/m_1717_prog_restconf.html):
  documents `restconf` and secure HTTP enablement. Negate RESTCONF and
  disable both HTTP servers for the console-only baseline.
- [Cisco SSH router configuration guide](https://www.cisco.com/c/en/us/support/docs/security-vpn/secure-shell-ssh/4145-ssh.html):
  describes VTY transport selection and covering all available VTY lines.
  `transport input none` denies new inbound VTY transports, including SSH
  and Telnet; it is not a claim that every SSH-related listener is stopped.

Apply from a verified console, not through an entry point being disabled.
Check syntax and feature availability on the exact PID/release, including
ISR 4000 and ASR 1000 releases. Do not remove cryptographic keys as a
shortcut to disabling SSH: keys may have other uses. Review existing
sessions separately and test new connections from reachable management
paths for both address families and any configured nonstandard ports.
Use effective/default configuration and feature-specific operational
evidence; absent lines alone do not prove disabled services. No live-router
validation has been performed. Other service families remain in the draft
inventory and are not covered by this focused authoring decision.

## Router release-note candidates

The project has not established an exhaustive approved model list. If the
intended scope is the union of routers supporting IOS XE 17.18.x or 26.2.x,
the following Cisco release notes identify families to assess. A family-level
release note does not prove that every PID, image, mode, license, credential
type, or site-to-site VPN feature is supported.

| Family | 17.18.x | 26.2.x |
| --- | --- | --- |
| Catalyst 8200/8300 Edge | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/cloud_edge/c8300/rel_notes/17-18-x/release-notes-catalyst-8200-and-catalyst-8300-series-edge-platforms-release-17-18-x.html) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/cloud_edge/c8300/rel_notes/26-x/release-notes-catalyst-8200-and-catalyst-8300-series-edge-platforms-release-26-2-x.html) |
| Catalyst 8500 Edge | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/cloud_edge/c8500/release-notes/17-18-x/ReleaseNotes-C8500-17-18-1a.html) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/cloud_edge/c8500/release-notes/releasenotes-c8500-edge-26-2-x.html) |
| 8100/8300 Secure Routers | [8100](https://www.cisco.com/c/en/us/td/docs/routers/secure-routers/sec-8100-series/release-notes/release_notes_for_cisco_8100_series_secure_routers_17_18_x.html), [8300](https://www.cisco.com/c/en/us/td/docs/routers/secure-routers/sec-8300-series/release-notes/17-18-x/release-notes-cisco-8300-series-secure-routers-release-17-18-x.html) | [8000 Secure Routers](https://www.cisco.com/c/en/us/td/docs/routers/secure-routers/cisco-8000-series-secure-routers-release-26-2-x.html) |
| 8500 Secure Routers (distinct from 8500 Edge) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/secure-routers/sec-8500-series/release-notes/17-18/release_notes_for_cisco_8500_series_secure_routers_release_17_18_x.html) | Not established |
| ISR 1000 | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/access/1100/release/17-18/isr1k-release-notes-xe-17-18-x.html) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/access/1100/release/isr1k-release-notes-xe-26-2-x.html) |
| ISR 4000 | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/access/isr4400/Release-notes/17-18-x/isr4k-rel-notes-xe-17-18.html) | Not supported, per operator |
| ASR 1000 | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/asr1000/release/notes/xe-17-18/asr1000-rel-notes-xe-17-18.html) | Not supported, per operator |
| IR1101/IR1800/IR8140/IR8340 | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/IIoT/release-notes/17-18-x/IOT-IR-17-18-1-RN.html) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/IIoT/release-notes/26-2-x/IOT-IR-26-2-x-RN.html) |
| ESR6300 | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/IIoT/release-notes/17-18-x/IIOT-ESR-17-18-1-RN.html) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/IIoT/release-notes/26-2-x/IIOT-ESR-26-2-x-RN.html) |
| Catalyst 8000V (virtual) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/C8000V/Release-Notes/c8000v-releasenotes-17-18.html) | [Release notes](https://www.cisco.com/c/en/us/td/docs/routers/C8000V/Release-Notes/c8000v-releasenotes-26-2-x.html) |

The operator includes ISR 4000 and ASR 1000 in the SRG scope despite their
not supporting IOS XE 26.x.

The candidate configuration is not validated for every family or PID. Check
the exact device's command support, IKEv2/IPsec features, and effective log
access before choosing an option. No secure local-secret option has been
established here for a platform supporting neither type 8 nor type 9.
