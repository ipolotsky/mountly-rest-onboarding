from app.database import SessionLocal
from app.schemas import LegalBlock
from app.service import OnboardingService


def test_admin_onboardings_surface_restaurant_name(fresh_database):
    with SessionLocal() as session:
        service = OnboardingService(session)
        onboarding_id = service.create("fr", "desktop")
        block = LegalBlock()
        block.fields.legal_name.value = "Chez Tester"
        block.fields.legal_name.status = "present"
        service.save_legal(onboarding_id, block)

    with SessionLocal() as session:
        rows = OnboardingService(session).admin_onboardings()

    row = next(item for item in rows if item.id == onboarding_id)
    assert row.restaurant_name == "Chez Tester"


def test_admin_onboardings_are_newest_first(fresh_database):
    with SessionLocal() as session:
        service = OnboardingService(session)
        service.create("fr", "desktop")
        service.create("fr", "mobile")
        service.create("fr", "desktop")

    with SessionLocal() as session:
        rows = OnboardingService(session).admin_onboardings()

    created = [row.created_at for row in rows]
    assert len(rows) == 3
    assert created == sorted(created, reverse=True)


def test_admin_feedback_surfaces_csat_answers_and_link(fresh_database):
    with SessionLocal() as session:
        service = OnboardingService(session)
        onboarding_id = service.create("fr", "mobile")
        service.feedback(onboarding_id, 5, {"helped": "Le pré-remplissage", "improve": "Rien"})

    with SessionLocal() as session:
        feedback = OnboardingService(session).admin_feedback()

    assert len(feedback) == 1
    row = feedback[0]
    assert row.id == onboarding_id  # the link target for the result page
    assert row.csat == 5
    assert row.helped == "Le pré-remplissage"
    assert row.improve == "Rien"
    assert row.device == "mobile"
    assert row.submitted_at


def test_admin_feedback_blank_answers_become_none(fresh_database):
    with SessionLocal() as session:
        service = OnboardingService(session)
        onboarding_id = service.create("fr", "desktop")
        service.feedback(onboarding_id, 3, {"helped": "  ", "improve": ""})

    with SessionLocal() as session:
        feedback = OnboardingService(session).admin_feedback()

    assert feedback[0].csat == 3
    assert feedback[0].helped is None
    assert feedback[0].improve is None


def test_admin_feedback_is_empty_without_submissions(fresh_database):
    with SessionLocal() as session:
        service = OnboardingService(session)
        service.create("fr", "desktop")
        assert service.admin_feedback() == []


def test_admin_feedback_keeps_only_the_latest_per_onboarding(fresh_database):
    with SessionLocal() as session:
        service = OnboardingService(session)
        onboarding_id = service.create("fr", "desktop")
        service.feedback(onboarding_id, 2, {"helped": "first", "improve": ""})
        service.feedback(onboarding_id, 5, {"helped": "second", "improve": "nothing"})

    with SessionLocal() as session:
        feedback = OnboardingService(session).admin_feedback()

    assert len(feedback) == 1
    assert feedback[0].csat == 5
    assert feedback[0].helped == "second"
