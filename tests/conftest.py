"""Gemeinsame Fixtures: die Mini-Instanzen, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Handrechnungen (α = Größe einer größten unabhängigen Menge): Pfad P4: 2, Dreieck mit Pendel: 2, Stern mit drei Blättern: 3, Dreieck K3: 1, Fünfeck: 2, K4: 1, Petersen-Graph: 4, Gitter 3×3: 5."""

import functools
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mls_experiments as _ex  # noqa: E402
import mls_scenario as S  # noqa: E402


@pytest.fixture
def path4():
    """Pfad 0-1-2-3."""
    return S.path_graph(4).adj


@pytest.fixture
def paw():
    """Dreieck 0-1-2 mit Pendel 3 an Knoten 2."""
    return S.triangle_with_pendant().adj


@pytest.fixture
def star3():
    """Mitte 0 mit drei Blättern."""
    return S.star_graph(3).adj


@pytest.fixture
def triangle():
    return S.complete_graph(3).adj


@pytest.fixture
def k4():
    return S.complete_graph(4).adj


@pytest.fixture
def c5():
    return S.ring_graph(5).adj


@pytest.fixture
def petersen():
    return S.petersen_graph().adj


@pytest.fixture
def grid3():
    return S.grid_graph(9, 0, 0).adj


# Die Experimente sind reine Funktionen fester Instanzen und teuer: einmal je Testlauf, nicht je Test.
for _name in ("family_rows", "toronto_rows", "search_rows", "ablation_rows"):
    setattr(_ex, _name, functools.lru_cache(maxsize=None)(getattr(_ex, _name)))
