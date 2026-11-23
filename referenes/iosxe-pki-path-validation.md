# IOS-XE IKEv2/IPsec PKI path validation

Cisco sources reviewed **23 November 2026** for
SRG-NET-000164-VPN-000560.

## Cisco sources and supported behavior

- Cisco's [IOS XE 16.12 PKI authorization, revocation, and certificate-chain validation guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_pki/configuration/xe-16-12/sec-pki-xe-16-12-book/sec-cfg-auth-rev-cert.html)
  describes validating peer certificate chains to a trusted certificate
  (trustpoint), configuring CRL or OCSP checks, and configuring chain
  validation. It states that a chain is processed to the first trusted
  certificate and documents that failed revocation retrieval rejects the
  peer unless revocation checking is explicitly bypassed.
- Cisco's [IOS XE CA-signed certificate configuration guide](https://www.cisco.com/c/en/us/support/docs/security-vpn/public-key-infrastructure-pki/220422-configure-ca-signed-certificates-with-io.html)
  documents importing/authenticating root and intermediate CA certificates
  with `crypto pki authenticate`; each IOS XE trustpoint stores a single CA
  certificate. Exact configuration support varies by release and platform.
- The [IOS XE IKEv2 configuration guide](https://www.cisco.com/c/en/us/td/docs/ios-xml/ios/sec_conn_ike2vpn/configuration/xe-16-11/sec-flex-vpn-xe-16-11-book/sec-cfg-ikev2-flex.html)
  documents IKEv2 certificate authentication and selecting a PKI trustpoint
  in an IKEv2 profile.

## SRG applicability and template notes

SRG-NET-000164-VPN-000560 is conditional: it applies when the VPN Gateway
uses PKI-based authentication. The PSK-only variant has no certificate path
to validate. When the X.509 variant is deployed, the requirement applies;
IOS XE supports PKI path validation for VPN peers. The template's
`revocation-check ocsp crl` selects OCSP first and CRL fallback for status
checking, but actual trust-anchor and intermediate CA certificates must
also be authenticated and provisioned. The certificate subject/issuer maps
restrict peer identity; they do not themselves build or validate the
certificate chain.

The templates contain placeholders, not actual CA or identity certificates.
No certificate properties could be parsed and no live router was tested.
Validate chain construction, trust anchors, OCSP/CRL retrieval and
fail-closed behavior on the exact deployed PID and IOS XE release.
