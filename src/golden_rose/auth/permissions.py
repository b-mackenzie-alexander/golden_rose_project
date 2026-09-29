from golden_rose.auth.principal import StaffPrincipal

CREATE_DRAFT_EMPLOYER_PERMISSION = "employer:draft:create"
EMPLOYER_DRAFT_REVISE_PERMISSION = "employer:draft:revise"
EMPLOYER_READ_PERMISSION = "employer:read"
EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION = "employer_contact:draft:create"
EMPLOYER_CONTACT_READ_PERMISSION = "employer_contact:read"
STAFF_ACCOUNT_CREATE_PERMISSION = "staff_account:create"
STAFF_ACCOUNT_ACTIVATE_PERMISSION = "staff_account:activate"
STAFF_ACCOUNT_SUSPEND_PERMISSION = "staff_account:suspend"
STAFF_ACCOUNT_DEPROVISION_PERMISSION = "staff_account:deprovision"
STAFF_ACCOUNT_READ_PERMISSION = "staff_account:read"
STAFF_ACCOUNT_RECOVERY_RECORD_PERMISSION = "staff_account:recovery:record"
STAFF_ACCOUNT_SESSION_REVOKE_PERMISSION = "staff_account:session:revoke"
STAFF_ACCOUNT_DELEGATION_GRANT_PERMISSION = "staff_account:delegation:grant"
STAFF_ACCOUNT_DELEGATION_REVOKE_PERMISSION = "staff_account:delegation:revoke"


def can_create_draft_employer(principal: StaffPrincipal) -> bool:
    return CREATE_DRAFT_EMPLOYER_PERMISSION in principal.permissions


def can_revise_draft_employer(principal: StaffPrincipal) -> bool:
    return EMPLOYER_DRAFT_REVISE_PERMISSION in principal.permissions


def can_read_employer(principal: StaffPrincipal) -> bool:
    return EMPLOYER_READ_PERMISSION in principal.permissions


def can_create_draft_employer_contact(principal: StaffPrincipal) -> bool:
    return EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION in principal.permissions


def can_read_employer_contact(principal: StaffPrincipal) -> bool:
    return EMPLOYER_CONTACT_READ_PERMISSION in principal.permissions


def can_create_staff_account(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_CREATE_PERMISSION in principal.permissions


def can_activate_staff_account(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_ACTIVATE_PERMISSION in principal.permissions


def can_suspend_staff_account(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_SUSPEND_PERMISSION in principal.permissions


def can_deprovision_staff_account(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_DEPROVISION_PERMISSION in principal.permissions


def can_read_staff_account(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_READ_PERMISSION in principal.permissions


def can_record_staff_account_recovery(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_RECOVERY_RECORD_PERMISSION in principal.permissions


def can_revoke_staff_account_sessions(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_SESSION_REVOKE_PERMISSION in principal.permissions


def can_grant_staff_account_delegation(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_DELEGATION_GRANT_PERMISSION in principal.permissions


def can_revoke_staff_account_delegation(principal: StaffPrincipal) -> bool:
    return STAFF_ACCOUNT_DELEGATION_REVOKE_PERMISSION in principal.permissions
