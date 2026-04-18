from pkg.presenter import DigestPresenter
from pkg.service import EnvelopeCompiler


def run_signal_smoke_d(query: str) -> str:
    coordinator = EnvelopeCompiler()
    presenter = DigestPresenter()
    digest = coordinator.compile_digest(query)
    return presenter.render(digest)
