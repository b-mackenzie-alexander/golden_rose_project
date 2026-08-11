from golden_rose.auth.principal import StaffPrincipal

CREATE_DRAFT_EMPLOYER_PERMISSION = "employer:draft:create"
EMPLOYER_DRAFT_REVISE_PERMISSION = "employer:draft:revise"
EMPLOYER_READ_PERMISSION = "employer:read"


def can_create_draft_employer(principal: StaffPrincipal) -> bool:
    return CREATE_DRAFT_EMPLOYER_PERMISSION in principal.permissions


def can_revise_draft_employer(principal: StaffPrincipal) -> bool:
    return EMPLOYER_DRAFT_REVISE_PERMISSION in principal.permissions


def can_read_employer(principal: StaffPrincipal) -> bool:
    return EMPLOYER_READ_PERMISSION in principal.permissions
