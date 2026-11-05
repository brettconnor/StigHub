# IOS-XE per-user SSH session limit

- Source: Cisco internal RS-Cookbook, IOS-XE general management recipe.
- URL: https://wwwin-github.cisco.com/gct-dp/RS-Cookbook/blob/master/Config%20Recipes/IOS-XE/cs-general-mgmt.cisco
- Accessed: 2026-11-04 through the GitHub Enterprise contents API.
- Observed command: `ip ssh server peruser session limit 16`.
- Source annotation: `SRG-APP-000001-NDM-000200`.

The operator interprets `SRG-NET-000053-VPN-000170` as covering remote-access
VPN user sessions and has designated it out of scope for this site-to-site
deployment. The SSH command is not the selected fix for that rule.

The command limits SSH sessions per user, not
IPsec security associations or a device-wide session total. The shared VPN
SRG requires a limit of 1 or an organization-defined number documented in
the SSP. The recipe's value of 16 is not evidence of local SSP approval.
Verify applicable platform/release support and account access paths before
asserting complete enforcement. No live device validation was performed.
