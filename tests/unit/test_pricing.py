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
    assert money("0.125") == Decimal("0.99")


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


# ----------------------------------
# TESTS DES COUPONS
# ----------------------------------

@pytest.mark.parametrize(
    "coupon, qty, expected_discount",
    [
        ("WELCOME10", 1, "0.00"),  # 10 € : seuil non atteint
        ("WELCOME10", 2, "2.00"),  # 20 € : réduction de 10 %
        ("FIXED5", 2, "0.00"),     # 20 € : seuil non atteint
        ("FIXED5", 3, "5.00"),     # 30 € : réduction de 5 €
        ("FREESHIP", 1, "0.00"),   # Livraison gratuite
    ]
)
def test_coupons(
    catalogue_simule, coupon, qty, expected_discount
):
    panier = [
        {"product_id": "produit10", "qty": qty}
    ]

    resultat = quote(panier, coupon=coupon)

    assert resultat.discount == Decimal(expected_discount)


# ----------------------------------
# TESTS DE LIVRAISON
# ----------------------------------

@pytest.mark.parametrize(
    "coupon, qty, expected_shipping",
    [
        (None, 5, "0.00"),         # 50 € : livraison gratuite
        ("WELCOME10", 5, "4.90"), # Après remise : 45 €
        ("WELCOME10", 6, "0.00"), # Après remise : 54 €
    ]
)
def test_livraison_apres_remise(
    catalogue_simule, coupon, qty, expected_shipping
):
    panier = [
        {"product_id": "produit10", "qty": qty}
    ]

    resultat = quote(panier, coupon=coupon)

    assert resultat.shipping == Decimal(expected_shipping)


# ----------------------------------
# COUPON INCONNU
# ----------------------------------

def test_coupon_inconnu(catalogue_simule):
    panier = [
        {"product_id": "produit10", "qty": 1}
    ]

    with pytest.raises(ValueError):
        quote(panier, coupon="FAUXCOUPON")


# ----------------------------------
# COUPON EN MINUSCULES
# ----------------------------------

def test_coupon_minuscule(catalogue_simule):
    panier = [
        {"product_id": "produit10", "qty": 2}
    ]

    resultat = quote(panier, coupon="welcome10")

    assert resultat.discount == Decimal("2.00")
    assert resultat.coupon == "WELCOME10"


def test_quote_as_dict(catalogue_simule):
    panier = [
        {"product_id": "produit5", "qty": 1}
    ]

    resultat = quote(panier)
    donnees = resultat.as_dict()

    assert donnees["subtotal"] == "5.00"
    assert donnees["shipping"] == "4.90"
    assert donnees["total"] == "9.90"
    assert donnees["lines"][0]["product_id"] == "produit5"
    assert donnees["lines"][0]["qty"] == 1
