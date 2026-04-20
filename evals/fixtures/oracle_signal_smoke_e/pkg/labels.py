def build_member_label(owner_alias: str) -> str:
    if owner_alias == "member-review":
        return "member owner: member review"
    return "member owner: digest review"
