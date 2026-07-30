# Current Work — Golden Rose Operations Platform

**Updated:** 2026-07-30
**Lane:** Planning / discovery
**Overall status:** Phase 0 is in progress. No implementation, infrastructure provisioning, public release, or production-data use is authorized by this file.

## Active objective
Turn the completed initial discovery baseline into an approved, narrow first delivery: an agency-staff pilot for employer demand entry and retrieval, followed by a governed dashboard and transparent worker/employer comparison aid.

## Current evidence-backed direction
- The agency’s current operation is paper-first and fragmented across workbooks, hosted forms, Trello, calendars, messaging, and manual follow-up.
- Multiple legacy employer and worker forms overlap. The proposed replacement is one canonical staged workflow, not duplicate forms or response stores.
- The first usable product should serve agency members: enter employer demand, find/review requests, and replace manual metric collection with governed operational data.
- Employer demand is the proposed first entry workflow because current demand exceeds available worker supply.
- Worker profiles should follow quickly, but self-reported preferences/skills are not verified credentials and must not drive automatic ranking, eligibility, hiring, or referral.
- Public worker/employer access and higher-trust staff administration require materially separate security boundaries.

## Immediate next steps
1. Review this document set against the preliminary PRD with Beatrice and the client.
2. Obtain the outstanding business-model/legal-content and operational-policy decisions needed to define the staff pilot safely.
3. Convert the approved Phase 1 field inventory and workflow states into a concrete implementation plan.
4. Before any coding, re-baseline live Git state and create a purpose-named branch from the approved integration branch.

## Required decision gates before implementation
- Client/counsel-approved source and owner for public, legal, fee, retention, consent, and receipt/agreement content.
- Initial staff role/permission matrix, MFA/account-recovery posture, and support owner.
- Canonical field-purpose inventory for employer/contact/worksite/request/shift records.
- Approval of which legacy fields are excluded, staff-only, controlled extensions, or require neutral/counsel-reviewed treatment.
- Data classification, environment, synthetic-fixture, backup/recovery, and production-data pilot gate.

## Hard stop boundaries
- Do not collect or import unrestricted live personal data.
- Do not enable public workflows, uploads, payment, signatures, screening, or vendor integrations.
- Do not encode legacy language, protected-trait/proxy criteria, legal text, fee policy, retention rules, or business terms as production behavior.
- Do not implement automated matching, ranking, eligibility, hiring, or referral decisions.
- Do not start cloud services, provision accounts, or change client systems without explicit scoped approval.

## Repository-governance slice
- `develop` now exists from the initial `main` baseline and is the intended protected integration branch.
- Active branch: `docs/repository-governance-as-code`, which defines CI branch-source enforcement, repository policy IaC, verification scripts, and ADR-0001.
- Before applying GitHub protections, open and exercise this PR into `develop`; then apply and verify the committed policy for both protected branches.
- GitHub does not natively offer per-target merge-method enforcement. Feature work may squash into `develop`; `develop` → `main` promotions must use a merge commit under the documented release gate until a separately approved stronger mechanism exists.

## Repository bootstrap state
- The initial tracked baseline contains the living documents, ADR convention, and a protective `.gitignore`.
- Client-source artifacts, generated client PDFs, existing discovery/compliance/governance notes, and the PDF-generation script remain intentionally untracked pending a separate confidentiality/content review.
- The remote is `origin` at `https://github.com/b-mackenzie-alexander/golden_rose_project.git`; the initial `main` push establishes the default branch before governance-as-code work begins.

## Continuity sources
- Discovery and detailed evidence: currently local `docs/discovery/` and `docs/compliance/`; review and sanitize before a future tracked-documentation commit.
- Governance baseline: currently local `docs/governance/`; review and sanitize before a future tracked-documentation commit.
- Engagement evidence index: Obsidian note `Golden Rose Employment Agency - Engagement Index`.
- Stable project decisions: `TECHNOLOGY_DECISIONS.md` and `docs/adr/`.
- Execution checklist: `ROADMAP.md`.
