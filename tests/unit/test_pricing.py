"""Tests unitaires des règles de prix MiniShop."""

from decimal import Decimal
from types import SimpleNamespace

import pytest
import minishop.pricing as pricing

from minishop.pricing import line_total, money, quote

pytestmark = pytest.mark.unit


# ----------------------------------
# FIXTURE : catalogue simulé
# ----------------------------------

@pytest.fixture
def catalogue_simule(monkeypatch):
    produits = {
        "produit20": Decimal("20.00"),
        "produit10": Decimal("10.00"),
        "produit5": Decimal("5.00"),
    }

    def faux_get_product(product_id):
        return SimpleNamespace(
            id=product_id,
            price=produits[product_id]
        )

    monkeypatch.setattr(
        pricing, "get_product", faux_get_product
    )


# ----------------------------------
# TESTS EXISTANTS
# ----------------------------------

def test_money_arrondi_commercial():
    assert money("0.125") == Decimal("0.13")


def test_line_total_sans_remise():
    assert line_total(
        Decimal("12.50"), 2
    ) == Decimal("25.00")


def test_quote_panier_vide():
    q = quote([])

    assert q.total == Decimal("0.00")
    assert q.shipping == Decimal("0.00")


# ----------------------------------
# TESTS PARAMETRES
# ----------------------------------

@pytest.mark.parametrize(
    "qty", [0, -1, 100, "2", True]
)
def test_quantite_invalide(qty):
    with pytest.raises(ValueError):
        line_total(Decimal("10"), qty)


@pytest.mark.parametrize(
    "price, qty, expected",
    [
        ("10", 1, "10.00"),
        ("10", 2, "20.00"),
        ("10", 9, "90.00"),
    ],
)
def test_total_sans_remise(price, qty, expected):
    resultat = line_total(Decimal(price), qty)

    assert resultat == Decimal(expected)


@pytest.mark.parametrize(
    "qty, expected",
    [
        (9, "90.00"),
        (10, "95.00"),
        (11, "104.50"),
    ],
)
def test_remise_volume(qty, expected):
    resultat = line_total(Decimal("10"), qty)

    assert resultat == Decimal(expected)


# ----------------------------------
# TDD : COUPON STUDENT15
# ----------------------------------

# Test 1 : réduction normale de 15 %

def test_student15_remise_normale(catalogue_simule):
    panier = [
        {"product_id": "produit20", "qty": 1}
    ]

    resultat = quote(panier, coupon="STUDENT15")

    assert resultat.subtotal == Decimal("20.00")
    assert resultat.discount == Decimal("3.00")
    assert resultat.total == Decimal("21.90")


# Test 2 : coupon sans montant minimum

def test_student15_sans_minimum(catalogue_simule):
    panier = [
        {"product_id": "produit10", "qty": 1}
    ]

    resultat = quote(panier, coupon="STUDENT15")

    assert resultat.discount == Decimal("1.50")
    assert resultat.total == Decimal("13.40")


# Test 3 : non cumulable avec remise volume

def test_student15_non_cumulable(catalogue_simule):
    panier = [
        {"product_id": "produit5", "qty": 10},
        {"product_id": "produit20", "qty": 1},
    ]

    resultat = quote(panier, coupon="STUDENT15")

    assert resultat.subtotal == Decimal("67.50")
    assert resultat.discount == Decimal("3.00")
    assert resultat.total == Decimal("64.50")
