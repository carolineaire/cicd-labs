# DIVERGENCE SPEC/CODE : ce fichier suppose les prix du catalogue déduits de la spécification
# (mug 12,50 €, hoodie 44,00 €, sticker 2,45 €). Le catalogue n'est pas fourni.

from decimal import Decimal

import pytest

from minishop.pricing import (
    coupon_discount,
    line_total,
    money,
    quote,
    shipping_cost,
)

pytestmark = [pytest.mark.generated, pytest.mark.unit]


def items(*pairs):
    """Construit la liste d'items attendue par quote() à partir de paires (produit, quantité)."""
    return [{"product_id": pid, "qty": qty} for pid, qty in pairs]


# ---------------------------------------------------------------------------
# Scénarios de la spécification
# ---------------------------------------------------------------------------


def test_panier_vide():
    """Un panier vide a un total de 0 et aucuns frais de livraison."""
    q = quote([])
    assert q.total == Decimal("0.00")
    assert q.shipping == Decimal("0.00")


def test_achat_simple_avec_frais_de_livraison():
    """Deux mugs sous le seuil de 50 € paient 4,90 € de livraison."""
    q = quote(items(("mug", 2)))
    assert q.subtotal == Decimal("25.00")
    assert q.shipping == Decimal("4.90")
    assert q.total == Decimal("29.90")


def test_livraison_offerte_a_partir_de_50_euros():
    """Un panier de 50 € ou plus bénéficie de la livraison offerte."""
    q = quote(items(("hoodie", 1), ("mug", 1)))
    assert q.shipping == Decimal("0.00")
    assert q.total == Decimal("56.50")


def test_remise_volume_des_10_unites():
    """Dix stickers déclenchent la remise volume de 5 % sur la ligne."""
    q = quote(items(("sticker", 10)))
    assert q.subtotal == Decimal("23.28")


def test_coupon_de_bienvenue():
    """WELCOME10 applique 10 % de remise quand le sous-total atteint 20 €."""
    q = quote(items(("mug", 2)), coupon="WELCOME10")
    assert q.discount == Decimal("2.50")
    assert q.total == Decimal("27.40")


def test_coupon_de_bienvenue_sous_le_seuil():
    """WELCOME10 n'accorde aucune remise si le sous-total est inférieur à 20 €."""
    q = quote(items(("mug", 1)), coupon="WELCOME10")
    assert q.discount == Decimal("0.00")


def test_coupon_de_livraison_offerte():
    """FREESHIP supprime les frais de livraison même sous le seuil."""
    q = quote(items(("sticker", 1)), coupon="FREESHIP")
    assert q.shipping == Decimal("0.00")
    assert q.total == Decimal("2.45")


def test_coupon_inconnu():
    """Un code coupon absent de la liste connue lève une erreur 'Coupon inconnu'."""
    with pytest.raises(ValueError, match="Coupon inconnu"):
        quote(items(("mug", 1)), coupon="NOEL2026")


def test_produit_inconnu():
    """Un produit absent du catalogue lève une erreur 'Produit inconnu'."""
    # DIVERGENCE SPEC/CODE : le code délègue à get_product() qui lève KeyError sans message
    # 'Produit inconnu' explicite ; la spec exige ce message partiel.
    with pytest.raises(Exception, match="Produit inconnu"):
        quote(items(("licorne", 1)))


def test_coupon_fixed5_au_dessus_du_seuil():
    """FIXED5 retire 5 € quand le sous-total atteint 30 €, la livraison restant facturée."""
    q = quote(items(("mug", 3)), coupon="FIXED5")
    assert q.subtotal == Decimal("37.50")
    assert q.discount == Decimal("5.00")
    assert q.shipping == Decimal("4.90")
    assert q.total == Decimal("37.40")


def test_remise_volume_avec_coupon_welcome10():
    """La remise volume et WELCOME10 se combinent : le coupon porte sur le sous-total déjà remisé."""
    q = quote(items(("sticker", 10)), coupon="WELCOME10")
    assert q.subtotal == Decimal("23.28")
    assert q.discount == Decimal("2.33")
    assert q.total == Decimal("25.85")


def test_quantite_zero_invalide():
    """Une quantité nulle est refusée avec l'erreur 'Quantité hors limites'."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        quote(items(("mug", 0)))


# ---------------------------------------------------------------------------
# Cas limites (non cités par la spécification)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("qty", [1, 99])
def test_limite_quantites_bornes_acceptees(qty):
    """Les quantités 1 et 99, bornes incluses, sont acceptées."""
    assert line_total(Decimal("1.00"), qty) >= Decimal("0")


@pytest.mark.parametrize("qty", [0, -1, 100])
def test_limite_quantites_hors_bornes_refusees(qty):
    """Les quantités 0, négative et 100 (hors bornes 1..99) sont refusées."""
    with pytest.raises(ValueError, match="Quantité hors limites"):
        line_total(Decimal("1.00"), qty)


@pytest.mark.parametrize("qty", [True, False, 2.0, "2"])
def test_limite_quantite_non_entiere_refusee(qty):
    """Une quantité non entière (bool, float, str) est refusée."""
    with pytest.raises(ValueError):
        line_total(Decimal("1.00"), qty)


def test_limite_remise_volume_9_unites_sans_remise():
    """Neuf unités du même produit n'ouvrent pas droit à la remise volume."""
    assert line_total(Decimal("12.50"), 9) == Decimal("112.50")


def test_limite_remise_volume_10_unites_avec_remise():
    """Dix unités ouvrent droit à la remise volume de 5 %."""
    assert line_total(Decimal("12.50"), 10) == Decimal("118.75")


def test_limite_remise_volume_arrondi_99_unites():
    """La remise volume sur 99 unités est arrondie au centime."""
    assert line_total(Decimal("2.45"), 99) == Decimal("230.42")


@pytest.mark.parametrize(
    "subtotal, expected",
    [
        (Decimal("19.99"), Decimal("0.00")),
        (Decimal("20.00"), Decimal("2.00")),
        (Decimal("20.01"), Decimal("2.00")),
    ],
)
def test_limite_welcome10_seuil_20_euros(subtotal, expected):
    """WELCOME10 s'applique à partir de 20 € inclus, pas en dessous."""
    assert coupon_discount(subtotal, "WELCOME10") == expected


def test_limite_welcome10_arrondi_au_centime():
    """La remise WELCOME10 de 23,25 € (2,325 €) est arrondie à 2,33 € (demi supérieur)."""
    assert coupon_discount(Decimal("23.25"), "WELCOME10") == Decimal("2.33")


@pytest.mark.parametrize(
    "subtotal, expected",
    [
        (Decimal("29.99"), Decimal("0.00")),
        (Decimal("30.00"), Decimal("5.00")),
    ],
)
def test_limite_fixed5_seuil_30_euros(subtotal, expected):
    """FIXED5 s'applique à partir de 30 € inclus, pas en dessous."""
    assert coupon_discount(subtotal, "FIXED5") == expected


@pytest.mark.parametrize(
    "amount, expected",
    [
        (Decimal("49.99"), Decimal("4.90")),
        (Decimal("50.00"), Decimal("0.00")),
        (Decimal("50.01"), Decimal("0.00")),
    ],
)
def test_limite_livraison_seuil_50_euros(amount, expected):
    """La livraison est offerte à partir de 50 € inclus après remise."""
    assert shipping_cost(amount, None, empty=False) == expected


def test_limite_freeship_ignore_le_seuil():
    """FREESHIP offre la livraison même pour un montant très faible."""
    assert shipping_cost(Decimal("1.00"), "FREESHIP", empty=False) == Decimal("0.00")


def test_limite_coupon_insensible_a_la_casse_et_aux_espaces():
    """Un code coupon en minuscules avec espaces est normalisé et appliqué."""
    q = quote(items(("mug", 2)), coupon="  welcome10 ")
    assert q.coupon == "WELCOME10"
    assert q.discount == Decimal("2.50")


def test_limite_coupon_vide_sans_remise():
    """Une chaîne de coupon vide n'applique aucune remise et ne lève pas d'erreur."""
    q = quote(items(("mug", 2)), coupon="")
    assert q.coupon is None
    assert q.discount == Decimal("0.00")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("0.125", Decimal("0.13")),
        (Decimal("2.675"), Decimal("2.68")),
        (Decimal("1.004"), Decimal("1.00")),
    ],
)
def test_limite_arrondi_commercial_demi_superieur(value, expected, monkeypatch):
    """L'arrondi au centime suit ROUND_HALF_UP : 0,125 devient 0,13."""
    monkeypatch.delenv("MINISHOP_BUG", raising=False)
    assert money(value) == expected


def test_limite_student15_ignore_les_lignes_en_remise_volume():
    """STUDENT15 ne s'applique qu'aux lignes sans remise volume : dix stickers donnent 0 € de remise."""
    q = quote(items(("sticker", 10)), coupon="STUDENT15")
    assert q.discount == Decimal("0.00")


def test_limite_student15_sur_ligne_eligible():
    """STUDENT15 applique 15 % sur les lignes éligibles, arrondi au centime."""
    q = quote(items(("mug", 1)), coupon="STUDENT15")
    assert q.discount == Decimal("1.88")
    assert q.total == Decimal("15.52")


def test_limite_panier_vide_avec_coupon_inconnu_sans_erreur():
    """Sans ligne, le coupon n'est pas évalué : aucune erreur et total nul."""
    q = quote([], coupon="NOEL2026")
    assert q.discount == Decimal("0.00")
    assert q.total == Decimal("0.00")


def test_limite_as_dict_expose_montants_en_texte():
    """as_dict() sérialise les montants sous forme de chaînes au format à deux décimales."""
    d = quote(items(("mug", 2))).as_dict()
    assert d["subtotal"] == "25.00"
    assert d["shipping"] == "4.90"
    assert d["total"] == "29.90"
    assert d["coupon"] is None
