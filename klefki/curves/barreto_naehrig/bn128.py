"""
ref: https://github.com/ethereum/research/blob/711bd9532b4534ef5ae6277bd7afe625195506d5/zksnark/bn128_field_elements.py
"""
import klefki.const as const
from klefki.types.algebra.fields import FiniteField
from klefki.types.algebra.fields import PolyExtField
from klefki.types.algebra.groups import EllipticCurveGroup
from klefki.types.algebra.groups import EllipicCyclicSubgroup
from klefki.curves.arith import short_weierstrass_form_curve_addition2


class BN128FP(FiniteField):
    P = const.BN128_P


class BN128FP2(PolyExtField):
    F = BN128FP
    E = const.BN128_FP2_E


class BN128FP12(PolyExtField):
    F = BN128FP
    E = const.BN128_FP12_E


class ECGBN128(EllipticCurveGroup):
    A = const.BN128_A

    N = const.BN128_N

    def op(self, g):
        if g == self.zero():
            return self
        if self == self.zero():
            return g
        field = self.id[0].type

        # a1,a3,a2,a4,a6 = 0, 0, 0, a, b
        x, y = short_weierstrass_form_curve_addition2(
            self.x, self.y,
            g.x, g.y,
            field.zero(),
            field.zero(),
            field.zero(),
            field(self.A),
            field(self.B),
            field
        )
        if x == y == field.zero():
            return self.zero()
        return self.__class__((x, y))

    def twist(self):
        x, y = self.x, self.y
        if self == self.zero():
            return self.zero()
        if isinstance(x, BN128FP12) and isinstance(y, BN128FP12):
            return self
        elif isinstance(x, BN128FP2) and isinstance(y, BN128FP2):
            return self.twist_FP2_to_FP12(x, y)
        elif isinstance(x, BN128FP) and isinstance(y, BN128FP):
            return self.twist_FP_to_FP12(x, y)
        else:
            raise Exception("cannot twist curve to fp12")

    @classmethod
    def twist_FP_to_FP12(cls, x, y):
        assert isinstance(x, BN128FP)
        assert isinstance(y, BN128FP)
        ret = cls(BN128FP12([x] + [BN128FP(0)] * 11), BN128FP12([y] + [BN128FP(0)] * 11))
        return ret

    @classmethod
    def twist_FP2_to_FP12(cls, x, y):
        # "Twist" a point in E(FQ2) into a point in E(FQ12)
        zero = BN128FP.zero()
        one = BN128FP.one()
        w = BN128FP12([zero, one] + [zero] * 10)
        assert isinstance(x, BN128FP2)
        assert isinstance(y, BN128FP2)
        nx = BN128FP12([x.id[0]] + [zero] * 5 + [x.id[1]] + [zero] * 5)
        ny = BN128FP12([y.id[0]] + [zero] * 5 + [y.id[1]] + [zero] * 5)
        ret = cls((nx / w **2, ny / w**3))
        assert ret.is_on_curve()
        return ret

    @staticmethod
    def linefunc(P1, P2, T):
        # https://github.com/ethereum/research/blob/9a7b6825b0dee7a59a03f8ca1d1ec3ae7fb6d598/zksnark/bn128_pairing.py
        assert P1 and P2 and T # No points-at-infinity allowed, sorry
        x1, y1 = P1.x, P1.y
        x2, y2 = P2.x, P2.y
        xt, yt = T.x, T.y
        if x1 != x2:
            m = (y2 - y1) / (x2 - x1)
            return m * (xt - x1) - (yt - y1)
        elif y1 == y2:
            m = (x1**2 * 3) / (y1 * 2)
            return m * (xt - x1) - (yt - y1)
        else:
            return xt - x1

    @classmethod
    def miller_loop(cls, Q, P):
        # ref: https://github.com/ethereum/research/blob/9a7b6825b0dee7a59a03f8ca1d1ec3ae7fb6d598/zksnark/bn128_pairing.py
        log_ate_loop_count = 63
        ate_loop_count = 29793968203157093288

        # if Q is None or P is None:
        #     return BN128FP12.one()
        if Q == cls.zero() or P == cls.zero():
            return cls.one()

        R = Q
        f = BN128FP12.one()
        for i in range(log_ate_loop_count, -1, -1):
            f = f * f * cls.linefunc(R, R, P)
            R = R @ 2
            if ate_loop_count & (2**i):
                f = f * cls.linefunc(R, Q, P)
                R = R + Q
#        assert R == Q @ ate_loop_count
        Q1 = cls(Q.x ** BN128FP.P, Q.y ** BN128FP.P)
#        assert Q1.is_on_curve()
        # assert is_on_curve(Q1, b12)
        nQ2 = cls(Q1.x ** BN128FP.P, (-Q1.y) ** BN128FP.P)
        # assert is_on_curve(nQ2, b12)
#        assert nQ2.is_on_curve()
        f = f * cls.linefunc(R, Q1, P)
        R = R + Q1
        f = f * cls.linefunc(R, nQ2, P)
        R = R + nQ2
        # R = add(R, nQ2) This line is in many specifications but it technically does nothing
        return f ** ((BN128FP.P ** 12 - 1) // cls.N)

    @classmethod
    def pairing(cls, Q, P):
        """
        e(P, Q + R) = e(P, Qj * e(P, R)
        e(P + Q, R) = e(P, R) * e(Q, R)
        """
        assert P.is_on_curve()
        assert Q.is_on_curve()
        return cls.miller_loop(Q.twist(), P.twist())

    @classmethod
    def e(cls, P, Q):
        return cls.pairing(P, Q)

    def is_on_curve(self):
        return self.y**2 - self.x**3 == self.B

    @property
    def B(self):
        if isinstance(self.x, BN128FP2):
            return BN128FP2([3, 0])
        elif isinstance(self.x, BN128FP12):
            return BN128FP12([3] + [0] * 11) / BN128FP12([0] * 6 + [1] + [0] * 5)
        return BN128FP(3)





ECGBN128.G1 = ECGBN128(
    BN128FP(const.BN128_G1x),
    BN128FP(const.BN128_G1y)
)

ECGBN128.G2 = ECGBN128(
    BN128FP2(const.BN128_G2x),
    BN128FP2(const.BN128_G2y)
)

ECGBN128.G = ECGBN128.G1
