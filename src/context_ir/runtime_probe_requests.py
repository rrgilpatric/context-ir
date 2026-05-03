"""Planned runtime probe requests for already-attachable unsupported boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import context_ir.runtime_acquisition as runtime_acquisition
from context_ir.semantic_types import (
    CallSiteFact,
    MetaclassKeywordFact,
    SemanticProgram,
    SemanticSubjectKind,
    SourceSite,
    UnresolvedReasonCode,
    UnsupportedConstruct,
)

_SourceSiteIdentity = tuple[str, int, int, int, int]


class RuntimeProbeRequestStatus(Enum):
    """Execution status for a runtime probe acquisition request."""

    PLANNED_NOT_EXECUTED = "planned_not_executed"


class RuntimeProbeFamily(Enum):
    """Runtime-boundary families currently eligible for probe planning."""

    DYNAMIC_IMPORT = "dynamic_import"
    REFLECTIVE_BUILTIN = "reflective_builtin"
    RUNTIME_MUTATION = "runtime_mutation"
    EXEC_OR_EVAL = "exec_or_eval"
    METACLASS_BEHAVIOR = "metaclass_behavior"


@dataclass(frozen=True)
class RuntimeProbeRequest:
    """Internal acquisition request for a planned, not-yet-executed runtime probe."""

    subject_kind: SemanticSubjectKind
    subject_id: str
    source_site: SourceSite
    reason_code: UnresolvedReasonCode
    boundary_text: str
    family_label: RuntimeProbeFamily
    form_label: str
    replay_target_seed: str
    replay_selector_seed: str
    status: RuntimeProbeRequestStatus = RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED

    def __post_init__(self) -> None:
        """Reject incomplete or non-planned runtime probe requests."""
        if self.subject_kind is not SemanticSubjectKind.UNSUPPORTED_FINDING:
            raise ValueError("runtime probe requests target unsupported findings")
        if not self.subject_id.strip():
            raise ValueError("subject_id must be non-empty")
        if not self.boundary_text.strip():
            raise ValueError("boundary_text must be non-empty")
        if not self.form_label.strip():
            raise ValueError("form_label must be non-empty")
        if not self.replay_target_seed.strip():
            raise ValueError("replay_target_seed must be non-empty")
        if not self.replay_selector_seed.strip():
            raise ValueError("replay_selector_seed must be non-empty")
        if self.status is not RuntimeProbeRequestStatus.PLANNED_NOT_EXECUTED:
            raise ValueError("runtime probe requests must be planned-only")


def derive_runtime_probe_requests(
    program: SemanticProgram,
) -> tuple[RuntimeProbeRequest, ...]:
    """Derive planned probe requests for currently attachable runtime boundaries."""
    requests_by_site: dict[_SourceSiteIdentity, RuntimeProbeRequest] = {}
    call_sites_by_id = {
        call_site.call_site_id: call_site for call_site in program.syntax.call_sites
    }
    metaclass_keywords_by_id = {
        metaclass_keyword.metaclass_keyword_id: metaclass_keyword
        for metaclass_keyword in program.syntax.metaclass_keywords
    }

    for construct in runtime_acquisition._eligible_dynamic_import_constructs(
        program
    ).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.DYNAMIC_IMPORT,
            ),
        )

    for construct in runtime_acquisition._eligible_hasattr_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            ),
        )

    for (
        construct,
        _argument_count,
    ) in runtime_acquisition._eligible_getattr_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            ),
        )

    for (
        construct,
        _argument_count,
    ) in runtime_acquisition._eligible_vars_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            ),
        )

    for construct in runtime_acquisition._eligible_dir_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.REFLECTIVE_BUILTIN,
            ),
        )

    for construct in runtime_acquisition._eligible_globals_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
            ),
        )

    for construct in runtime_acquisition._eligible_locals_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
            ),
        )

    for construct in runtime_acquisition._eligible_setattr_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
            ),
        )

    for construct in runtime_acquisition._eligible_delattr_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.RUNTIME_MUTATION,
            ),
        )

    for construct in runtime_acquisition._eligible_eval_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.EXEC_OR_EVAL,
            ),
        )

    for construct in runtime_acquisition._eligible_exec_constructs(program).values():
        _add_request(
            requests_by_site,
            _request_from_call_construct(
                program=program,
                construct=construct,
                call_site=_required_call_site(construct, call_sites_by_id),
                family_label=RuntimeProbeFamily.EXEC_OR_EVAL,
            ),
        )

    for construct in runtime_acquisition._eligible_metaclass_behavior_constructs(
        program
    ).values():
        _add_request(
            requests_by_site,
            _request_from_metaclass_construct(
                program=program,
                construct=construct,
                metaclass_keyword=_required_metaclass_keyword(
                    construct,
                    metaclass_keywords_by_id,
                ),
            ),
        )

    return tuple(sorted(requests_by_site.values(), key=_request_sort_key))


def _add_request(
    requests_by_site: dict[_SourceSiteIdentity, RuntimeProbeRequest],
    request: RuntimeProbeRequest,
) -> None:
    """Insert one request while enforcing one planned request per source site."""
    site_identity = runtime_acquisition._source_site_identity(request.source_site)
    if site_identity in requests_by_site:
        raise ValueError("multiple runtime probe requests share the same source site")
    requests_by_site[site_identity] = request


def _request_from_call_construct(
    *,
    program: SemanticProgram,
    construct: UnsupportedConstruct,
    call_site: CallSiteFact,
    family_label: RuntimeProbeFamily,
) -> RuntimeProbeRequest:
    """Build a planned probe request for one attachable call boundary."""
    target_seed = _target_seed_for_scope(
        program=program,
        scope_id=construct.enclosing_scope_id,
        source_site=construct.site,
    )
    form_label = _call_form_label(family_label, call_site)
    return RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        source_site=construct.site,
        reason_code=construct.reason_code,
        boundary_text=construct.construct_text,
        family_label=family_label,
        form_label=form_label,
        replay_target_seed=target_seed,
        replay_selector_seed=(
            f"call:{target_seed}:{form_label}@{_source_site_fragment(construct.site)}"
        ),
    )


def _request_from_metaclass_construct(
    *,
    program: SemanticProgram,
    construct: UnsupportedConstruct,
    metaclass_keyword: MetaclassKeywordFact,
) -> RuntimeProbeRequest:
    """Build a planned probe request for one preserved metaclass keyword boundary."""
    target_seed = _target_seed_for_scope(
        program=program,
        scope_id=metaclass_keyword.owner_definition_id,
        source_site=construct.site,
    )
    form_label = f"{RuntimeProbeFamily.METACLASS_BEHAVIOR.value}:keyword"
    return RuntimeProbeRequest(
        subject_kind=SemanticSubjectKind.UNSUPPORTED_FINDING,
        subject_id=construct.construct_id,
        source_site=construct.site,
        reason_code=construct.reason_code,
        boundary_text=construct.construct_text,
        family_label=RuntimeProbeFamily.METACLASS_BEHAVIOR,
        form_label=form_label,
        replay_target_seed=target_seed,
        replay_selector_seed=(
            f"class:{target_seed}:metaclass@{_source_site_fragment(construct.site)}"
        ),
    )


def _required_call_site(
    construct: UnsupportedConstruct,
    call_sites_by_id: dict[str, CallSiteFact],
) -> CallSiteFact:
    """Return the originating call site for an eligible unsupported construct."""
    if not construct.construct_id.startswith("unsupported:"):
        raise ValueError("eligible call construct must use unsupported: identifier")
    call_site_id = construct.construct_id.removeprefix("unsupported:")
    call_site = call_sites_by_id.get(call_site_id)
    if call_site is None:
        raise ValueError("eligible call construct is missing its source call site")
    return call_site


def _required_metaclass_keyword(
    construct: UnsupportedConstruct,
    metaclass_keywords_by_id: dict[str, MetaclassKeywordFact],
) -> MetaclassKeywordFact:
    """Return the preserved metaclass keyword for an eligible construct."""
    if not construct.construct_id.startswith("unsupported:"):
        raise ValueError(
            "eligible metaclass construct must use unsupported: identifier"
        )
    metaclass_keyword_id = construct.construct_id.removeprefix("unsupported:")
    metaclass_keyword = metaclass_keywords_by_id.get(metaclass_keyword_id)
    if metaclass_keyword is None:
        raise ValueError(
            "eligible metaclass construct is missing its source keyword site"
        )
    return metaclass_keyword


def _target_seed_for_scope(
    *,
    program: SemanticProgram,
    scope_id: str | None,
    source_site: SourceSite,
) -> str:
    """Return a deterministic replay target seed from semantic scope context."""
    if scope_id is not None:
        symbol = program.resolved_symbols.get(scope_id)
        if symbol is not None:
            return symbol.qualified_name
        if scope_id.strip():
            return scope_id
    return f"source:{source_site.file_path}:{source_site.span.start_line}"


def _call_form_label(
    family_label: RuntimeProbeFamily,
    call_site: CallSiteFact,
) -> str:
    """Return the family-local call form label for acquisition planning."""
    return f"{family_label.value}:{call_site.callee_text}/{call_site.argument_count}"


def _source_site_fragment(site: SourceSite) -> str:
    """Return a compact source-site fragment for replay selector seeds."""
    span = site.span
    return (
        f"{site.file_path}:{span.start_line}:{span.start_column}:"
        f"{span.end_line}:{span.end_column}"
    )


def _request_sort_key(
    request: RuntimeProbeRequest,
) -> tuple[str, int, int, int, int, str, str]:
    """Return the deterministic ordering key for planned runtime probe requests."""
    site_identity = runtime_acquisition._source_site_identity(request.source_site)
    return (
        site_identity[0],
        site_identity[1],
        site_identity[2],
        site_identity[3],
        site_identity[4],
        request.family_label.value,
        request.subject_id,
    )


__all__ = [
    "RuntimeProbeFamily",
    "RuntimeProbeRequest",
    "RuntimeProbeRequestStatus",
    "derive_runtime_probe_requests",
]
