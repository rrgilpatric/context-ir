import pkg


class MemberSignalCompiler:
    def compile_member_digest(self, query: str) -> str:
        member_note = query or "missing member note"
        owner_alias = self.resolve_owner_alias(member_note)
        owner_label = pkg.labels.build_member_label(owner_alias)
        pkg_alias = pkg
        pkg_alias.labels.build_member_label(owner_alias)
        return f"{owner_label} | keep member report aligned | {member_note}"

    def resolve_owner_alias(self, query: str) -> str:
        if "owner" in query or "member" in query:
            return "member-review"
        return "digest-review"
