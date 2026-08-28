# Human qualification checklist

Status: not_run until an approved named-human qualification gate opens.

This checklist defines the value-safe manual evidence matrix for the private fictional-synthetic `develop` target. It is source guidance only; it does not grant tester access, service start, cloud access, or permission to run a human walkthrough.

## Required matrix rows

Every required row records pass/fail/not-run, tester role, language, evidence reference, and disposition. Use value-safe references to operator-held private evidence; do not paste raw private artifacts into tracked source.

| Row | browser | OS | device or viewport | assistive technology | network condition | language | Required coverage | Result | Evidence reference | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| macOS Safari English Employer path | macOS Safari | macOS | desktop viewport | keyboard only | normal | English | Employer create/read/search/revision/replay path | not-run | [operator-held] | pending |
| macOS Safari Spanish Employer path | macOS Safari | macOS | desktop viewport | keyboard only | normal | Spanish | Employer create/read/search/revision/replay path | not-run | [operator-held] | pending |
| Chromium desktop English Employer path | Chromium desktop | current desktop OS | desktop viewport | keyboard only | normal | English | Employer create/read/search/revision/replay path | not-run | [operator-held] | pending |
| Chromium desktop Spanish Employer path | Chromium desktop | current desktop OS | desktop viewport | keyboard only | normal | Spanish | Employer create/read/search/revision/replay path | not-run | [operator-held] | pending |
| accessibility keyboard/focus | current required browser | current desktop OS | desktop viewport | keyboard only | normal | English or Spanish | keyboard navigation and focus visibility | not-run | [operator-held] | pending |
| accessibility responsive reflow | current required browser | current desktop OS | narrow viewport | none | normal | English or Spanish | responsive reflow without content loss | not-run | [operator-held] | pending |
| accessibility reduced motion | current required browser | current desktop OS | desktop viewport | reduced motion | normal | English or Spanish | reduced motion behavior | not-run | [operator-held] | pending |
| accessibility text spacing | current required browser | current desktop OS | desktop viewport | text spacing override | normal | English or Spanish | text spacing support without content loss | not-run | [operator-held] | pending |
| accessibility contrast | current required browser | current desktop OS | desktop viewport | contrast review | normal | English or Spanish | contrast review outcome | not-run | [operator-held] | pending |
| refresh/back/forward/BFCache | current required browser | current desktop OS | desktop viewport | none | normal | English or Spanish | refresh/back/forward/BFCache behavior | not-run | [operator-held] | pending |
| constrained network | current required browser | current desktop OS | desktop viewport | none | constrained network | English or Spanish | loading and recovery behavior | not-run | [operator-held] | pending |
| safe error/recovery | current required browser | current desktop OS | desktop viewport | none | normal | English or Spanish | safe induced error/recovery state | not-run | [operator-held] | pending |

## Value-safety rules

Do not store submitted names, UUIDs, commands, cursors, tester identities, endpoints, tokens, screenshots containing sensitive values, or raw bodies in this tracked checklist or any tracked manual qualification artifact.

If any required row is failed or not-run, the target is not fully qualified for the human-feedback outcome. Record the blocker category and disposition without exposing raw private evidence.
