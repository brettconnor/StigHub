# IOS-XE PKI private-key management

Cisco source reviewed **23 November 2026** for
SRG-NET-000165-VPN-000570.

## Cisco guidance

Cisco's [IOS XE CA-signed certificate configuration guide](https://www.cisco.com/c/en/us/support/docs/security-vpn/public-key-infrastructure-pki/220422-configure-ca-signed-certificates-with-io.html)
describes the key/PKI workflow: generate a key, link it to a trustpoint,
enroll for a certificate, authenticate CA certificates, and import the
identity certificate. It explains that the `exportable` suffix permits use
of `crypto pki export`, and its verification example uses
`show crypto key mypubkey ec <key-label>` to inspect key type, storage, and
whether a key is exportable. The guide's RSA-specific conversion example
must not be assumed to apply to EC keys or every IOS XE release.

The project X.509 template names a dedicated P-256 EC key
`VPN-IDENTITY-KEY` and binds it to `VPN-TP` with `eckeypair`. Its sample
generation command omits the `exportable` suffix. Confirm the resulting
key's exportability and storage on the target IOS XE platform/release rather
than inferring it from the template.

## SRG applicability and evidence limits

When PKI device authentication is in use, SRG-NET-000165-VPN-000570 calls
for a FIPS-compliant key-management process. A non-exportable key and
restricted administrative access are useful controls, but do not by
themselves establish that the platform's key generation and storage are
inside an applicable FIPS-validated cryptographic boundary. Identify the
exact PID and IOS XE release, applicable validation/certificate and
operating mode, key-generation/storage path, and authorized key-use
procedures before assigning `Met`. Verify key properties and trustpoint
binding on the device; repository configuration is not device evidence.

This source does not establish FIPS validation or operating-mode support
for every router PID/release in the project.
