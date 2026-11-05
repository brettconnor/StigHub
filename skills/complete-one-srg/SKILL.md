---
name: complete-one-srg-requirment
description: Populate the product-specific files for one SRG requirement using the operator-defined steps.
---

# Complete one SRG requirement

Follow the steps below for the selected SRG and product. This workflow is
being defined incrementally; do not invent steps for other fields.

## Canonical examples: met by configuration

The operator-approved canonical examples of SRGs informally known as
"met by configuration" are:

- `VPN/Cisco-IOS-XE/SRG-NET-000015-VPN-000010/`
- `VPN/Cisco-IOS-XE/SRG-NET-000018-VPN-000015/`

Use these examples as the model for golden-template configuration fixes,
minimal `show` checks, concise affirmative justifications, and a `Met`
status. "Met by configuration" describes the authoring pattern; the value
in `status.txt` remains `Met`. Select controls for each new requirement
rather than copying an example's fix or status without assessing it.

## Deployment and assessment scope

The assessed Cisco IOS-XE device is a VPN router deployed exclusively for
site-to-site traffic. Firewall and IDPS functions, configuration, and
deployment evidence are outside this project's assessment scope. Apply
this operator-established scope without requesting reconfirmation.

For `SRG-NET-000019-VPN-000040`, assess the router's inbound/outbound IPsec
security policy and ESP tunnel-mode configuration. Do not make its
router-scoped status depend on firewall/IDPS topology or inspection evidence.
Keep the shared SRG text and copied VulDiscussion verbatim; this scope
decision guides product-specific fix, check, justification, and status
authoring rather than rewriting the source requirement. Keep conclusions
limited to the assessed VPN router.

The operator has designated `SRG-NET-000041-VPN-000110` as applicable.
Do not classify this login-banner requirement as out of scope solely
because the deployment is site-to-site. Its configuration is absent from
the golden IPsec template; the operator-supplied supplemental source is
the RS-Cookbook IOS-XE general management recipe, whose `banner login`
block provides the notice-and-consent banner. See
`skills/build-ipsec-vpn-config/references/login-banner.md` for the source
and verification notes. A missing golden-template control is not itself
evidence of nonapplicability. Use the operator-approved supplemental source
directly under Step 4; do not add the banner to the golden template.

For `SRG-NET-000042-VPN-000120`, the operator accepts the IOS-XE
banner-then-login sequence as satisfying acknowledgment: the notice is
presented before authentication, and the user explicitly proceeds with
login. Use the same approved `banner login` configuration as the preceding
banner-display SRG and author its status as `Met` under this interpretation.
Do not require a separate GUI click-through control or reconfirm this
decision. This is an operator-established assessment interpretation, not a
record of device testing.

For `SRG-NET-000053-VPN-000170`, the operator interprets user sessions as
remote-access VPN user sessions. The assessed deployment provides
site-to-site IPsec connectivity between routers, so use the out-of-scope
workflow and `Not Applicable` status. Do not substitute administrator SSH
session limits for VPN user-session controls. This decision is specific to
this rule and preserves the established applicability of the banner SRGs.

The golden template covers only site-to-site VPN configuration. Keep
general management controls, including login banners, in their approved
supplemental sources rather than expanding that template.

The operator has designated `SRG-NET-000019-VPN-002435` as fully outside
the assessed product's scope because TLS VPN is unsupported in this
site-to-site IOS-XE VPN router project. Complete Steps 1-3 for out-of-scope
rules as usual. Preserve technology-specific scope such as `TLS VPN` in
the requirement; noun substitution must not turn a TLS-specific obligation
into a generic IPsec router obligation. For out-of-scope rules, Steps 4
and 5 write exactly `NA` followed by a newline to `fix.txt` and `check.txt`,
respectively, instead of configuration or show commands. Step 6 writes a
simple, concise explanation of why the requirement is not applicable in
`justification.txt`, using the same plain-text style as the previous
examples. State the assessed product's role or supported technology and
connect it directly to the applicability decision; omit unrelated caveats
and gap analyses. This applicability rationale is the exception to Step 6's
configuration-focused wording. Step 7 writes exactly `Not Applicable`
followed by a newline to `status.txt`.

## Policy selection

Always use the existing, simpler operator-established policy when one
applies to the requirement. Reuse it without asking the operator to choose
again or expanding its scope with additional restrictions. For this VPN
project, the established WAN ingress policy permits only peer-specific IKE
and native ESP; use that policy for applicable access and information-flow
controls.

Ask for policy clarification only when no applicable policy exists or a
specific requirement remains unsupported by the existing policy and golden
configuration. Do not invent policy approvals or claim unsupported coverage.

## Step 1: Populate severity.txt

1. Read the selected rule's top-level shared SRG text at
   `<srg>/<rule-id>/srg.txt`.
2. Copy the value under `Severity:` into
   `<srg>/<product>/<rule-id>/severity.txt`, preserving its spelling and case.
3. Write only the severity value followed by a newline. Do not include
   `Severity:`, `SEVERITY:`, the rule ID, a viewer heading, or commentary.
4. Verify that the destination value matches the source severity exactly.

Example source: `VPN/SRG-NET-000015-VPN-000010/srg.txt`

```text
Severity:
medium
```

Result: `VPN/Cisco-IOS-XE/SRG-NET-000015-VPN-000010/severity.txt`

```text
medium
```

The viewer may display `===== severity.txt =====` above the value; that
heading is not part of the file contents.

## Step 2: Populate requirement.txt

1. Read the requirement under `SRG Requirement:` in the same top-level shared
   `<srg>/<rule-id>/srg.txt`.
2. Determine the project-specific noun for the selected product from the
   project context. For Cisco IOS-XE, use `Cisco IOS-XE VPN router`.
3. Identify the generic noun phrase that refers to the product being
   assessed, such as `VPN Gateway`, and replace it with the project-specific
   noun where appropriate. Use context rather than a blind global
   replacement: do not rename other entities mentioned in the requirement.
   Preserve the article and make only grammatical adjustments necessary for
   the substituted noun.
4. Preserve the rest of the source requirement, including its obligations,
   scope, and policy references. Do not add implementation details,
   interpretation, or compliance claims.
5. Write the resulting requirement text followed by a newline to
   `<srg>/<product>/<rule-id>/requirement.txt`. Do not include
   `SRG Requirement:`, `REQUIREMENT:`, the rule ID, or a viewer heading.
6. Verify that only the appropriate product noun and any necessary grammar
   changed from the shared requirement.

Example source: `VPN/SRG-NET-000015-VPN-000010/srg.txt`

```text
The VPN Gateway must enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies.
```

Result: `VPN/Cisco-IOS-XE/SRG-NET-000015-VPN-000010/requirement.txt`

```text
The Cisco IOS-XE VPN router must enforce approved authorizations for logical access to information and system resources in accordance with applicable access control policies.
```

## Step 3: Populate vuldiscussion.txt

1. Read the selected rule's VulDiscussion in the top-level shared
   `<srg>/<rule-id>/srg.txt`.
2. Copy the discussion verbatim into
   `<srg>/<product>/<rule-id>/vuldiscussion.txt`, preserving its wording,
   punctuation, and paragraph breaks. Do not substitute product nouns,
   summarize, or add interpretation.
3. Include only the discussion text followed by a newline, without the
   source section label, a viewer heading, or commentary.
4. Verify that the destination discussion matches the source exactly.

## Step 4: Populate fix.txt

1. Read the selected requirement and the canonical golden configuration
   template at `configs/cli/iosxe-ikev2-ipsec`. For applicable controls
   outside its site-to-site VPN scope, use an operator-approved supplemental
   source directly and retain its web reference under
   `skills/build-ipsec-vpn-config/references/`.
2. Identify the configuration block(s) from the selected source needed to meet the
   requirement. Include the necessary configuration context and directly
   required dependencies, but exclude unrelated blocks.
3. Copy those blocks into `<srg>/<product>/<rule-id>/fix.txt`, preserving
   their commands, indentation, placeholders, and relative order.
4. Include only the configuration block(s). Do not add a `FIX:` label,
   Markdown code fences, a viewer heading, explanatory prose, or commands
   invented outside the golden template or approved supplemental source.
5. Verify that every copied command comes from the selected source and is
   relevant to meeting the requirement. End the file with a newline.

If neither the golden template nor an approved supplemental source contains
the configuration needed to meet the requirement, report that gap to the
operator rather than inventing a fix or presenting unrelated configuration
as sufficient. Do not change the golden template as part of this step.

## Step 5: Populate check.txt

1. Read the selected rule's `fix.txt`.
2. Select the minimal IOS `show` commands needed to view its configuration
   blocks and interface attachments. Prefer targeted running-configuration
   sections or interfaces over dumping the entire configuration.
3. Write only those commands, one per line, to
   `<srg>/<product>/<rule-id>/check.txt`. Preserve the fix's names and
   placeholders. Do not include prompts, headings, Markdown fences,
   expected output, assessment prose, or configuration-changing commands.
4. Cover each distinct block without redundant commands. If the fix has
   mutually exclusive interface alternatives, include a command for each;
   the operator runs only the command for the deployed alternative.
5. Verify that the commands expose every configuration block in `fix.txt`
   and end the file with a newline. Viewing configuration alone does not
   establish operational behavior or compliance.

## Step 6: Populate justification.txt

1. Read the selected rule's `requirement.txt` and `fix.txt`, together with
   relevant operator decisions from the agent/human conversation.
2. Explain why the proposed configuration in `fix.txt` meets the obligations
   in `requirement.txt`. Connect the specific configuration controls to the
   required behavior and the applicable approved access-control policy;
   do not merely restate the requirement or list commands.
3. Use agent/human back-and-forth when needed to establish policy intent,
   scope, assumptions, or how the proposed controls satisfy the requirement.
   Do not invent policy approvals or treat unresolved assumptions as facts.
4. Keep the rationale concise and affirmative: state only what the
   configuration does and why that behavior supports the requirement.
   Never describe what the configuration does not do. Exclude gap analyses,
   caveats, deployment warnings, and unrelated controls from this file.
   Discuss unresolved questions or gaps separately with the operator;
   keep every written claim supported and do not silently change `fix.txt`
   or the golden template.
5. Write the resulting rationale as one or two short plain-text paragraphs in
   `<srg>/<product>/<rule-id>/justification.txt`, ending with a newline.
   Do not include a `JUSTIFICATION:` label, viewer heading, Markdown fences,
   or the conversation transcript.
6. Verify that each claim is supported by the proposed configuration,
   established operator decisions, or explicitly identified dependencies.
   A proposed solution's rationale is not proof of deployment or a passing
   assessment.

## Step 7: Populate status.txt

1. Review the selected requirement, proposed fix, and justification,
   together with relevant operator decisions.
2. Select the status:
   - `Not Applicable`: the requirement is outside the established assessment
     scope, as explained in `justification.txt`.
   - `Met`: a suitable fix satisfies the requirement.
   - `Mitigated with RAE`: a suitable fix is unavailable, but mitigation
     with RAE is established with the operator.
   - `Not Met`: the requirement applies, a suitable fix is unavailable,
     and mitigation with RAE is not established.
3. Use agent/human discussion as needed to determine whether the fix is
   suitable or mitigation with RAE applies. Do not infer either solely
   from the presence of a populated file or invent an RAE decision.
4. Write only the selected status, with the exact spelling and case above,
   followed by a newline, to `<srg>/<product>/<rule-id>/status.txt`.
   Do not include a label, explanation, or viewer heading.