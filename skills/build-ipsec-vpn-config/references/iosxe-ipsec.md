# IOS XE IPsec and IKEv2 references

These are the web references gathered while reviewing
`configs/cli/iosxe-ikev2-ipsec` on 2026-11-04. They are retained here so
future edits to the canonical template and its product guidance can trace
technical claims to their sources. Platform, hardware, software-image, and
release support must be verified for the actual deployment.

## Cisco primary documentation

1. **FlexVPN and Internet Key Exchange Version 2 Configuration Guide,
   Cisco IOS XE Gibraltar 16.11.x — Configuring IKEv2**

   <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ike2vpn/configuration/xe-16-11/sec-flex-vpn-xe-16-11-book/sec-cfg-ikev2-flex.html>

   Describes IKEv2 proposals, policies, profiles, and key rings; lists
   encryption, integrity, PRF, and DH as proposal transforms; documents
   defaults and cautions that platform support varies. Consult the current
   platform/release guide before relying on any command or algorithm.

2. **FlexVPN and Internet Key Exchange Version 2 Configuration Guide,
   Cisco IOS XE Gibraltar 16.10.x**

   <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ike2vpn/configuration/xe-16-10/sec-flex-vpn-xe-16-10-book/sec-cfg-ikev2-flex.html>

   Additional IKEv2 proposal and AES-GCM background, including Cisco's note
   that authenticated encryption combines encryption and integrity. This is
   an older release guide and is not a substitute for target-release
   validation.

3. **Security and VPN Configuration Guide, Cisco IOS XE 17.x — IPsec
   Virtual Tunnel Interfaces**

   <https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/sec-vpn/b-security-vpn/m_sec-ipsec-virt-tunnl-0.html>

   Describes static and dynamic VTIs, tunnel-mode requirements, traffic
   selector behavior, and attaching security services to tunnel interfaces.
   The documented restrictions are platform/feature dependent.

4. **IPsec Configuration Guide, Cisco IOS XE 17, ASR 900 — Transform Sets**

   <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ikevpn/configuration/xe-3s/asr900/17-1-1/b-sec-ipsec-xe-17-1-asr900/m-sec-ipsec-transform-sets-900.html>

   Provides IOS XE transform-set command examples and verification context.
   Its examples and support statements apply to the named platform/release;
   they should not be generalized without checking the target device.

5. **IPsec Configuration Guide, Cisco IOS XE 17, ASR 900 — IKE**

   <https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ikevpn/configuration/xe-3s/asr900/17-1-1/b-sec-ipsec-xe-17-1-asr900/m-sec-key-exch-ipsec-900.html>

   IKE configuration and platform support background for ASR 900 IOS XE.

6. **Security Configuration Guide, Cisco IOS XE 17.14.x, Catalyst 9300 —
   Configuring IPsec**

   <https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/17-14/configuration_guide/sec/b_1714_sec_9300_cg/configuring_ipsec.html>

   Describes Catalyst 9300 IPsec restrictions and supported IPsec transforms,
   including platform-specific VTI limitations. Do not apply these Catalyst
   restrictions or capabilities to routers without their own documentation.

7. **Cisco Support — Implementing IKEv2 Route-Based Site-to-Site VPN on Cisco
   Routers Using IPv6**

   <https://www.cisco.com/c/en/us/support/docs/security-vpn/internet-security-association-key-management-protocol-isakmp/223291-implementing-ikev2-route-based-site-to.html>

   Cisco example configuration for IPv6 route-based site-to-site IKEv2/IPsec,
   including an IPv6 keyring peer and VTI. Examples demonstrate a pattern;
   confirm algorithms and syntax against the target platform and release.

8. **Cisco IOS XE 17 Interface Characteristics Configuration Guide**

   <https://www.cisco.com/c/en/us/td/docs/switches/lan/c9000/infra/interface-characteristics/interface-characteristics-configuration-guide.html>

   Background on Layer 2 and Layer 3 interface characteristics, routed ports,
   VLAN subinterfaces, and switch virtual interfaces.

9. **VLAN Configuration Guide, Cisco IOS XE 26.x, Catalyst 9300**

   <https://www.cisco.com/c/en/us/td/docs/switches/lan/catalyst9300/software/release/26-x/configuration_guide/vlan/b_26x_vlan_9300_cg/configuring_vlans.html>

   VLAN/SVI reference for the named Catalyst platform and release family.

10. **Cisco Catalyst 8300 Series Edge Platforms Data Sheet**

    <https://www.cisco.com/c/en/us/products/collateral/routers/catalyst-8300-series-edge-platforms/datasheet-c78-744088.html>

    Product-level feature overview. A data sheet is not a substitute for the
    IOS XE configuration guide or command reference.

11. **Cisco Catalyst 8300 Series Edge Platforms Release Notes**

    <https://www.cisco.com/c/en/us/support/routers/catalyst-8300-series-edge-platforms/products-release-notes-list.html>

    Index to release-specific notes. Check the notes for the exact installed
    release and platform.

## Cisco community material

12. **Cisco Community — IKEv2 AES-GCM proposal and NULL integrity**

    <https://community.cisco.com/t5/vpn/ikev2-ipsec-proposal-aes-gcm-256-encryption-requires-null-for/td-p/2918304>

    Community explanation that GCM includes packet integrity, so a separate
    HMAC is not used for the ESP transform. Treat this as secondary
    explanation; use the relevant Cisco configuration guide and command
    reference for supported syntax.

13. **Cisco Community — Site-to-Site IKEv2 IPsec VPN Implementation**

    <https://community.cisco.com/t5/security-knowledge-base/site-to-site-ikev2-ipsec-vpn-implementation/ta-p/5304831>

    Community configuration walkthrough covering the IKEv2 proposal, policy,
    keyring, profiles, and transform sets. Verify each command and algorithm
    against current official platform documentation.

## Other secondary example

14. **PingLabz — IKEv2 Site-to-Site VPN with SVTI: Cisco IOS XE Config**

    <https://www.pinglabz.com/ikev2-svti-configuration/>

    Lab example found during research, including an AES-GCM IKE proposal
    example. This is not Cisco product documentation; do not rely on it for
    platform support or production recommendations.

15. **Cisco Support — Secure Stored Pre-shared Keys in a Router**

    <https://www.cisco.com/c/en/us/support/docs/security-vpn/ipsec-negotiation-ike-protocols/46420-pre-sh-keys-ios-rtr-cfg.html>

    Background on protecting stored pre-shared keys in IOS/IOS XE. Follow
    current platform and organizational secret-management policy; never place
    operational key material in this repository.

## Scope notes

- These references were collected for research and traceability. No
  configuration was applied to a router or validated with a device CLI.
- AES-GCM support, IKEv2 PRF configuration, DH groups, IPv6 VTI behavior,
  keyring syntax, interface syntax, licensing, and hardware acceleration
  vary by product and IOS XE release.
- The reference set does not establish that the repository template is
  deployable as-is, that traffic authorization is configured, or that a
  device meets an SRG.
