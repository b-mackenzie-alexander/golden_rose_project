from golden_rose.auth.principal import StaffPrincipal

CREATE_DRAFT_EMPLOYER_PERMISSION = "employer:draft:create"


def can_create_draft_employer(principal: StaffPrincipal) -> bool:
    return CREATE_DRAFT_EMPLOYER_PERMISSION in principal.permissions
