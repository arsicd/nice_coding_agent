from typing import Any

import pytest

from app.controller import AppController
from app.presenter import AppPresenter
from app.state import AppState
from tests.fakes.fake_router import FakeRouter


@pytest.fixture
def fake_router() -> FakeRouter:
    return FakeRouter()


@pytest.fixture
def app_state() -> AppState:
    return AppState()


@pytest.fixture
def app_controller(app_state: AppState, fake_router: FakeRouter) -> AppController:
    return AppController(app_state, fake_router)


@pytest.fixture
def app_presenter(app_state: AppState, app_controller: AppController) -> AppPresenter:
    return AppPresenter(app_state, app_controller)


@pytest.fixture
def captured_events() -> list[tuple[str, Any]]:
    """Shared list for recording (event_name, payload) tuples from the event bus."""
    return []
