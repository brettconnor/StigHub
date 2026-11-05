# IOS-XE login banner reference

- Source: Cisco internal RS-Cookbook, IOS-XE general management recipe.
- URL: https://wwwin-github.cisco.com/gct-dp/RS-Cookbook/blob/master/Config%20Recipes/IOS-XE/cs-general-mgmt.cisco
- Accessed: 2026-11-04 through the GitHub Enterprise contents API.
- Evidence: the recipe includes a `banner login #` block containing the
  U.S. Government notice-and-consent text.
- Operator decision: `SRG-NET-000041-VPN-000110` is applicable to this
  project, including its site-to-site VPN router deployment.

The golden IPsec template currently lacks this block. Treat the recipe as
an operator-supplied supplemental configuration source, not as evidence
that a banner is already configured or validated on a device.

Compare the recipe's banner against the shared SRG's mandated wording
before adoption. The recipe wraps lines, adds asterisk borders, and uses
`USG authorized purpose` where the SRG says `USG-authorized purpose`.
Retain the source reference and resolve textual differences when preparing
the canonical configuration.
