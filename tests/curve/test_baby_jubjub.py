"""
Test case from:
https://eips.ethereum.org/EIPS/eip-2494
"""


import pytest
from zkp_playground.curves.baby_jubjub import FiniteFieldBabyJubjub as F, EllipticCurveBabyJubjub as G


def test_addition():
    x1 = F(17777552123799933955779906779655732241715742912184938656739573121738514868268)
    y1 = F(2626589144620713026669568689430873010625803728049924121243784502389097019475)
    x2 = F(16540640123574156134436876038791482806971768689494387082833631921987005038935)
    y2 = F(20819045374670962167435360035096875258406992893633759881276124905556507972311)
    x3 = F(7916061937171219682591368294088513039687205273691143098332585753343424131937)
    y3 = F(14035240266687799601661095864649209771790948434046947201833777492504781204499)
    g1 = G((x1, y1))
    g2 = G((x2, y2))
    add_sum = (g1 + g2)
    assert add_sum == G((x3, y3))


def test_double():
    x1 = 17777552123799933955779906779655732241715742912184938656739573121738514868268
    y1 = 2626589144620713026669568689430873010625803728049924121243784502389097019475

    x2 = 17777552123799933955779906779655732241715742912184938656739573121738514868268
    y2 = 2626589144620713026669568689430873010625803728049924121243784502389097019475

    x3 = 6890855772600357754907169075114257697580319025794532037257385534741338397365
    y3 = 4338620300185947561074059802482547481416142213883829469920100239455078257889

    g1 = G((F(x1), F(y1)))
    g2 = G((F(x1), F(y2)))
    assert g1 + g2 == G((F(x3), F(y3)))


def test_doubling_the_identity():
    x1 = 0
    y1 = 1
    x2 = 0
    y2 = 1
    x3 = 0
    y3 = 1

    g1 = G((F(x1), F(y1)))
    g2 = G((F(x1), F(y2)))
    assert g1 + g2 == G((F(x3), F(y3)))


def test_curve_membership():
    assert G((F(0), F(1)))
#    assert not G((F(1), F(0)))


def test_base_point_choice():
    Bx = 5299619240641551281634865583518297030282874472190772894086521144482721001553
    By = 16950150798460657717958625567821834550301663161624707787222815936182638968203
    Gx = 995203441582195749578291179787384436505546430278305826713579947235728471134
    Gy = 5472060717959818805561601436314318772137091100104008585924551046643952123905
    assert G.G == G((F(Gx), F(Gy)))
    assert G.G @ 8 == G((F(Bx), F(By)))


def test_base_point_order():
    Bx = 5299619240641551281634865583518297030282874472190772894086521144482721001553
    By = 16950150798460657717958625567821834550301663161624707787222815936182638968203
    l = 2736030358979909402780800718157159386076813972158567259200215660948447373041
    assert G(F(Bx), F(By)) @ l == G(F(0), F(1))
