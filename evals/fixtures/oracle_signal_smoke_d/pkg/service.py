from pkg.base import LayoutBase
from pkg.models import ReviewEnvelope


class EnvelopeCompiler(LayoutBase):
    def compile_digest(self, query: str) -> str:
        envelope = ReviewEnvelope(
            owner_alias="method-review",
            review_step=query or "missing digest",
            alignment_note="keep presenter aligned",
        )
        digest = super().format_digest(envelope)
        note_registry.record_missing_digest(digest)
        return digest
