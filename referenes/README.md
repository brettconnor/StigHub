# Cisco Catalyst 8000 reference snapshot

Retrieved from public Cisco documentation on **5 November 2026**.
The directory spelling `referenes` follows the requested destination.
Cisco documents retain their original content and copyright notices.
Nothing in this snapshot establishes certification, compliance, live-device
testing, stock availability, or a fielding approval.

## IKEv2 protocol reference

- [IKEv2 Packet Exchange and Protocol-Level Debugging](./IKEv2-packet-exchange.md)
  — Cisco's IKEv1/IKEv2 exchange comparison and terminology.
- [IOS-XE IKEv2 session termination](./iosxe-ikev2-session-termination.md)
  — periodic DPD for site-to-site peer sessions, Child-SA teardown, and
  the distinction from forwarded inner TCP connections.
- [IOS-XE VPN router service inventory — draft](./iosxe-service-inventory-matrix.md)
  — proposed service review matrix, evidence and unresolved platform coverage.
- [IOS-XE IPsec anti-replay](./iosxe-ipsec-anti-replay.md)
  — Cisco-documented ESP sequence-number replay protection, default window,
  configuration and active-SA verification.
- [IOS-XE IKEv2/IPsec PKI path validation](./iosxe-pki-path-validation.md)
  — certificate-chain validation, trust anchors, revocation status, and
  conditional scope for SRG-NET-000164-VPN-000560.
- [IOS-XE PKI private-key management](./iosxe-pki-private-key-management.md)
  — Cisco key-generation/exportability guidance and the evidence needed to
  assess SRG-NET-000165-VPN-000570.
- [IOS-XE FIPS evidence for VPN private-key management](./c8kv-fips-key-management.md)
  — Cisco compliance letters (with C8KV examples), NIST module
  status/caveats, and the configuration/evidence basis for
  SRG-NET-000165-VPN-000570.
- [IOS-XE VPN-to-IDPS routing](./iosxe-vpn-idps-routing.md)
  — VTI post-decryption routing, static routes for protected prefixes, and
  the PBR alternative for all ingress traffic.

## Product IDs

These are the platform IDs listed in the latest family datasheets found,
not a claim that every model is newly introduced in 2026. Minimum releases
below are initial platform support requirements, not upgrade recommendations.
See [product-ids.csv](./product-ids.csv) for machine-readable values.

| Family | Platform/ordering PID | Minimum IOS XE from datasheet |
| --- | --- | --- |
| C8200 | `C8200-1N-4T` | 17.4.1 |
| C8200L | `C8200L-1N-4T` | 17.5.1 |
| C8300 | `C8300-2N2S-4T2X` | 17.3.2 |
| C8300 | `C8300-1N1S-4T2X` | 17.3.2 |
| C8300 | `C8300-2N2S-6T` | 17.3.2 |
| C8300 | `C8300-1N1S-6T` | 17.3.2 |
| C8500 | `C8500-20X6C` | 17.10.1 |
| C8500 | `C8500-12X4QC` | 17.3.2 |
| C8500 | `C8500-12X` | 17.3.2 |
| C8500L | `C8500L-8S4X` | 17.4.1a |
| C8000V | `L-DNA-C8000V` | Subscription ordering PID; not a hardware platform |

C8000V is virtual software, not a physical chassis. Its datasheet describes
deployment-dependent subscription/marketplace buying options. The separate
ordering guide identifies `L-DNA-C8000V`; this is a top-level subscription
ordering PID, not a complete SKU selection. Tier, term, bandwidth, cloud
marketplace, and contractual choices still require ordering validation.
The older ordering guide is supplemental, not a newer datasheet.

For accessory/module and other table details, see the original documents
and [source-tables.csv](./source-tables.csv). That export preserves table rows;
it is not an automatically certified compatibility matrix.

## Latest versus recommended software

- **Latest published release found:** IOS XE **26.2.1**, release-note series
  **26.2.x**, for C8200/C8300, C8500, and C8000V. Each downloaded release-note
  document explicitly identifies 26.2.1 as the first release in that series.
- Cisco's [IOS XE 26 availability index](./IOS-XE-26-release-index.html)
  lists 26.2.1 as available, released **31 August 2026**.
- Cisco's [stable-release guidance](./IOS-XE-recommended-releases.pdf),
  updated **15 June 2026**, recommends **17.12.8 or 17.15.6** for these
  families, depending on feature requirements.
- Latest is not synonymous with recommended. The recommendation predates
  the 26.2 release; do not infer that 26.2.1 is the preferred production
  release. Check current guidance, exact hardware, operating mode, features,
  ROMMON prerequisites, caveats, security advisories, and lifecycle status
  before deployment.
- The existing IOS XE 17 draft package should not be silently relabeled
  IOS XE 26. Release migration and assessment applicability are separate
  decisions. No Word documents were changed by this download task.

## Downloaded documents

Every PDF below also has a same-basename HTML snapshot.
HTML snapshots may reference online images, scripts, or styles; use the PDFs
for self-contained offline reading.

| Document | Cisco HTML update date | Local PDF |
| --- | --- | --- |
| C8200 datasheet | 6 October 2026 | [PDF](./C8200-datasheet.pdf) |
| C8300 datasheet | 6 October 2026 | [PDF](./C8300-datasheet.pdf) |
| C8500 datasheet | 9 October 2026 | [PDF](./C8500-datasheet.pdf) |
| C8000V datasheet | 22 August 2025 | [PDF](./C8000V-datasheet.pdf) |
| C8200/C8300 26.2.x release notes | 27 September 2026 | [PDF](./C8200-C8300-IOS-XE-26.2.x-release-notes.pdf) |
| C8500 26.2.x release notes | 27 September 2026 | [PDF](./C8500-IOS-XE-26.2.x-release-notes.pdf) |
| C8000V 26.2.x release notes | 27 September 2026 | [PDF](./C8000V-IOS-XE-26.2.x-release-notes.pdf) |
| C8000V ordering guide | 6 August 2024 | [PDF](./C8000V-ordering-guide.pdf) |
| Stable-release guidance | 15 June 2026 | [PDF](./IOS-XE-recommended-releases.pdf) |

The C8000V PDF cover says version 3.2, 19 August 2025; its HTML page update
date is 22 August 2025. Page update dates need not equal document cover dates.

Source URLs, retrieval timestamps, byte sizes, page titles, and SHA-256
digests are recorded in [download-manifest.json](./download-manifest.json).
PDF headers and parsing, HTML titles, platform IDs, release identifiers,
and all recorded file digests were checked locally.
