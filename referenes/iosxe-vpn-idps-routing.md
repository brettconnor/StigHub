# IOS-XE VPN-to-IDPS routing

Reviewed **23 November 2026** for SRG-NET-000205-VPN-000710.

## Cisco routing behavior and commands

- Cisco's [IOS XE 16.12 IPsec VTI guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_vpnips/configuration/xe-16-12/sec-sec-for-vpns-w-ipsec-xe-16-12-book/sec-ipsec-virt-tunnl.html)
  explains that traffic arriving on a VTI is decrypted and then routed by
  the IP routing table. The guide documents static/dynamic routing for
  traffic forwarded to VTIs.
- Cisco's [IPv6 PBR guide for IOS XE 17.x](https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-routing/b-ip-routing/m_ip6-pbr-xe.html)
  documents input-interface IPv6 PBR using a route map, `match ipv6 address`,
  `set ipv6 next-hop`, and `ipv6 policy route-map`. The next hop must be a
  global IPv6 address present in the RIB and directly connected.
- Cisco's [IPv4 PBR guide for IOS XE 17.x](https://www.cisco.com/c/en/us/td/docs/routers/ios-xe/ip-routing/b-ip-routing/m_iri-pbr.pdf)
  documents interface-attached `ip policy route-map` processing for packets
  arriving on the interface.
- Cisco's [multi-SA VTI configuration guide](https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/214728-configure-multi-sa-virtual-tunnel-interf.html)
  describes routing traffic through VTIs and notes PBR use in that VTI
  design. Verify support for the exact platform, release, tunnel type, and
  direction before using PBR on a VTI.

## Design guidance for 000710

For known protected IPv4/IPv6 destination prefixes, the simplest router-side
solution is a route for each prefix via the adjacent IDPS next hop. The
route applies to any traffic for that destination, including packets
decrypted from a VTI. Provide corresponding return routes through the
inspection path.

If literally every packet arriving decrypted on a VTI must go to the
inspection hop regardless of destination, use input-interface PBR only
after verifying support on the target PID/release. Scope the policy to the
VTI, not the WAN interface, so IKE/ESP underlay traffic is unaffected.
Ensure an unavailable next hop cannot cause normal routing to bypass the
IDPS; route-map fallback and tracking behavior must be validated on the
target.

A global IPv4/IPv6 default route to the IDPS is not an equivalent scoped
policy: it affects other router traffic and can alter WAN peer reachability
or tunnel-endpoint routing. This reference does not define the site's IDPS
addresses, protected prefixes, interface names, or approved failover
behavior.

## Source-specific forwarding into a VTI

For route-based VPNs, a destination route for a remote protected prefix
through a VTI encrypts traffic to that prefix regardless of source. If
source-specific selection is required, apply PBR on the downstream-facing
input interface, match the device source address and intended remote
destinations, and direct matching packets to the appropriate VTI. Do not
apply that policy on the WAN interface. Cisco's multi-SA VTI guide documents
PBR as a way to select traffic for a VTI; verify exact platform/release
support. Cisco's IOS XE IPv6 PBR guide requires a usable RIB path for the
destination when using an output-interface action. Ensure the remote peer
routes return traffic to the device and, where applicable, its IPsec traffic
selectors include the device and remote prefixes.

## Full-tunnel northbound routing

The operator's current high-security deployment choice is full-tunnel
routing rather than source-specific PBR. For a route-based VTI, install
IPv4/IPv6 default routes through the corresponding tunnel:

```text
ip route 0.0.0.0 0.0.0.0 <TUN4>
ipv6 route ::/0 <TUN6>
```

These are routing-table defaults, not per-device policies: they send all
traffic using that routing table through the VPN, including traffic from
other downstream hosts and potentially router-originated traffic. Preserve
underlay reachability with more-specific host routes for each outer VPN peer
via its WAN next hop:

```text
ip route <IPSEC_PEER_IPV4> 255.255.255.255 <WAN_IPV4_NEXT_HOP>
ipv6 route <IPSEC_PEER_IPV6>/128 <WAN_IPV6_NEXT_HOP>
```

Use the target platform's appropriate WAN interface/next-hop form. Ensure
the remote gateway provides the intended onward routing and return path.
For fail-closed behavior, verify that loss of the VTI cannot select another
Internet default route and bypass the tunnel; do not rely on interface state
or static-route withdrawal without validating target behavior. If only one
host should be full-tunneled while other hosts remain split-routed, a global
default route is not appropriate; use a separately scoped routing table or
validated source policy instead.

## Southbound decrypted traffic through an IDS/IPS

Assuming the IDS/IPS is a routed next hop, add a more-specific route for
each protected destination prefix through its VPN-facing/inspection-side
next-hop address:

```text
ip route <PROTECTED_IPV4_PREFIX> <MASK> <IDS_IPS_IPV4_NEXT_HOP>
ipv6 route <PROTECTED_IPV6_PREFIX>/<PREFIX_LENGTH> <IDS_IPS_IPV6_NEXT_HOP>
```

The routes are used after VTI decapsulation and take precedence over the
full-tunnel defaults by longest-prefix match. The IDS/IPS and protected
network must have return routes that send the reverse flow back through the
inspection path to the VPN gateway. Preserve symmetric paths for stateful
inspection.

With fail-closed requirements, prevent removal/unreachability of an
inspection route from exposing a less-specific VTI default as a bypass.
Validate next-hop tracking and route-withdrawal behavior on the target; a
floating discard route for the protected prefix may be used as a fallback
when the preferred IDS/IPS route is withdrawn. This guidance assumes a
routed IDS/IPS; a transparent bridge deployment needs a different topology.
