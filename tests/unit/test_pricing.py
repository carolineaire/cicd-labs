"""Tests unitaires des règles de prix — POINT DE DÉPART (Atelier 1).

Complétez ce fichier : objectif >= 90 % de couverture sur minishop/pricing.py.
"""

from decimal import Decimal

import pytest

from minishop.pricing import line_total, money, quote, apply_student15

pytestmark = pytest.mark.unit


def test_money_arrondi_commercial():
    """0.125 s'arrondit à 0.13 (ROUND_HALF_UP), pas 0.12."""
    assert money("0.125") == Decimal("0.13")


def test_line_total_sans_remise():
    assert line_total(Decimal("12.50"), 2) == Decimal("25.00")


def test_quote_panier_vide():
    """Un panier vide coûte 0 € : pas de frais de livraison."""
    q = quote([])
    assert q.total == Decimal("0.00")
    assert q.shipping == Decimal("0.00")


# TODO Atelier 1 :
#  - remise volume à partir de 10 unités (et pas à 9 !)
#  - quantités invalides (0, 100, -1, "2", True) -> ValueError   (astuce : @pytest.mark.parametrize)
#  - coupons WELCOME10 / FIXED5 / FREESHIP (seuils inclus/exclus), coupon inconnu, casse
#  - livraison offerte à partir de 50 € APRÈS remise
#  - produit inconnu -> KeyError

# Test 1 : quantités invalides
@pytest.mark.unit
@pytest.mark.parametrize("qty", [0, -1, 100, "2", True])
def test_quantite_invalide(qty):
    with pytest.raises(ValueError):
        line_total(Decimal("10"), qty)

# Test 2 : calcul sans remise volume
@pytest.mark.unit
@pytest.mark.parametrize(
    "price, qty, expected",
    [
        ("10", 1, "10.00"),
        ("10", 2, "20.00"),
        ("10", 9, "90.00"),
    ],
)
def test_total_sans_remise(price, qty, expected):
    result = line_total(Decimal(price), qty)
    assert result == Decimal(expected)


# Partie TDD
@pytest.mark.unit
def test_student15_remise_normale():
    # Une ligne de 20 €, sans remise volume
    lignes = [(Decimal("20.00"), False)]

    resultat = apply_student15(lignes)

    assert resultat == Decimal("17.00")


@pytest.mark.unit
def test_student15_sans_minimum():
    # Une ligne de 10 €, sans remise volume
    lignes = [(Decimal("10.00"), False)]

    resultat = apply_student15(lignes)

    assert resultat == Decimal("8.50")


@pytest.mark.unit
def test_student15_non_cumulable():
    # 45 € déjà remisés + 20 € sans remise volume
    lignes = [
        (Decimal("45.00"), True),
        (Decimal("20.00"), False),
    ]

    resultat = apply_student15(lignes)

    assert resultat == Decimal("62.00")
