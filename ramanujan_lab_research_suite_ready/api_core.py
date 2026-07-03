"""Minimal reusable q-series core for the Ramanujan Laboratory REST API."""
from __future__ import annotations

import ast
import math
import re
from fractions import Fraction


class QSeries:
    def __init__(self, coeffs, limit):
        self.limit = int(limit)
        self.coeffs = [self._exact(x) for x in list(coeffs)[: self.limit + 1]]
        self.coeffs += [Fraction(0)] * (self.limit + 1 - len(self.coeffs))

    @staticmethod
    def _exact(x):
        if isinstance(x, Fraction):
            return x
        if isinstance(x, float):
            return Fraction(str(x))
        return Fraction(x)

    @classmethod
    def one(cls, limit):
        return cls([1], limit)

    def _coerce(self, other):
        return other if isinstance(other, QSeries) else QSeries([other], self.limit)

    def __neg__(self):
        return QSeries([-x for x in self.coeffs], self.limit)

    def __add__(self, other):
        other = self._coerce(other)
        return QSeries([a+b for a,b in zip(self.coeffs, other.coeffs)], self.limit)

    __radd__ = __add__

    def __sub__(self, other):
        return self + (-self._coerce(other))

    def __rsub__(self, other):
        return self._coerce(other) - self

    def __mul__(self, other):
        if not isinstance(other, QSeries):
            return QSeries([self._exact(other)*x for x in self.coeffs], self.limit)
        out = [Fraction(0)]*(self.limit+1)
        left = [(i,x) for i,x in enumerate(self.coeffs) if x]
        right = [(j,x) for j,x in enumerate(other.coeffs) if x]
        for i,a in left:
            for j,b in right:
                if i+j > self.limit:
                    break
                out[i+j] += a*b
        return QSeries(out, self.limit)

    __rmul__ = __mul__

    def inv(self):
        a0 = self.coeffs[0]
        if a0 == 0:
            raise ZeroDivisionError("series has zero constant term")
        out = [Fraction(0)]*(self.limit+1)
        out[0] = 1/a0
        for n in range(1, self.limit+1):
            out[n] = -sum(self.coeffs[k]*out[n-k] for k in range(1,n+1))/a0
        return QSeries(out, self.limit)

    def __truediv__(self, other):
        return self * (other.inv() if isinstance(other, QSeries) else 1/Fraction(other))

    def __rtruediv__(self, other):
        return self.inv()*other

    def __pow__(self, power):
        if not isinstance(power, int):
            raise TypeError("integer powers only")
        if power < 0:
            return self.inv() ** (-power)
        result = QSeries.one(self.limit)
        base = self
        while power:
            if power & 1:
                result = result*base
            power >>= 1
            if power:
                base = base*base
        return result


def generate_base_pochhammer(m, limit):
    m = int(m)
    out = [0]*(limit+1)
    out[0] = 1
    k = 1
    while True:
        a = m*k*(3*k-1)//2
        b = m*k*(3*k+1)//2
        sign = -1 if k % 2 else 1
        if a <= limit: out[a] = sign
        if b <= limit: out[b] = sign
        if a > limit and b > limit: break
        k += 1
    return out


def gen_phi(k, limit):
    out = [0]*(limit+1)
    n = 0
    while k*n*n <= limit:
        out[k*n*n] += 1 if n == 0 else 2
        n += 1
    return QSeries(out, limit)


def gen_psi(k, limit):
    out = [0]*(limit+1)
    n = 0
    while k*n*(n+1)//2 <= limit:
        out[k*n*(n+1)//2] += 1
        n += 1
    return QSeries(out, limit)


def latex_to_python(source):
    s = source.replace("$", "").replace("\n", "").replace("\r", "")
    s = re.sub(r"\\(?:varphi|phi)\s*\(\s*q\^?\{?([0-9]*)\}?\s*\)", lambda m: f"phi({m.group(1) or '1'})", s)
    s = re.sub(r"\\psi\s*\(\s*q\^?\{?([0-9]*)\}?\s*\)", lambda m: f"psi({m.group(1) or '1'})", s)
    while r"\frac" in s:
        start = s.find(r"\frac")
        def group(pos):
            while pos < len(s) and s[pos].isspace(): pos += 1
            if pos >= len(s) or s[pos] != "{":
                raise SyntaxError("fractions require braces")
            depth, i = 1, pos+1
            while i < len(s) and depth:
                depth += (s[i] == "{") - (s[i] == "}")
                i += 1
            return s[pos+1:i-1], i
        num, after_num = group(start+5)
        den, after_den = group(after_num)
        s = s[:start]+f"(({num})/({den}))"+s[after_den:]
    s = re.sub(r"f_\{([^}]+)\}", r"f(\1)", s)
    s = re.sub(r"f_(\d+)", r"f(\1)", s)
    s = s.replace("^", "**").replace("{", "(").replace("}", ")")
    s = s.replace(r"\cdot", "*").replace(r"\times", "*").replace(r"\left", "").replace(r"\right", "")
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"\)(?=[A-Za-z0-9(])", ")*", s)
    s = re.sub(r"(?<=\d)(?=[A-Za-z(])", "*", s)
    return s


ALLOWED = {"f", "q", "phi", "psi"}


def restricted_eval(expression, env):
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Attribute, ast.Subscript, ast.Lambda, ast.Dict, ast.ListComp, ast.Import, ast.ImportFrom)):
            raise ValueError("unsupported syntax")
        if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
            raise ValueError("unsupported function call")
        if isinstance(node, ast.Name) and node.id not in ALLOWED:
            raise ValueError(f"unknown symbol {node.id}")
    return eval(compile(tree, "<formula>", "eval"), {"__builtins__": {}}, env)


def expand(formula, limit):
    limit = int(limit)
    q = QSeries([0,1], limit)
    def f(n):
        n = int(n)
        if n <= 0:
            raise ValueError("f subscript must be positive")
        return QSeries(generate_base_pochhammer(n, limit), limit)
    env = {"f": f, "q": q, "phi": lambda k: gen_phi(int(k), limit), "psi": lambda k: gen_psi(int(k), limit)}
    result = restricted_eval(latex_to_python(formula), env)
    if not isinstance(result, QSeries):
        result = QSeries([result], limit)
    return result.coeffs


def serialize_coefficients(coeffs):
    return [int(x) if x.denominator == 1 else {"numerator": x.numerator, "denominator": x.denominator} for x in coeffs]


def dissect(formula, p, limit):
    coeffs = expand(formula, limit)
    return [serialize_coefficients(coeffs[r::p]) for r in range(p)]


def check_congruence(formula, step, residue, modulus, limit):
    coeffs = expand(formula, limit)
    failures = []
    for index in range(residue, limit+1, step):
        if coeffs[index].denominator != 1 or int(coeffs[index]) % modulus:
            failures.append(index)
    return {"holds_through": not failures, "failures": failures[:100], "checked_limit": limit}
