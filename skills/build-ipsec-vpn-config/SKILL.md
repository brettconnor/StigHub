---
name: IPSec-VPN
description: Create, review, and document Cisco IOS XE site-to-site IKEv2/IPsec VTI configurations using this repository's canonical template and retained references.
---

# IPSec VPN configuration skill

Use this skill when creating, reviewing, cleaning up, or documenting Cisco
IOS XE site-to-site IPsec VPN configurations, especially IKEv2 route-based
virtual tunnel interfaces (VTIs), IPv4/IPv6 peers, or the canonical template
at `configs/cli/iosxe-ikev2-ipsec`.

## Repository source of truth

- Treat `configs/cli/iosxe-ikev2-ipsec` as the repository's canonical golden
  configuration template. Keep it readable, consistently indented, and
  placeholder-only. Do not silently diverge product answers from it.
- Use `VPN/Cisco-IOS-XE/<rule-id>/*.txt` for product-specific SRG answers.
  Distinguish what the template actually configures from what still needs
  deployment-specific implementation or verification.
- Consult [`references/README.md`](references/README.md) and
  [`references/iosxe-ipsec.md`](references/iosxe-ipsec.md) for retained web
  sources. Prefer the Cisco primary documentation relevant to the exact
  platform and release; treat community and lab examples as secondary.
- Repository references explain source claims; they are not proof that a
  configuration is supported, deployed, operational, compliant, or safe for
  a particular network.

## Workflow

1. Inspect the canonical template, target product/rule files, Git status,
   platform/model, IOS XE release, and relevant Cisco documentation before
   editing. Preserve existing operator changes.
2. Identify the requested outcome. Keep cleanup/layout work separate from
   changes to algorithms, topology, authentication, traffic selectors,
   routing, ACLs, or policy unless the task explicitly asks for those changes.
3. Make the smallest necessary edits. Preserve placeholders and distinguish
   example alternatives from commands that should be applied together.
4. Validate the rendered configuration against the target platform and
   release's Cisco command reference, feature support, release notes, and
   licensing requirements. If no device or parser is available, state that
   limitation; never imply that the config was device-tested.
5. Review the final diff, check for accidental credentials and obsolete
   cryptographic settings, and describe what is and is not established by the
   evidence.

## Configuration and security guidance

- Keep all addresses, interface names, peer identifiers, VLAN IDs, and
  secrets as clear placeholders in repository templates. Never introduce a
  real pre-shared key, password, private key, or certificate. Provision
  unique, strong per-peer secrets through the organization's approved secret
  management process.
- Use modern authenticated encryption and key exchange consistent with
  applicable policy and device support. Avoid deprecated/banned primitives
  such as AES-CBC, SHA-1, DES/3DES, MD5, and legacy ESP HMAC combinations.
  Prefer AEAD (such as supported AES-GCM) and strong DH/ECDH groups; verify
  exact IOS XE syntax and support instead of assuming it is portable.
- For AES-GCM IKE proposals, follow the target IOS XE documentation for
  required proposal transforms (including PRF and whether a separate
  integrity transform is omitted). For ESP AES-GCM, do not add a separate
  ESP HMAC transform.
- Keep peer keyring entries, IKEv2 profiles, IPsec profiles, and tunnel
  interfaces clearly associated. Check both IPv4 and IPv6 peer identity,
  endpoint, and address-family syntax. Avoid malformed combined CLI lines.
- Make mutually exclusive topology alternatives explicit—for example, a
  routed Layer 3 WAN port versus a Layer 2 port with an SVI. Do not present
  both alternatives as simultaneously applicable to the same interface.
- A VTI provides a tunnel interface and routing path; do not imply that peer
  authentication alone authorizes access to protected resources. Identify
  where traffic authorization is enforced, including both IPv4 and IPv6,
  and require verification of the deployed policy and traffic path.
- Do not add routing, ACLs, crypto maps, keepalives, MTU settings, licensing
  commands, or platform-specific workarounds without confirming need and
  support. Flag environment-dependent values for operator completion.
- Preserve the boundary between the example/template and active device
  configuration. No repository template is evidence of deployment or
  compliance by itself.

## Product SRG answer guidance

When answering an SRG for this template:

- Explain what the template actually demonstrates and what it does not.
- Use a **Not Reviewed** or equivalent status when only the template is
  available. Do not claim compliance without sanitized active configuration,
  policy references, and appropriate operational evidence.
- For authorization requirements, distinguish IKE peer authentication and
  encryption from authorization of tunneled source/destination resources.
  Check deployed routing, IPv4/IPv6 ACLs or other enforcement points, and
  approved positive and negative traffic tests.
- Describe evidence to collect without requesting or recording live secrets.
  Sanitize configurations before storing artifacts.
- Keep requirement, discussion, status, check, severity, fix, mitigation,
  artifact, and justification fields consistent with each other and with the
  shared DISA baseline.

## Retained references

See [`references/iosxe-ipsec.md`](references/iosxe-ipsec.md) for the dated
reference ledger. It records Cisco IOS XE IKEv2, VTI, transform-set, IPsec,
interface, and platform documents consulted, along with clearly labeled
secondary sources and scope caveats.