# IOS-XE FIPS evidence for VPN private-key management

Reviewed **23 November 2026** for SRG-NET-000165-VPN-000570 and
SRG-NET-000230-VPN-000770.

The operator states that VPN-capable Cisco IOS-XE router families have
family/release-specific compliance letters identifying the same applicable
NIST CMVP certificates. The linked C8KV letters below are representative
examples; use the letter matching the exact platform and approved release.

## Cisco product-to-module statements

- Cisco's [C8KV IOS XE 26.2 internal compliance letter](https://www.cisco.com/c/dam/en_us/solutions/industries/government/security_certification/pdfs/cisco-c8kv-routers-running-ios-xe-26-2-internal-compliance-letter.pdf)
  identifies IOS XE 26.2 and the Cisco C8KV platform, cites IC2M Rel5b
  (CMVP #5356) and CiscoSSL FIPS Provider 8.0 (CMVP #5430), and lists IPsec
  among the applicable services. Cisco states the modules initialize in
  their approved manner and handle applicable cryptographic algorithms for
  the listed services.
- Cisco's [C8KV IOS XE 17.18 internal compliance letter](https://www.cisco.com/c/dam/en_us/solutions/industries/government/security_certification/pdfs/c8kv-routers-running-ios-xe-17-18-internal-compliance-letter.pdf)
  cites IC2M Rel5b CMVP #4752 for the product/release.

## NIST CMVP status and caveats

- [Certificate #5356](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/5356)
  is the active FIPS 140-3 Level 1 IC2M Rel5b certificate, with a sunset
  date of 6 August 2029. It requires approved-mode operation and explicitly
  provides no assurance of minimum strength for generated SSPs (including
  keys), or minimum security for externally loaded SSPs.
- [Certificate #5430](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/5430)
  is the active FIPS 140-3 Level 1 CiscoSSL FIPS Provider certificate, with
  a sunset date of 17 November 2029. It requires approved-mode operation
  and provides no assurance of minimum security for externally loaded SSPs
  or SSPs established with externally loaded SSPs.
- [Certificate #4752](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/4752)
  is Historical and replaced by #5356. Its listed tested configuration is
  IOS XE 17.12 on an ASR 1001-HX; its caveat also disclaims assurance of
  minimum strength of generated SSPs.

## SRG-NET-000165-VPN-000570 application

For Cisco IOS-XE VPN routers running approved versions, the matching Cisco
compliance letter and the active CMVP certificates provide product/release
and IPsec module evidence. Pair that evidence with the X.509 configuration's dedicated,
locally generated P-256 EC key (`VPN-IDENTITY-KEY`), its `VPN-TP`
`eckeypair` binding, non-exportable key state, and operation in the
applicable approved mode. Cisco's key-management guide documents the
`exportable` generation suffix and `show crypto key mypubkey ec` inspection;
verify the actual target key rather than assuming exportability from the
template. Avoid externally generated/imported private keys.

This is a defensible `Met` basis for each exact platform/release covered by
its matching Cisco letter after required key and approved-mode evidence is
verified; it does not automatically cover every IOS XE version or every
private-key management process. In particular, do not use the 17.18
letter's historical #4752 citation as current assurance without a current
Cisco-to-CMVP mapping for the exact platform and release. The NIST caveat
about generated SSP strength makes explicit P-256 key configuration and
device verification material.

## SRG-NET-000230-VPN-000770 application

For the IOS-XE VPN router, defer to NIST CMVP validation of the cryptographic
modules, using the matching Cisco family/release compliance letter to map
the product and IPsec service to the validated modules. The site-to-site PSK
template uses AES-GCM-256, a SHA-256 IKEv2 PRF, group 19, and peer-specific
IKEv2 pre-shared-key authentication, with the IKEv2 profiles bound to the
AES-GCM IPsec transform. These are the approved cryptographic services used
by the router's validated modules for the VPN.

This assessment pattern treats the control as `Met` for the supported
platform/release combinations covered by the matching Cisco letter and
NIST's approved-mode CMVP validation. `show version` and the targeted
configuration checks in the product record identify the device software and
configured mechanisms; they are not substitutes for the matching product
letter or proof of the live device's operating state.

Sources:

- [NIST CMVP #4752](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/4752)
- [NIST CMVP #5356](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/5356)
- [NIST CMVP #5430](https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/5430)
- [Cisco IOS XE CA-signed certificate configuration guide](https://www.cisco.com/c/en/us/support/docs/security-vpn/public-key-infrastructure-pki/220422-configure-ca-signed-certificates-with-io.html)
