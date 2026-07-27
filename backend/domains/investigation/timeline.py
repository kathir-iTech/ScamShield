from typing import Any, Dict, List

from services.orchestrator import analyze_text

from core.constants import UNKNOWN_CATEGORY

from .models import InvestigationArtefact, TimelineEvent


def _analyse_artefacts(validated: List[Dict]) -> List[InvestigationArtefact]:
    results = []
    for v in validated:
        analysis = analyze_text(v["text"])
        results.append(InvestigationArtefact(
            index=v["index"],
            artefact_type=v["type"],
            text=v["text"],
            analysis=analysis,
        ))
    return results


def _build_timeline(artefacts: List[InvestigationArtefact]) -> List[Dict]:
    events: List[TimelineEvent] = []
    event_counter = 0

    for art in artefacts:
        analysis = art.analysis
        prediction = analysis.get("prediction", "safe")
        indicators = analysis.get("detected_indicators", [])
        rule_label = analysis.get("rule_label", "low")
        category = analysis.get("scam_category", UNKNOWN_CATEGORY)
        assessment_score = analysis.get("assessment_score", 0)

        event_counter += 1
        events.append(TimelineEvent(
            index=event_counter,
            artefact_index=art.index,
            event_type="message_received",
            description=f"{art.artefact_type.title()} message received for analysis",
            details=f"Artefact #{art.index + 1}",
        ))

        event_counter += 1
        events.append(TimelineEvent(
            index=event_counter,
            artefact_index=art.index,
            event_type="classification",
            description=f"Classified as '{prediction}' with score {assessment_score}/100",
            details=f"Category: {category}, Rule label: {rule_label}",
        ))

        if "OTP Request" in indicators:
            event_counter += 1
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="otp_requested",
                description="OTP or verification code requested",
                details="Sensitive credential targeted",
            ))

        if "Payment Request" in indicators:
            event_counter += 1
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="payment_requested",
                description="Payment or money transfer requested",
                details="Financial transaction demanded",
            ))

        if "Suspicious URL" in indicators or "Shortened URL" in indicators:
            event_counter += 1
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="link_shared",
                description="Suspicious link shared in message",
                details="Phishing or malicious URL detected",
            ))

        if "Account Threat" in indicators:
            event_counter += 1
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="threat_escalation",
                description="Account threat or suspension warning issued",
                details="Urgency/scare tactic detected",
            ))

        if "QR Code Request" in indicators:
            event_counter += 1
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="qr_requested",
                description="QR code scan requested",
                details="QR-based payment scam possible",
            ))

        if "KYC Update Request" in indicators:
            event_counter += 1
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="identity_requested",
                description="KYC or identity documents requested",
                details="Identity theft or credential harvesting",
            ))

        entities = analysis.get("entities", [])
        high_risk_entities = [e for e in entities if e.get("risk") == "HIGH"]
        if high_risk_entities:
            event_counter += 1
            types = set(e.get("type", "unknown") for e in high_risk_entities)
            events.append(TimelineEvent(
                index=event_counter,
                artefact_index=art.index,
                event_type="high_risk_entity",
                description=f"High-risk entities detected: {', '.join(types)}",
                details="Dangerous indicators present in message",
            ))

    return [
        {
            "index": e.index,
            "artefact": e.artefact_index,
            "event_type": e.event_type,
            "description": e.description,
            "details": e.details,
        }
        for e in events
    ]
