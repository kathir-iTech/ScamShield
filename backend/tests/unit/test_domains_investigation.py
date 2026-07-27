import pytest

from domains.investigation.models import CampaignIndicators, MergedEntity, TimelineEvent, InvestigationArtefact


class TestCampaignIndicators:
    def test_creation(self):
        indicators = CampaignIndicators()
        assert indicators.shared_phones == []
        assert indicators.shared_domains == []
        assert indicators.shared_upi == []
        assert indicators.shared_emails == []
        assert indicators.repeated_wording is False
        assert indicators.same_scam_family is False

    def test_with_phones(self):
        indicators = CampaignIndicators()
        indicators.shared_phones.append("+911234567890")
        assert "+911234567890" in indicators.shared_phones


class TestMergedEntity:
    def test_creation(self):
        entity = MergedEntity(
            value="test@example.com",
            entity_type="EMAIL",
            occurrences=1,
            first_seen=0,
            sources=[0],
            max_risk="LOW",
        )
        assert entity.value == "test@example.com"
        assert entity.entity_type == "EMAIL"
        assert entity.occurrences == 1

    def test_increment_occurrences(self):
        entity = MergedEntity(
            value="test@example.com",
            entity_type="EMAIL",
            occurrences=1,
            first_seen=0,
            sources=[0],
            max_risk="LOW",
        )
        entity.occurrences += 1
        assert entity.occurrences == 2


class TestTimelineEvent:
    def test_creation(self):
        event = TimelineEvent(
            index=0,
            artefact_index=0,
            event_type="analysis_start",
            description="Test",
            details="Details",
        )
        assert event.event_type == "analysis_start"
        assert event.index == 0


class TestInvestigationArtefact:
    def test_creation(self):
        artefact = InvestigationArtefact(
            index=0,
            artefact_type="sms",
            text="test message",
            analysis={"prediction": "safe"},
        )
        assert artefact.text == "test message"
        assert artefact.analysis["prediction"] == "safe"
