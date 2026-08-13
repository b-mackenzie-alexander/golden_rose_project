from golden_rose.auth.principal import StaffPrincipal

CREATE_DRAFT_EMPLOYER_PERMISSION = "employer:draft:create"
EMPLOYER_DRAFT_REVISE_PERMISSION = "employer:draft:revise"
EMPLOYER_READ_PERMISSION = "employer:read"
EMPLOYER_CONTACT_DRAFT_CREATE_PERMISSION = "employer_contact:draft:create"
EMPLOYER_CONTACT_READ_PERMISSION = "employer_contact:read"


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
