# IOS XE IPsec and IKEv2 references

These are the web references gathered while reviewing
the golden VPN template on 2026-11-04. The current variants are
`configs/cli/iosxe-ikev2-ipsec-psk.cisco` and
`configs/cli/iosxe-ikev2-ipsec-x509.cisco`. References are retained here so
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

## X.509 peer authentication and authorization update (2026-11-19)

The operator requested separate PSK and X.509 authentication variants.
`configs/cli/iosxe-ikev2-ipsec-psk.cisco` retains the established PSK
configuration; `configs/cli/iosxe-ikev2-ipsec-x509.cisco` uses mutual ECDSA
authentication, an explicitly selected PKI trustpoint with OCSP-first
revocation checking and CRL fallback,
and per-path certificate maps requiring the full approved peer subject and
issuer DNs. This is static router-peer authorization, not user MFA, AAA
account authorization, or authorization of decrypted LAN traffic. The
peer-specific WAN ACL and IPsec/VTI blocks are unchanged and identical in
both variants. Choose one variant, not both. X.509 is not a prerequisite
for the `Not Applicable` disposition of SRG-NET-000140-VPN-000500 in the
established account/deployment scope.

The IPv4 and IPv6 IKEv2 profiles retain their names and are distinguished by
their local WAN addresses. Their certificate maps may name the same
dual-stack peer or distinct approved peers. IOS ORs `match identity` and
`match certificate`; the former remote-address matches were removed rather
than retained as certificate-map bypasses. Local-address and certificate
matches are different types and are ANDed.

Sources checked:

- The [Cisco IOS XE IKEv2 guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ike2vpn/configuration/xe-16-11/sec-flex-vpn-xe-16-11-book/sec-cfg-ikev2-flex.html)
  documents `ecdsa-sig`, local DN identity, trustpoint selection,
  IPv4/IPv6 local-address matching, and the OR/AND profile-matching rules.
- The [Cisco IKEv2 certificate example](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ike2vpn/configuration/xe-16-11/sec-flex-vpn-xe-16-11-book/sec-apx-ikev2-legacy.html)
  demonstrates certificate-map selection of an IKEv2 profile.
- [Cisco CA-signed certificate provisioning](https://www.cisco.com/c/en/us/support/docs/security-vpn/public-key-infrastructure-pki/220422-configure-ca-signed-certificates-with-io.html)
  documents EC key generation, `eckeypair`, terminal enrollment, CA
  authentication and identity-certificate import. Each trustpoint holds
  one CA certificate; configure intermediate/root trustpoints as required
  by the approved hierarchy instead of overwriting one trustpoint repeatedly.
- [Cisco PKI authorization and revocation guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_pki/configuration/xe-16-12/sec-pki-xe-16-12-book/sec-cfg-auth-rev-cert.html)
  documents ordered revocation methods and rejection when status checking
  fails without a `none` fallback. The operator prefers OCSP, then CRL.

Before deployment, verify exact PID/release support (including ISR 4000
and ASR 1000), both peers' ECDSA support, securely provisioned P-256 keys,
approved identity/CA chains, DN formatting, certificate usages, current
validity, key strength and signature algorithms. Reject unexpected
self-signed peer certificates; intentionally provisioned root trust
anchors require independently verified fingerprints. The template contains
no certificate bytes to parse or validate.

Configure trusted time and ensure OCSP and CRL services are available over
a permitted management/OOB path: the existing WAN ACL does not permit general PKI
retrieval traffic. Do not work around availability problems with
`revocation-check none` or a fallback authentication method. Validate
revocation behavior on the target: `revocation-check ocsp crl` selects OCSP
first and CRL as the fallback method. Verify AIA/CDP retrieval locations,
responder trust, revoked/unknown responses, OCSP outages, stale/unreachable
CRLs, and rejection when neither method establishes acceptable status.

This is a candidate configuration, not a tested migration script. Applying
it to an existing PSK router requires reviewing/removing old profile
authentication, keyring bindings and overlapping profiles; do not assume
pasting the new template removes old commands. No router was changed.
Previously authored SRG fixes remain snapshots; they were not regenerated
by this template-only change.

Focused static validation checks the reference chain, mutual ECDSA,
certificate allowlists, absence of PSK/remote-identity bypasses, and
preservation of the WAN/IPsec/VTI blocks. Live acceptance must establish
both address-family tunnels and reject wrong-subject/wrong-issuer peers
(including other peers with valid certificates from the same CA), untrusted,
expired/revoked certificates and PSK attempts. Check negotiated IKEv2
authentication, rekey and data flow; configuration display alone is not
proof of authorization enforcement.

## Scope notes

- These references were collected for research and traceability. No
  configuration was applied to a router or validated with a device CLI.
- AES-GCM support, IKEv2 PRF configuration, DH groups, IPv6 VTI behavior,
  keyring syntax, interface syntax, licensing, and hardware acceleration
  vary by product and IOS XE release.
- The reference set does not establish that the repository template is
  deployable as-is, that traffic authorization is configured, or that a
  device meets an SRG.
