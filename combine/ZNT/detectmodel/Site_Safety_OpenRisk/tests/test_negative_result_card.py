from types import SimpleNamespace
from app_server import AppState


def test_no_risk_event_is_visible_without_claiming_confirmed_safe():
    event = {'event_id':'EVT-negative','risks':[], 'data_mode':'offline',
             'pipeline':{'job_id':'JOB-negative'},'media':{'image_path':'input.png'}}
    state = SimpleNamespace(db=SimpleNamespace(list=lambda kind:[event]),media_url=lambda path:path)
    cards = AppState.frontend_events(state)
    assert len(cards) == 1
    assert cards[0]['noRiskDetected']
    assert cards[0]['confidence'] is None
    assert not cards[0]['autoConfirm'] and not cards[0]['machineVerified']
    assert not cards[0]['live'] and cards[0]['riskCount'] == 0
    assert cards[0]['detectJobId'] == 'JOB-negative'
