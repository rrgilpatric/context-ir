from dataclasses import dataclass


@dataclass
class ReviewEnvelope:
    owner_alias: str
    review_step: str
    alignment_note: str
