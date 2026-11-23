# IOS-XE IKEv2 session termination

Reviewed **23 November 2026** for SRG-NET-000213-VPN-000720.

## Configuration and behavior

Both PSK and X.509 IOS-XE templates configure periodic Dead Peer Detection
(DPD) on their IPv4 and IPv6 IKEv2 profiles:

```text
crypto ikev2 profile IKE2-PROFILE
 dpd 30 6 periodic
!
crypto ikev2 profile IKE2-PROFILE6
 dpd 30 6 periodic
```

Cisco's IOS XE 16.11 IKEv2 guide documents the profile command syntax
`dpd interval retry-interval {on-demand | periodic}` and states DPD is
disabled by default. Periodic mode sends liveness probes without waiting for
data traffic. When a peer becomes unreachable after retries, DPD clears the
IKE/IPsec session state. The selected values use a 30-second probe interval
and 6-second retry interval; confirm support and behavior on the target
platform and release.

For a clean IKEv2 session close, RFC 7296 states that closing an IKE SA
implicitly closes its associated Child SAs. Cisco also documents that, unless
the optional IPsec SA idle timer is configured, IPsec SAs remain until their
global lifetimes regardless of activity. DPD is peer-liveness detection for
the site-to-site VPN session; it does not manage arbitrary inner TCP
connections forwarded by the router.

## References

- [Cisco IOS XE Gibraltar 16.11.x — Configuring IKEv2](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ike2vpn/configuration/xe-16-11/sec-flex-vpn-xe-16-11-book/sec-cfg-ikev2-flex.html)
- [Cisco IOS XE 17 — IPsec Dead Peer Detection Periodic Message Option](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_dplane/configuration/xe-17/sec-ipsec-data-plane-xe-17/sec-ipsec-dead-peer.html)
- [Cisco IOS XE 17 — IPsec Security Association Idle Timers](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_dplane/configuration/xe-17/sec-ipsec-data-plane-xe-17/sec-ipsec-idle-tmrs.html)
- [RFC 7296, Section 1.4.1 — Deleting an SA](https://www.rfc-editor.org/rfc/rfc7296#section-1.4.1)
