# Deferred staff-intake UX polish

**Observed:** Local browser verification of PR #102 at `develop@2783415dd19027428bf2036730b6c0d83f23ab3c`, 2026-09-14. These are non-blocking polish items. The owner requested keeping this note for the next docs-update PR; it is not part of PR B implementation scope.

- [ ] Align intake action buttons with the established workspace button styles, including disabled, pending and keyboard-focus states.
- [ ] Add clear field-level validation guidance alongside section-level save failures, in English and Spanish. Preserve fixed safe errors and avoid reflecting restricted values in shared messages or logs.
- [ ] Refresh the applicable draft list after acknowledged creation so stale “No drafts found” copy does not sit beside a successfully saved intake. Preserve applied search filters, cursor validity and dirty section buffers.

Regression acceptance: retain independent section save state, original-key recovery for unknown outcomes, unsaved edits during response/refetch, restricted-address disclosure rules, bilingual parity and narrow/keyboard usability.

Separate verification follow-ups: native leave-dialog cancel/stay was browser-tool limited; full manual accessibility/fluent-language checks, zoom and reduced-motion testing remain unrun. These are evidence gaps, not proven product defects.

Browser evidence is preserved in commit `ee82615` on `test/staff-intake-browser-ux`, including `docs/review-handoffs/2026-09-14-staff-intake-browser-ux.md`. Bring this note and that evidence into the next docs update; do not silently include deferred polish implementation in PR B.

## Owner feedback — 2026-09-15, reassess after PR D

- Finish PR C, then implement PR D canonical corrections/current-facts review before reassessing workspace navigation and revision UX.
- Make Employer intakes the onboarding/review entry point and assess Employers as the ongoing employer record workspace after PR D; the present name/type-only revision surface is an intermediate state.
- Plan a configuration menu with a user-selected display/input timezone. Eastern Time is the initial agency preference; use a named timezone such as America/New_York to handle EST/EDT by date, with automatic conversion to/from UTC. Staff should use ordinary date/time controls and not calculate offsets. Include localized display of follow-up/work times/history, explicit daylight-saving ambiguity handling and unchanged date-only semantics.
- These are deferred product directions, not PR C implementation or completed configuration functionality.
