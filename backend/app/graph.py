from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from app import parsers, registry
from app.ingest import IngestedFile
from app.llm import ParseUsage
from app.merge import merge_menu_groups
from app.schemas import (
    BankingBlock,
    LegalBlock,
    LegalRegistry,
    MenuBlock,
    MenuGroup,
    SourceFile,
)
from app.validators import (
    holder_matches_legal_name,
    validate_bic,
    validate_iban,
    validate_siren,
    validate_siret,
)

DocumentType = Literal["legal", "banking", "menu"]


class OnboardingState(TypedDict, total=False):
    document_type: DocumentType
    files: list[IngestedFile]

    existing_legal: LegalBlock | None
    existing_banking: BankingBlock | None
    existing_menu: MenuBlock | None

    legal: LegalBlock | None
    banking: BankingBlock | None
    menu: MenuBlock | None

    parsed_menu_groups: list[MenuGroup]
    source_files: list[SourceFile]
    usages: list[ParseUsage]
    registry_result: dict | None


def _ingest_node(state: OnboardingState) -> OnboardingState:
    state.setdefault("usages", [])
    state.setdefault("parsed_menu_groups", [])
    return state


async def _parse_legal_node(state: OnboardingState) -> OnboardingState:
    if state.get("document_type") != "legal":
        return state
    blocks = [file.block for file in state.get("files", [])]
    output = await parsers.parse_legal(blocks)
    state["legal"] = output.block
    state["usages"].append(output.usage)
    return state


async def _parse_banking_node(state: OnboardingState) -> OnboardingState:
    if state.get("document_type") != "banking":
        return state
    blocks = [file.block for file in state.get("files", [])]
    output = await parsers.parse_banking(blocks)
    state["banking"] = output.block
    state["usages"].append(output.usage)
    return state


async def _parse_menu_node(state: OnboardingState) -> OnboardingState:
    if state.get("document_type") != "menu":
        return state
    parsed_groups: list[MenuGroup] = []
    for ingested in state.get("files", []):
        output = await parsers.parse_menu_file(ingested)
        state["usages"].append(output.usage)
        parsed_groups.extend(output.groups)
    state["parsed_menu_groups"] = parsed_groups
    return state


def _validate_node(state: OnboardingState) -> OnboardingState:
    legal = state.get("legal")
    if legal is not None and legal.status == "ready":
        _validate_legal(legal)

    banking = state.get("banking")
    if banking is not None and banking.status == "ready":
        _validate_banking(banking, legal or state.get("existing_legal"))
    return state


def _validate_legal(legal: LegalBlock) -> None:
    fields = legal.fields
    if fields.siren.value:
        fields.siren.valid = validate_siren(fields.siren.value)
    if fields.siret.value:
        fields.siret.valid = validate_siret(fields.siret.value)


def _validate_banking(banking: BankingBlock, legal: LegalBlock | None) -> None:
    fields = banking.fields
    if fields.iban.value:
        fields.iban.valid = validate_iban(fields.iban.value)
    if fields.bic.value:
        fields.bic.valid = validate_bic(fields.bic.value)
    legal_name = legal.fields.legal_name.value if legal else None
    banking.cross_doc_holder_match = holder_matches_legal_name(
        fields.account_holder.value, legal_name
    )


async def _enrich_registry_node(state: OnboardingState) -> OnboardingState:
    legal = state.get("legal")
    if legal is None or legal.status != "ready":
        return state
    siren = legal.fields.siren.value
    if not siren or not validate_siren(siren):
        legal.registry = LegalRegistry(status="skipped", name_match=None)
        return state

    result = await registry.verify_siren(siren, legal.fields.legal_name.value)
    state["registry_result"] = result.model_dump()
    if result.status == "match":
        legal.registry = LegalRegistry(status="match", name_match=result.name_match)
    elif result.status == "no_match":
        legal.registry = LegalRegistry(status="no_match", name_match=None)
    else:
        legal.registry = LegalRegistry(status="unavailable", name_match=None)
    return state


def _merge_menu_node(state: OnboardingState) -> OnboardingState:
    if state.get("document_type") != "menu":
        return state
    existing = state.get("existing_menu") or MenuBlock()
    parsed_groups = state.get("parsed_menu_groups", [])
    merged_groups = merge_menu_groups(existing.groups, parsed_groups)

    source_files = list(existing.source_files)
    known_ids = {source.id for source in source_files}
    for ingested in state.get("files", []):
        if ingested.file_id in known_ids:
            continue
        source_files.append(
            SourceFile(
                id=ingested.file_id,
                kind=ingested.kind,
                filename=ingested.filename,
                url=f"/api/onboarding/files/{ingested.file_id}",
            )
        )
        known_ids.add(ingested.file_id)

    has_usable = any(group.items for group in merged_groups)
    status = "ready" if has_usable else "couldnt_parse"
    state["menu"] = MenuBlock(status=status, groups=merged_groups, source_files=source_files)
    return state


def _assemble_node(state: OnboardingState) -> OnboardingState:
    return state


def _converse_node(state: OnboardingState) -> OnboardingState:
    # Stub for the future chat front-door. A real implementation routes to the same
    # parse/validate/merge nodes and renders assistant turns + UI directives, without
    # changing the core. The wizard never reaches this node.
    return state


def build_graph():
    graph = StateGraph(OnboardingState)
    graph.add_node("ingest", _ingest_node)
    graph.add_node("parse_legal", _parse_legal_node)
    graph.add_node("parse_banking", _parse_banking_node)
    graph.add_node("parse_menu", _parse_menu_node)
    graph.add_node("validate", _validate_node)
    graph.add_node("enrich_registry", _enrich_registry_node)
    graph.add_node("merge_menu", _merge_menu_node)
    graph.add_node("assemble", _assemble_node)
    graph.add_node("converse", _converse_node)

    graph.set_entry_point("ingest")
    graph.add_edge("ingest", "parse_legal")
    graph.add_edge("parse_legal", "parse_banking")
    graph.add_edge("parse_banking", "parse_menu")
    graph.add_edge("parse_menu", "validate")
    graph.add_edge("validate", "enrich_registry")
    graph.add_edge("enrich_registry", "merge_menu")
    graph.add_edge("merge_menu", "assemble")
    graph.add_edge("assemble", END)
    # `converse` is intentionally an orphan: it has no incoming wizard edge. A future
    # chat endpoint invokes it directly through the service, not through the wizard flow,
    # so it reuses the same parse/validate/merge nodes without changing the core.
    graph.add_edge("converse", END)

    return graph.compile()


_compiled = None


async def run_pipeline(state: OnboardingState) -> OnboardingState:
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return await _compiled.ainvoke(state)
