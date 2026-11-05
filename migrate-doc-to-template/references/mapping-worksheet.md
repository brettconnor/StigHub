# Mapping worksheet

Copy this file into the job's scratch folder and fill it in during Step 3.
Show the filled tables to the operator, and do not build until the operator
approves them.

## Job

| Item | Value |
|---|---|
| Source | `<path>` (SHA-256 `<hash>`) |
| Template | `<path>` (SHA-256 `<hash>`) |
| Output | `<folder>/<file name>` (must not exist yet) |
| Scratch folder | `<path>` |

## 1. Slot map

One row per template slot, in template order. Location uses inventory labels
(`B#`, `B# T# r# c#`).

| # | Template location | Template slot (placeholder / sample text) | Source location | Source content (short) | Action | Notes |
|---|---|---|---|---|---|---|
| 1 | B30 | `<Add System Name>` | B24 | Example System | fill | |
| 2 | B39 T1 r1-r2 | 2 component rows | B70 T2 r1-r4 | 4 components | fill + clone 2 rows | |
| 3 | B56 | `<Add System Diagram>` | B90 image rId11 | network diagram | picture, 6.0 in wide | legend dropped |

Actions: `fill`, `fill + clone N`, `remove blank rows`, `picture`,
`leave placeholder`, `restructure (approved)`.

## 2. Template slots with no source data

These keep the template placeholder text.

| Template location | Placeholder |
|---|---|

## 3. Source content with no template slot

Dropped unless the operator approves adding it.

| Source location | Content |
|---|---|

## 4. Markings and metadata found in the source

Never copied, whatever the operator decides.

| Location | Finding |
|---|---|

## 5. Source inconsistencies and leftover filler

Reported only; not fixed.

| Location | Issue |
|---|---|

## 6. Template boilerplate that may not fit

Reported only; not edited.

| Template location | Text | Why it may not fit |
|---|---|---|

## 7. Open questions (ask all at once)

1.

## Final report layout (Step 7)

1. Output path, plus confirmation that the template and source were checked by SHA-256 and are unchanged.
2. What was filled, including rows or paragraphs added by cloning.
3. Placeholders still open, with locations.
4. Source content dropped.
5. Markings and metadata not copied.
6. Source inconsistencies and leftover filler.
7. Assumptions and wording changes.
8. Template boilerplate that may not fit.
9. File properties inherited from the template.
10. Ask the operator to check the layout in Word.
