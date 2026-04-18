from pkg.models import ReviewEnvelope


class LayoutBase:
    def format_digest(self, envelope: ReviewEnvelope) -> str:
        return (
            f"owner:{envelope.owner_alias} | {envelope.review_step} -> "
            f"{envelope.alignment_note}"
        )
