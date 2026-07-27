from typing import Any, Dict, List

from core.constants import UNKNOWN_CATEGORY

from .models import InvestigationArtefact
from .entities import _detect_repeated_indicators


def _build_relationship_graph(
    artefacts: List[InvestigationArtefact],
    merged: Dict[str, List[Dict]],
    campaign: Dict,
) -> Dict:
    nodes = []
    edges = []
    used_ids = set()

    for art in artefacts:
        nid = f"artefact_{art.index}"
        if nid not in used_ids:
            used_ids.add(nid)
            category = art.analysis.get("scam_category", UNKNOWN_CATEGORY)
            family = art.analysis.get("reasoning_family", "")
            prediction = art.analysis.get("prediction", "safe")
            nodes.append({
                "id": nid,
                "type": "artefact",
                "label": f"Artefact #{art.index + 1} ({art.artefact_type})",
                "subtype": art.artefact_type,
                "detail": f"{category} | {family} | {prediction}",
            })

    for etype, entity_list in merged.items():
        for ent in entity_list[:5]:
            nid = f"entity_{etype}_{ent['normalised'][:30]}"
            if nid not in used_ids:
                used_ids.add(nid)
                nodes.append({
                    "id": nid,
                    "type": "entity",
                    "label": f"{etype}: {ent['value'][:40]}",
                    "subtype": etype,
                    "detail": f"Occurrences: {ent['occurrences']}, Risk: {ent['max_risk']}",
                })
            for src_idx in ent["sources"]:
                src_id = f"artefact_{src_idx}"
                edge_key = f"{src_id}->{nid}"
                if edge_key not in {e["source"] + "->" + e["target"] for e in edges}:
                    edges.append({
                        "source": src_id,
                        "target": nid,
                        "relationship": "mentions",
                        "weight": 0.6,
                        "detail": f"Mentions {etype}: {ent['value'][:30]}",
                    })

    if campaign.get("campaign_detected"):
        for art in artefacts:
            nid = f"artefact_{art.index}"
            edges.append({
                "source": nid,
                "target": "campaign_root",
                "relationship": "belongs_to_campaign",
                "weight": campaign.get("confidence", 0.5),
                "detail": "Part of coordinated campaign",
            })
        if "campaign_root" not in used_ids:
            used_ids.add("campaign_root")
            nodes.append({
                "id": "campaign_root",
                "type": "campaign",
                "label": "Campaign",
                "subtype": "campaign",
                "detail": f"Confidence: {campaign.get('confidence', 0):.1%}",
            })

    repeated = _detect_repeated_indicators(artefacts)
    for ind, count in list(repeated.items())[:5]:
        nid = f"indicator_{ind[:30]}"
        if nid not in used_ids:
            used_ids.add(nid)
            nodes.append({
                "id": nid,
                "type": "indicator",
                "label": f"Indicator: {ind}",
                "subtype": "repeated",
                "detail": f"Appeared {count} times across artefacts",
            })

    return {"nodes": nodes[:30], "edges": edges[:40]}
