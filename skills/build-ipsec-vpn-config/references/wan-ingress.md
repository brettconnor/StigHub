# WAN ingress filtering references

Accessed 2026-11-04 for `configs/cli/iosxe-ikev2-ipsec`.

## Cisco primary documentation

**IPv6 Access Control Lists, Cisco IOS XE Fuji 16.9.x**

<https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_data_acl/configuration/xe-16-9/sec-data-acl-xe-16-9-book/ip6-acls-xe.html>

Documents IPv6 ACL creation, ordered permit/deny rules, and interface
attachment with `ipv6 traffic-filter <name> in`. Explicitly warns that
neighbor discovery must be permitted on platforms without implicit ND
permissions, including ASR 1000. Blocking ND can prevent IPv6 link operation.

The operator's policy permits only peer-addressed IKE (UDP 500) and ESP before
denying all other WAN IP ingress. The template therefore intentionally
contains no ICMP error or IPv6 neighbor-discovery exceptions.
NAT-T is not used; UDP 4500 is not permitted in either address family.
An address-based permit does not authenticate a peer; IKE/IPsec performs
that verification. The physical WAN ACL is not a decrypted-tunnel resource
authorization policy.

This reference is release/platform scoped. Validate ACL command support,
fragment handling, IPsec/VTI packet-processing order, neighbor discovery,
PMTU, and both allowed and denied data flows on the actual device. No device
validation was performed. Static WAN addressing and next hops are assumed;
DHCP, IPv6 router advertisements, routing protocols, and direct WAN
management are blocked. IPv6 requires an approved alternative to dynamic
neighbor discovery, and blocked ICMP errors can break path MTU discovery.
No alternative or additional traffic exception is configured by this change.
IPv4 ARP is Layer 2 and is not filtered by these IP ACLs.
