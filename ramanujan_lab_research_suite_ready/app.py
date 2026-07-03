import streamlit as st
import ast
import pandas as pd
import time
import re
import math
import os
import pickle
import hashlib
import shutil
import json
import base64
import zlib
import sqlite3
import secrets
import hmac
import tempfile
import subprocess
import concurrent.futures
import threading
import urllib.parse
import datetime as _dt
import io
import textwrap
from fractions import Fraction
from itertools import product
from functools import reduce

APP_VERSION = "5.0 Research Suite"
PUBLIC_WEB_MODE = os.getenv("RAMANUJAN_PUBLIC_WEB", "1") == "1"
CACHE_DIR = os.getenv("RAMANUJAN_CACHE_DIR", os.path.join("/tmp", "ramanujan_lab_cache"))
DATA_DIR = os.getenv("RAMANUJAN_DATA_DIR", os.path.join("/tmp", "ramanujan_lab_data"))
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ==========================================
# --- INITIALIZE APP, BRANDING & STATE ---
# ==========================================
st.set_page_config(
    page_title="Ramanujan Laboratory Pro",
    page_icon="∞",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://docs.streamlit.io/",
        "About": "Ramanujan Laboratory Pro — a browser-based laboratory for eta quotients, q-series dissections, congruence searches, and transparent derivation traces.",
    },
)

st.markdown(
    """
    <style>
      .stApp {
        background:
          radial-gradient(circle at 8% 4%, rgba(91, 124, 250, .13), transparent 28%),
          radial-gradient(circle at 92% 7%, rgba(156, 86, 255, .11), transparent 26%);
      }
      .ram-hero {
        padding: 1.25rem 1.45rem;
        border-radius: 20px;
        border: 1px solid rgba(130, 140, 180, .25);
        background: linear-gradient(120deg, rgba(28,35,62,.94), rgba(53,32,88,.91));
        box-shadow: 0 16px 42px rgba(20, 24, 50, .22);
        margin-bottom: 1rem;
      }
      .ram-hero h1 { margin: 0; color: #ffffff; font-size: 2.05rem; }
      .ram-hero p { margin: .35rem 0 0; color: #d9ddff; font-size: 1rem; }
      .ram-card {
        border: 1px solid rgba(128, 139, 180, .22);
        border-radius: 16px;
        padding: .9rem 1rem;
        background: rgba(255,255,255,.035);
      }
      div[data-testid="stMetric"] {
        border: 1px solid rgba(128, 139, 180, .20);
        border-radius: 14px;
        padding: .55rem .75rem;
        background: rgba(255,255,255,.025);
      }
      div[data-testid="stCodeBlock"] { border-radius: 14px; }
      .small-note { opacity: .76; font-size: .88rem; }
      .derivation-step {
        border-left: 4px solid rgba(123, 97, 255, .78);
        border-radius: 12px;
        padding: .78rem 1rem;
        margin: .55rem 0 .9rem;
        background: linear-gradient(90deg, rgba(111,82,255,.10), rgba(255,255,255,.018));
      }
      .derivation-step strong { color: #dcd6ff; }
      .identity-note {
        border: 1px solid rgba(114, 201, 255, .22);
        border-radius: 12px;
        padding: .65rem .8rem;
        margin: .4rem 0;
        background: rgba(68, 143, 190, .055);
      }
      .proof-badge {
        display: inline-block;
        border-radius: 999px;
        padding: .22rem .62rem;
        margin-right: .35rem;
        font-size: .78rem;
        border: 1px solid rgba(145, 125, 255, .33);
        background: rgba(118, 88, 255, .10);
      }
      .web-status {
        display: inline-flex; align-items: center; gap: .4rem;
        border: 1px solid rgba(67, 214, 154, .30);
        background: rgba(67, 214, 154, .08);
        padding: .28rem .65rem; border-radius: 999px;
        font-size: .78rem; color: #baf7dd;
      }
      .home-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .85rem; margin: .8rem 0 1.15rem;
      }
      .home-card {
        min-height: 145px;
        border: 1px solid rgba(128, 139, 180, .22);
        border-radius: 16px; padding: 1rem 1.05rem;
        background: linear-gradient(145deg, rgba(255,255,255,.04), rgba(112,82,255,.035));
      }
      .home-card h3 { margin: 0 0 .42rem; font-size: 1.02rem; color: #f6f4ff; }
      .home-card p { margin: 0; opacity: .78; line-height: 1.45; font-size: .90rem; }
      .app-footer {
        margin-top: 2.2rem; padding: .9rem 0 .25rem;
        border-top: 1px solid rgba(128,139,180,.16);
        opacity: .67; font-size: .80rem; text-align: center;
      }
      @media (max-width: 900px) {
        .home-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      }
      @media (max-width: 640px) {
        .ram-hero { padding: 1rem 1rem; border-radius: 15px; }
        .ram-hero h1 { font-size: 1.45rem; }
        .ram-hero p { font-size: .89rem; line-height: 1.42; }
        .home-grid { grid-template-columns: 1fr; }
        .home-card { min-height: auto; }
        div[data-testid="stCodeBlock"] pre { font-size: .77rem; }
        section[data-testid="stSidebar"] { min-width: 285px; }
      }
    </style>
    <div class="ram-hero">
      <h1>∞ Ramanujan Laboratory Research Suite</h1>
      <p>Dissections, modular certificates, Hecke operators, relations, moments, visualization, APIs, and reproducible reports.</p>
      <div style="margin-top:.65rem"><span class="web-status">● Public research-suite edition</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "latex_clipboard" not in st.session_state:
    st.session_state.latex_clipboard = []


def add_to_clipboard(source, latex_content):
    if not latex_content.strip().startswith("$$") and not latex_content.strip().startswith("%"):
        latex_content = f"$$\n{latex_content}\n$$"
    entry = f"% --- {source} ---\n{latex_content}"
    if entry not in st.session_state.latex_clipboard:
        st.session_state.latex_clipboard.append(entry)


def safe_widget_key(value):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value)).strip("_")[:120] or "latex"


def latex_document(title, body):
    return (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage{amsmath,amssymb}\n"
        "\\usepackage[margin=1in]{geometry}\n"
        "\\newcommand{\\f}[1]{f_{#1}}\n"
        "\\begin{document}\n"
        f"\\section*{{{title}}}\n"
        f"{body}\n"
        "\\end{document}\n"
    )


def render_latex_export(title, latex_code, key, filename=None, add_global=True):
    """Show copyable LaTeX and optional clipboard/download controls."""
    st.markdown(f"**{title}**")
    st.code(latex_code, language="latex")
    cols = st.columns(2 if add_global else 1)
    if add_global:
        with cols[0]:
            if st.button("Add to global LaTeX clipboard", key=f"clip_{safe_widget_key(key)}", use_container_width=True):
                add_to_clipboard(title, latex_code)
                st.toast("LaTeX added to the global clipboard.")
        download_col = cols[1]
    else:
        download_col = cols[0]
    with download_col:
        st.download_button(
            "Download .tex snippet",
            data=latex_code,
            file_name=filename or f"{safe_widget_key(key).lower()}.tex",
            mime="text/x-tex",
            key=f"download_{safe_widget_key(key)}",
            use_container_width=True,
        )


# ==========================================
# --- SHARED MATH ENGINE & PARSER ---
# ==========================================
class QSeries:
    """Truncated formal power series with exact rational coefficients."""

    def __init__(self, coeffs, limit):
        self.limit = int(limit)
        self.coeffs = [self._exact(c) for c in list(coeffs)[: self.limit + 1]]
        if len(self.coeffs) < self.limit + 1:
            self.coeffs += [Fraction(0)] * (self.limit + 1 - len(self.coeffs))

    @staticmethod
    def _exact(value):
        if isinstance(value, Fraction):
            return value
        if isinstance(value, int):
            return Fraction(value)
        if isinstance(value, float):
            return Fraction(str(value))
        return Fraction(value)

    @classmethod
    def one(cls, limit):
        return cls([1], limit)

    @classmethod
    def zero(cls, limit):
        return cls([0], limit)

    def _coerce(self, other):
        if isinstance(other, QSeries):
            if other.limit != self.limit:
                return QSeries(other.coeffs, self.limit)
            return other
        return QSeries([self._exact(other)], self.limit)

    def __neg__(self):
        return QSeries([-c for c in self.coeffs], self.limit)

    def __add__(self, other):
        other = self._coerce(other)
        return QSeries([a + b for a, b in zip(self.coeffs, other.coeffs)], self.limit)

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self.__add__(-self._coerce(other))

    def __rsub__(self, other):
        return self._coerce(other).__sub__(self)

    def __mul__(self, other):
        if not isinstance(other, QSeries):
            scalar = self._exact(other)
            return QSeries([scalar * c for c in self.coeffs], self.limit)
        C = [Fraction(0)] * (self.limit + 1)
        A_nz = [(i, a) for i, a in enumerate(self.coeffs) if a]
        B_nz = [(j, b) for j, b in enumerate(other.coeffs) if b]
        for i, a in A_nz:
            for j, b in B_nz:
                if i + j > self.limit:
                    break
                C[i + j] += a * b
        return QSeries(C, self.limit)

    def __rmul__(self, other):
        return self.__mul__(other)

    def inv(self):
        a0 = self.coeffs[0]
        if a0 == 0:
            raise ZeroDivisionError("A formal power series is invertible only when its constant term is nonzero.")
        B = [Fraction(0)] * (self.limit + 1)
        B[0] = 1 / a0
        for n in range(1, self.limit + 1):
            B[n] = -sum(self.coeffs[k] * B[n-k] for k in range(1, n + 1)) / a0
        return QSeries(B, self.limit)

    def __pow__(self, power):
        if not isinstance(power, int):
            raise TypeError("Formal-series powers must be integers.")
        if power < 0:
            return self.inv() ** (-power)
        result = QSeries.one(self.limit)
        base = self
        exponent = power
        while exponent:
            if exponent & 1:
                result = result * base
            exponent >>= 1
            if exponent:
                base = base * base
        return result

    def __truediv__(self, other):
        if isinstance(other, QSeries):
            return self * other.inv()
        scalar = self._exact(other)
        if scalar == 0:
            raise ZeroDivisionError("division by zero")
        return self * (1 / scalar)

    def __rtruediv__(self, other):
        return self.inv() * other

    def integral_coefficients(self):
        return all(c.denominator == 1 for c in self.coeffs)

    def as_python_numbers(self):
        return [int(c) if c.denominator == 1 else c for c in self.coeffs]

def generate_base_pochhammer(m, limit):
    A = [0] * (limit + 1); A[0] = 1; k = 1
    while True:
        p1 = m * k * (3 * k - 1) // 2
        p2 = m * k * (3 * k + 1) // 2
        sign = -1 if k % 2 != 0 else 1
        if p1 <= limit: A[p1] = sign
        if p2 <= limit: A[p2] = sign
        if p1 > limit and p2 > limit: break
        k += 1
    return A

def gen_phi(k, limit):
    C = [0] * (limit + 1)
    n = 0
    while n*n*k <= limit:
        C[n*n*k] += 1 if n == 0 else 2
        n += 1
    return QSeries(C, limit)

def gen_psi(k, limit):
    C = [0] * (limit + 1)
    n = 0
    while n*(n+1)//2 * k <= limit:
        C[n*(n+1)//2 * k] += 1
        n += 1
    return QSeries(C, limit)

def gen_fab(a, b, limit):
    C = [0] * (limit + 1)
    n = 0
    while True:
        exp_pos = a*(n*(n+1)//2) + b*(n*(n-1)//2)
        m = -n
        exp_neg = a*(m*(m+1)//2) + b*(m*(m-1)//2)
        added = False
        if exp_pos <= limit:
            C[exp_pos] += 1
            added = True
        if n != 0 and exp_neg <= limit:
            C[exp_neg] += 1
            added = True
        if not added and exp_pos > limit and exp_neg > limit:
            break
        n += 1
    return QSeries(C, limit)

def gen_Psi_ab(a, b, limit):
    C = [0] * (limit + 1)
    
    # Positive n (from 0 to infinity)
    n = 0
    while True:
        exp_pos = a * (n * (n + 1) // 2) + b * (n * (n - 1) // 2)
        if exp_pos <= limit:
            C[exp_pos] += 1
        elif n > 0: 
            break
        n += 1

    # Negative n (from -1 down to -infinity)
    n = -1
    while True:
        exp_neg = a * (n * (n + 1) // 2) + b * (n * (n - 1) // 2)
        if exp_neg <= limit:
            C[exp_neg] -= 1
        else:
            break
        n -= 1
        
    return QSeries(C, limit)

def q_pochhammer_series(k, n, limit):
    res = QSeries([1] + [0]*limit, limit)
    for j in range(1, n + 1):
        if k*j > limit: break
        term = QSeries([1] + [0]*limit, limit)
        term.coeffs[k*j] = -1
        res = res * term
    return res

def gen_G(k, limit):
    res = QSeries([0]*(limit+1), limit)
    n = 0
    while k * n * n <= limit:
        num = QSeries([0]*(limit+1), limit)
        num.coeffs[k*n*n] = 1
        den = q_pochhammer_series(k, n, limit)
        res = res + (num / den)
        n += 1
    return res

def gen_H(k, limit):
    res = QSeries([0]*(limit+1), limit)
    n = 0
    while k * n * (n+1) <= limit:
        num = QSeries([0]*(limit+1), limit)
        num.coeffs[k*n*(n+1)] = 1
        den = q_pochhammer_series(k, n, limit)
        res = res + (num / den)
        n += 1
    return res

def gen_R(k, limit):
    """R(q^k)=(q^k,q^{4k};q^{5k})_infty/(q^{2k},q^{3k};q^{5k})_infty."""
    k = int(k)
    if k <= 0:
        raise ValueError("R(q^k) requires k >= 1.")
    res = QSeries.one(limit)
    step = 5 * k
    n = 0
    while True:
        exponents = [k + n*step, 4*k + n*step, 2*k + n*step, 3*k + n*step]
        if min(exponents) > limit:
            break
        for idx, exponent in enumerate(exponents):
            if exponent > limit:
                continue
            term = QSeries.one(limit)
            term.coeffs[exponent] = -1
            res = res * term if idx < 2 else res / term
        n += 1
    return res

def latex_to_python(latex_str):
    """Convert the supported LaTeX subset to a restricted Python expression."""
    s = latex_str.replace('$', '').replace('\\,', '').replace('\r', '').replace('\n', '')
    function_patterns = [
        (r'\\(?:varphi|phi)\s*\(\s*q\^?\{?([0-9X]*)\}?\s*\)', 'phi'),
        (r'\\psi\s*\(\s*q\^?\{?([0-9X]*)\}?\s*\)', 'psi'),
        (r'G\s*\(\s*q\^?\{?([0-9X]*)\}?\s*\)', 'G'),
        (r'H\s*\(\s*q\^?\{?([0-9X]*)\}?\s*\)', 'H'),
        (r'R\s*\(\s*q\^?\{?([0-9X]*)\}?\s*\)', 'R'),
    ]
    for pattern, name in function_patterns:
        s = re.sub(pattern, lambda m, nm=name: f"{nm}({m.group(1) or '1'})", s)
    s = re.sub(r'\\Psi\s*\(\s*q\^?\{?([0-9X]*)\}?\s*,\s*q\^?\{?([0-9X]*)\}?\s*\)',
               lambda m: f"Psi({m.group(1) or '1'},{m.group(2) or '1'})", s)
    s = re.sub(r'\\Psi\s*\(\s*([0-9X]+)\s*,\s*([0-9X]+)\s*\)',
               lambda m: f"Psi({m.group(1)},{m.group(2)})", s)
    s = re.sub(r'f\s*\(\s*q\^?\{?([0-9X]*)\}?\s*,\s*q\^?\{?([0-9X]*)\}?\s*\)',
               lambda m: f"fab({m.group(1) or '1'},{m.group(2) or '1'})", s)

    def get_group(text, start_i):
        if start_i >= len(text):
            raise SyntaxError("Incomplete \\frac expression.")
        if text[start_i] != '{':
            return text[start_i], start_i + 1
        depth, i = 1, start_i + 1
        while depth and i < len(text):
            depth += (text[i] == '{') - (text[i] == '}')
            i += 1
        if depth:
            raise SyntaxError("Unbalanced braces in \\frac expression.")
        return text[start_i + 1:i - 1], i

    while r'\frac' in s:
        start = s.rfind(r'\frac')  # innermost-first makes nested fractions reliable
        idx = start + 5
        numerator, after_num = get_group(s, idx)
        denominator, after_den = get_group(s, after_num)
        s = s[:start] + f"(({numerator})/({denominator}))" + s[after_den:]

    s = re.sub(r'f_\{([^}]+)\}', r'f(\1)', s)
    s = re.sub(r'f_(\d+|[a-zA-Z])', r'f(\1)', s)
    s = s.replace(r'\left', '').replace(r'\right', '')
    s = s.replace(r'\cdot', '*').replace(r'\times', '*')
    s = s.replace('^', '**').replace('{', '(').replace('}', ')')
    s = s.replace(' ', '').replace('x', 'X')

    # Supported implicit multiplication.
    s = re.sub(r'\)(?=[A-Za-z0-9(])', r')*', s)
    s = re.sub(r'(?<=[0-9qX])(?=[A-Za-z(])', '*', s)
    s = re.sub(r'(?<=q)(?=[0-9])', '*', s)
    return s

def validate_python_formula(expression, allowed_names):
    """Reject attributes, comprehensions, indexing, lambdas, and unapproved calls before eval."""
    tree = ast.parse(expression, mode="eval")
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load,
        ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
        ast.UAdd, ast.USub,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise SyntaxError(f"Unsupported or unsafe syntax: {type(node).__name__}.")
        if isinstance(node, ast.Name) and node.id not in allowed_names:
            raise NameError(f"Unsupported symbol '{node.id}'.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in allowed_names:
                raise SyntaxError("Only approved q-series functions may be called.")
            if node.keywords:
                raise SyntaxError("Keyword arguments are not supported.")
    return tree

def restricted_eval(expression, environment):
    validate_python_formula(expression, set(environment) - {"__builtins__"})
    return eval(compile(ast.parse(expression, mode="eval"), "<q-series>", "eval"), environment)

def require_integral_coefficients(coeffs, context="this calculation"):
    output = []
    for n, coefficient in enumerate(coeffs):
        exact = coefficient if isinstance(coefficient, Fraction) else Fraction(coefficient)
        if exact.denominator != 1:
            raise ValueError(
                f"{context} requires integral coefficients, but the coefficient of q^{n} is {exact}."
            )
        output.append(exact.numerator)
    return output

def lcm(a, b): return abs(a*b) // math.gcd(a, b) if a and b else 0
def lcm_list(lst): return reduce(lcm, lst, 1) if lst else 1

def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

# ==========================================
# --- SMART CACHING ARCHITECTURE ---
# ==========================================
if "smart_ram_cache" not in st.session_state:
    st.session_state.smart_ram_cache = {}

def _core_expansion_engine(latex_str, limit):
    """Core mathematical evaluation logic."""
    def f(n): 
        if int(n) <= 0: return QSeries([1] + [0]*limit, limit)
        return QSeries(generate_base_pochhammer(int(n), limit), limit)
    
    q_obj = QSeries([0, 1] + [0]*limit, limit)
    python_formula = latex_to_python(latex_str)
    
    safe_env = {
        "f": f, "q": q_obj, "X": 1, 
        "phi": lambda k: gen_phi(int(k), limit), 
        "psi": lambda k: gen_psi(int(k), limit), 
        "G": lambda k: gen_G(int(k), limit), 
        "H": lambda k: gen_H(int(k), limit), 
        "R": lambda k: gen_R(int(k), limit),
        "fab": lambda a, b: gen_fab(int(a), int(b), limit), 
        "Psi": lambda a, b: gen_Psi_ab(int(a), int(b), limit),
        "__builtins__": {}
    }

    final_series = restricted_eval(python_formula, safe_env)
    if not isinstance(final_series, QSeries): 
        final_series = QSeries([int(final_series)] + [0]*limit, limit)
    return final_series.coeffs

def get_smart_expansion(latex_str, limit, persist_to_disk=False):
    """
    Checks if a larger or equal expansion already exists for this exact formula.
    If yes, it instantly slices and returns the subset. 
    If no, it computes the new ceiling and saves it.
    """
    if not persist_to_disk:
        cache = st.session_state.smart_ram_cache
        if latex_str in cache:
            if cache[latex_str]["limit"] >= limit:
                st.toast(f"⚡ Smart Cache Hit: Sliced from {cache[latex_str]['limit']:,} terms in RAM!")
                return cache[latex_str]["coeffs"][:limit + 1]
        
        coeffs = _core_expansion_engine(latex_str, limit)
        st.session_state.smart_ram_cache[latex_str] = {"limit": limit, "coeffs": coeffs}
        return coeffs
    else:
        cache_dir = CACHE_DIR
        os.makedirs(cache_dir, exist_ok=True)
        safe_name = hashlib.md5(latex_str.encode()).hexdigest()
        file_path = os.path.join(cache_dir, f"{safe_name}.pkl")
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                saved_data = pickle.load(f)
            if saved_data["limit"] >= limit:
                st.toast(f"⚡ Smart Cache Hit: Sliced from {saved_data['limit']:,} terms on Disk!")
                return saved_data["coeffs"][:limit + 1]
        
        coeffs = _core_expansion_engine(latex_str, limit)
        with open(file_path, "wb") as f:
            pickle.dump({"limit": limit, "coeffs": coeffs}, f)
        return coeffs

# ==========================================
# --- SYMBOLIC ALGEBRA ENGINE ---
# ==========================================
class SymTerm:
    def __init__(self, coeff=1, q_power=0, etas=None, specials=None):
        self.coeff = Fraction(coeff)
        self.q_power = int(q_power)
        self.etas = {int(k): int(v) for k, v in (etas or {}).items() if v}
        self.specials = {(str(name), int(k)): int(v) for (name, k), v in (specials or {}).items() if v}

    def key(self):
        return (self.q_power, frozenset(self.etas.items()), frozenset(self.specials.items()))

    def substitute_q(self, m):
        m = int(m)
        return SymTerm(
            self.coeff,
            self.q_power * m,
            {k*m: v for k, v in self.etas.items()},
            {(name, k*m): v for (name, k), v in self.specials.items()},
        )

    def simplify_mod(self, p):
        """Use f_k^p == f_{pk} (mod p), including negative exponents."""
        p = int(p)
        if p < 2:
            return self
        final = {}
        for k, exponent in self.etas.items():
            current_k, current_e = k, exponent
            while current_e:
                # Quotient truncated toward zero makes negative exponents terminate:
                # -6 = 5(-1) + (-1), hence f_k^-6 == f_k^-1 f_{5k}^-1 (mod 5).
                quotient = (abs(current_e) // p) * (1 if current_e > 0 else -1)
                remainder = current_e - p * quotient
                if remainder:
                    final[current_k] = final.get(current_k, 0) + remainder
                current_k *= p
                current_e = quotient
        return SymTerm(self.coeff, self.q_power, final, self.specials)

    def apply_Up(self, p, r=0):
        if self.q_power % p != r:
            return None
        if any(k % p for k in self.etas):
            raise ValueError(f"A displayed term contains f_k with p not dividing k; it is not visibly a q^{p}-series.")
        if any(k % p for (_, k) in self.specials):
            raise ValueError(f"A displayed special factor is not visibly a q^{p}-series.")
        return SymTerm(
            self.coeff,
            (self.q_power-r)//p,
            {k//p: v for k, v in self.etas.items()},
            {(name, k//p): v for (name, k), v in self.specials.items()},
        )

    def __mul__(self, other):
        if isinstance(other, (int, float, Fraction)):
            return SymTerm(self.coeff * Fraction(other), self.q_power, self.etas, self.specials)
        etas = self.etas.copy()
        for k, v in other.etas.items():
            etas[k] = etas.get(k, 0) + v
        specials = self.specials.copy()
        for key, v in other.specials.items():
            specials[key] = specials.get(key, 0) + v
        return SymTerm(self.coeff*other.coeff, self.q_power+other.q_power, etas, specials)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, (int, float, Fraction)):
            return SymTerm(self.coeff/Fraction(other), self.q_power, self.etas, self.specials)
        return self * SymTerm(1/other.coeff, -other.q_power,
                              {k: -v for k, v in other.etas.items()},
                              {key: -v for key, v in other.specials.items()})

    def __rtruediv__(self, other):
        return SymTerm(other) / self

    def __pow__(self, power):
        if not isinstance(power, int):
            raise ValueError("Symbolic powers must be integers.")
        return SymTerm(self.coeff**power, self.q_power*power,
                       {k: v*power for k, v in self.etas.items()},
                       {key: v*power for key, v in self.specials.items()})

    @staticmethod
    def _factor_latex(name, k):
        qarg = "q" if k == 1 else f"q^{{{k}}}"
        return f"{name}({qarg})"

    def to_latex(self):
        if self.coeff == 0:
            return ""
        sign = "+" if self.coeff > 0 else "-"
        abs_c = abs(self.coeff)
        numerator, denominator = [], []
        if self.q_power:
            numerator.append("q" if self.q_power == 1 else f"q^{{{self.q_power}}}")
        for d in sorted(self.etas):
            exponent = self.etas[d]
            factor = f"f_{{{d}}}" + (f"^{{{abs(exponent)}}}" if abs(exponent) != 1 else "")
            (numerator if exponent > 0 else denominator).append(factor)
        for (name, k), exponent in sorted(self.specials.items()):
            factor = self._factor_latex(name, k) + (f"^{{{abs(exponent)}}}" if abs(exponent) != 1 else "")
            (numerator if exponent > 0 else denominator).append(factor)
        if abs_c != 1 or (not numerator and not denominator):
            coefficient = str(abs_c.numerator) if abs_c.denominator == 1 else rf"\frac{{{abs_c.numerator}}}{{{abs_c.denominator}}}"
            numerator.insert(0, coefficient)
        top = " ".join(numerator) or "1"
        bottom = " ".join(denominator)
        return sign + (rf"\frac{{{top}}}{{{bottom}}}" if bottom else top)


class SymExpr:
    def __init__(self, terms):
        self.terms = [terms] if isinstance(terms, SymTerm) else list(terms)
        self.simplify()

    def simplify(self):
        grouped = {}
        for term in self.terms:
            key = term.key()
            if key not in grouped:
                grouped[key] = SymTerm(0, term.q_power, term.etas, term.specials)
            grouped[key].coeff += term.coeff
        self.terms = [t for t in grouped.values() if t.coeff]
        self.terms.sort(key=lambda t: (t.q_power, len(t.etas)+len(t.specials), sorted(t.etas.items())))

    def substitute_q(self, m):
        return SymExpr([t.substitute_q(m) for t in self.terms])

    def simplify_mod(self, p):
        return SymExpr([t.simplify_mod(p) for t in self.terms])

    def apply_Up(self, p, r=0):
        terms = [u for t in self.terms if (u := t.apply_Up(p, r)) is not None]
        return SymExpr(terms or [SymTerm(0)])

    def components(self, p):
        result = {}
        for r in range(p):
            terms = [u for t in self.terms if (u := t.apply_Up(p, r)) is not None]
            result[r] = SymExpr(terms or [SymTerm(0)])
        return result

    def __add__(self, other):
        if isinstance(other, SymExpr):
            return SymExpr(self.terms + other.terms)
        if isinstance(other, SymTerm):
            return SymExpr(self.terms + [other])
        return SymExpr(self.terms + [SymTerm(other)])

    __radd__ = __add__

    def __sub__(self, other):
        return self + (-1)*other

    def __rsub__(self, other):
        return other + (-1)*self

    def __mul__(self, other):
        if isinstance(other, (int, float, Fraction, SymTerm)):
            return SymExpr([t*other for t in self.terms])
        return SymExpr([a*b for a in self.terms for b in other.terms])

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, (int, float, Fraction, SymTerm)):
            return SymExpr([t/other for t in self.terms])
        if isinstance(other, SymExpr) and len(other.terms) == 1:
            return self / other.terms[0]
        raise ValueError("Division by a multi-term symbolic expression is not a finite dissection.")

    def __rtruediv__(self, other):
        if len(self.terms) != 1:
            raise ValueError("Division by a sum is not supported in exact symbolic mode.")
        return SymExpr([other/self.terms[0]])

    def __pow__(self, power):
        if not isinstance(power, int) or power < 0:
            raise ValueError("A finite symbolic dissection can only be raised to a non-negative integer power.")
        result = SymExpr([SymTerm(1)])
        base, exponent = self, power
        while exponent:
            if exponent & 1:
                result = result*base
            exponent >>= 1
            if exponent:
                base = base*base
        return result

    def to_latex(self):
        if not self.terms:
            return "0"
        out = ""
        for i, term in enumerate(self.terms):
            text = term.to_latex()
            if i == 0:
                out += text[1:] if text.startswith('+') else text
            elif text.startswith('-'):
                out += " - " + text[1:]
            else:
                out += " + " + text[1:]
        return out or "0"

    @property
    def term_count(self):
        return len(self.terms)


def scale_latex_lhs(s, m):
    if m == 1:
        return s
    s = re.sub(r'f_\{(\d+)\}', lambda x: f"f_{{{int(x.group(1))*m}}}", s)
    return re.sub(r'f_(\d+)', lambda x: f"f_{{{int(x.group(1))*m}}}", s)

# ==========================================
# --- ETA-QUOTIENT ANALYSIS ENGINE ---
# ==========================================
class EtaDictTerm:
    def __init__(self, terms=None, scalar=1):
        self.terms = {int(d): int(e) for d, e in (terms or {}).items() if e}
        self.scalar = Fraction(scalar)

    def __mul__(self, other):
        if isinstance(other, (int, Fraction)):
            return EtaDictTerm(self.terms, self.scalar*other)
        terms = self.terms.copy()
        for d, e in other.terms.items():
            terms[d] = terms.get(d, 0) + e
        return EtaDictTerm(terms, self.scalar*other.scalar)

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, (int, Fraction)):
            return EtaDictTerm(self.terms, self.scalar/other)
        terms = self.terms.copy()
        for d, e in other.terms.items():
            terms[d] = terms.get(d, 0) - e
        return EtaDictTerm(terms, self.scalar/other.scalar)

    def __rtruediv__(self, other):
        return EtaDictTerm({d: -e for d, e in self.terms.items()}, Fraction(other, 1)/self.scalar)

    def __pow__(self, power):
        if not isinstance(power, int):
            raise ValueError("Eta-product exponents must be integers.")
        return EtaDictTerm({d: e*power for d, e in self.terms.items()}, self.scalar**power)

    @staticmethod
    def _reject_additive_input():
        raise ValueError(
            "This eta-multiplier field accepts one product/quotient only. "
            "For sums or differences, use the Automatic p-Dissection Solver or the Composite Dissection Lab."
        )

    def __add__(self, other):
        self._reject_additive_input()

    __radd__ = __add__

    def __sub__(self, other):
        self._reject_additive_input()

    def __rsub__(self, other):
        self._reject_additive_input()


def parse_eta_product(latex_input):
    def f_dict(n):
        n = int(n)
        if n <= 0:
            raise ValueError("Every f-subscript must be positive.")
        return EtaDictTerm({n: 1})
    obj = restricted_eval(latex_to_python(latex_input), {"f": f_dict, "__builtins__": {}})
    if isinstance(obj, (int, Fraction)):
        obj = EtaDictTerm({}, obj)
    if not isinstance(obj, EtaDictTerm):
        raise ValueError("This module accepts a pure product/quotient of f_d factors.")
    if obj.scalar != 1:
        raise ValueError("Remove scalar constants; they do not affect eta modularity.")
    return obj.terms


def get_divisors(n):
    return [d for d in range(1, int(n)+1) if n % d == 0]


def prime_factorization(n):
    n = abs(int(n))
    factors = {}
    d = 2
    while d*d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def gamma0_index(N):
    value = Fraction(N)
    for p in prime_factorization(N):
        value *= Fraction(p+1, p)
    return int(value)


def eta_product_latex(exponents, symbol="eta"):
    numerator, denominator = [], []
    for d in sorted(exponents):
        e = exponents[d]
        if not e:
            continue
        if symbol == "eta":
            base = rf"\eta({d}z)" if d != 1 else r"\eta(z)"
        else:
            base = f"f_{{{d}}}"
        factor = base if abs(e) == 1 else base + f"^{{{abs(e)}}}"
        (numerator if e > 0 else denominator).append(factor)
    top = " ".join(numerator) or "1"
    bottom = " ".join(denominator)
    return rf"\frac{{{top}}}{{{bottom}}}" if bottom else top


def squarefree_character_kernel(exponents, weight):
    parity = {}
    for delta, exponent in exponents.items():
        for p, valuation in prime_factorization(delta).items():
            parity[p] = (parity.get(p, 0) + exponent*valuation) % 2
    D = -1 if int(weight) % 2 else 1
    for p, bit in parity.items():
        if bit:
            D *= p
    return D


def analyze_eta_quotient(exponents, N):
    N = int(N)
    if N <= 0:
        raise ValueError("Level N must be positive.")
    bad = [d for d in exponents if N % d]
    if bad:
        raise ValueError(f"The proposed level {N} is not divisible by subscripts {bad}.")
    weight = Fraction(sum(exponents.values()), 2)
    sum_T = sum(delta*e for delta, e in exponents.items())
    sum_S = sum((N//delta)*e for delta, e in exponents.items())
    integral_weight = weight.denominator == 1
    newman_T = sum_T % 24 == 0
    newman_S = sum_S % 24 == 0
    orders = {}
    for c in get_divisors(N):
        order = Fraction(N, 24*math.gcd(c*c, N)) * sum(
            Fraction(math.gcd(c, delta)**2 * e, delta)
            for delta, e in exponents.items()
        )
        orders[c] = order
    holomorphic = all(order >= 0 for order in orders.values())
    cuspidal = all(order > 0 for order in orders.values())
    modular = integral_weight and newman_T and newman_S
    index = gamma0_index(N)
    sturm = math.floor(Fraction(int(weight)*index, 12)) if modular and holomorphic and weight >= 0 else None
    q_shift = Fraction(sum_T, 24)
    character_D = squarefree_character_kernel(exponents, weight) if integral_weight else None
    return {
        "N": N, "weight": weight, "sum_T": sum_T, "sum_S": sum_S,
        "newman_T": newman_T, "newman_S": newman_S,
        "integral_weight": integral_weight, "orders": orders,
        "holomorphic": holomorphic, "cuspidal": cuspidal,
        "modular": modular, "index": index, "sturm": sturm,
        "q_shift": q_shift, "character_D": character_D,
    }


def compute_euler_exponents(c_array, max_terms):
    def mobius(n):
        if n == 1:
            return 1
        factors = prime_factorization(n)
        if sum(factors.values()) != len(factors):
            return 0
        return -1 if len(factors) % 2 else 1
    W = [Fraction(0)]*(max_terms+1)
    for m in range(1, max_terms+1):
        W[m] = m*c_array[m] - sum(W[k]*c_array[m-k] for k in range(1, m))
    a = [Fraction(0)]*(max_terms+1)
    for n in range(1, max_terms+1):
        a[n] = sum(mobius(n//d)*W[d] for d in get_divisors(n))/n
    return [int(x) if x.denominator == 1 else x for x in a]


def format_latex_frac(value):
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else rf"\frac{{{value.numerator}}}{{{value.denominator}}}"


def find_eta_multipliers(N, base_dict_items, min_e, max_e, target_k=None,
                         targeted_divs=None, limit_n=20, limit_sturm=None,
                         max_combinations=250000):
    base = dict(base_dict_items)
    divisors = list(targeted_divs) if targeted_divs else get_divisors(N)
    if not divisors:
        return [], 0, False
    theoretical = (max_e-min_e+1)**len(divisors)
    checked = 0
    truncated = theoretical > max_combinations
    results = []
    for combo in product(range(min_e, max_e+1), repeat=len(divisors)):
        checked += 1
        if checked > max_combinations:
            break
        multiplier = {d: e for d, e in zip(divisors, combo) if e}
        total = base.copy()
        for d, e in multiplier.items():
            total[d] = total.get(d, 0) + e
            if not total[d]:
                total.pop(d)
        try:
            analysis = analyze_eta_quotient(total, N)
        except ValueError:
            continue
        if not (analysis["modular"] and analysis["holomorphic"]):
            continue
        if target_k is not None and analysis["weight"] != target_k:
            continue
        if analysis["weight"] <= 0:
            continue
        if limit_sturm is not None and analysis["sturm"] is not None and analysis["sturm"] > limit_sturm:
            continue
        results.append({"multiplier": multiplier, "total": total, **analysis})
    results.sort(key=lambda x: (sum(abs(v) for v in x["multiplier"].values()), x["weight"], x["sturm"] or 0))
    return results[:limit_n] if limit_n else results, checked, truncated


def generate_latex_export(base_dict, item):
    M_f = eta_product_latex(item["multiplier"], "f")
    total_eta = eta_product_latex(item["total"], "eta")
    return (
        "% Corrected eta-quotient certificate\n"
        f"% F(q) = {eta_product_latex(base_dict, 'f')}\n"
        f"% M(q) = {M_f}\n"
        f"% q^({format_latex_frac(item['q_shift'])}) F(q)M(q) = {total_eta}\n"
        f"% Weight = {format_latex_frac(item['weight'])}, level = {item['N']}\n"
        f"% Newman sums: {item['sum_T']} == 0 (mod 24), "
        f"{item['sum_S']} == 0 (mod 24)\n"
        f"% Character: chi(d) = ({item['character_D']}/d)\n"
        f"% Sturm bound = {item['sturm']}\n"
        f"{M_f}"
    )

# ==========================================
# --- MODULE 1: INFINITE FAMILY MINER ---
# ==========================================
def run_infinite_family_miner():
    st.title("♾️ Infinite-Family Pattern Miner")
    st.markdown("Search finite coefficient data for geometric progression patterns. A returned family is a **conjectural pattern**, not a proof, unless it is later certified by an exact identity or a valid Sturm bound.")

    def ifm_targeted_sieve(coeffs, mod, max_k, bases, min_A0, max_A0, safety_divisor):
        N = len(coeffs)
        hits = set()
        for base in bases:
            for A0 in range(min_A0, max_A0 + 1):
                for k in range(max_k + 1):
                    A = A0 * (base ** k)
                    if A < 2 or A > N / safety_divisor: continue 
                    for B in range(A):
                        sequence = [coeffs[i] for i in range(B, N, A) if i != 0]
                        if len(sequence) >= 5 and all(term % mod == 0 for term in sequence):
                            hits.add((A, B))
                            
        sorted_hits = sorted(list(hits), key=lambda x: x[0])
        fundamental_hits = []
        for A, B in sorted_hits:
            is_trivial = False
            for A_f, B_f in fundamental_hits:
                if A % A_f == 0 and B % A_f == B_f:
                    is_trivial = True
                    break
            if not is_trivial: fundamental_hits.append((A, B))
        return fundamental_hits

    def ifm_detect_infinite_families(hits, mod):
        if len(hits) < 3: return []
        families = []
        for i in range(len(hits) - 2):
            A0, B0 = hits[i]
            for j in range(i + 1, len(hits) - 1):
                A1, B1 = hits[j]
                if A1 % A0 != 0: continue
                R = A1 // A0
                if R <= 1: continue
                num = B1 - B0
                den = R - 1
                c1 = Fraction(num, den)
                c2 = Fraction(B0) - c1
                A2 = A1 * R
                expected_B2 = int(c1 * (R**2) + c2)
                if (A2, expected_B2) in hits:
                    families.append({"A0": A0, "R": R, "c1": c1, "c2": c2, "mod": mod})
        return families

    with st.sidebar:
        st.header("⚙️ 1. Search Limits")
        st.caption("Exact pure-Python expansions above roughly 20,000 terms can be very expensive; begin with a smaller search and extend only promising cases.")
        N = st.number_input("Terms to Generate ($N$)", min_value=500, value=10000, step=500)
        max_k = st.number_input("Max Search Depth ($k$)", min_value=3, value=8)
        
        st.markdown("### Memory / Caching Strategy")
        cache_mode = st.radio(
            "Save Computations:",
            ["Temporarily (RAM - Clears on exit)", "Permanently (Disk - Survives reboots)"],
            index=0
        )
        
        st.markdown("### Advanced Optimization")
        safety_divisor = st.selectbox(
            "Safety Valve Threshold (N divisor)",
            options=[6.0, 4.8],
            format_func=lambda x: "Strict (N // 6) - Requires massive N" if x == 6.0 else "Optimized (N / 4.8) - Saves computation",
            index=1
        )

        st.markdown("### Base Step Range ($A_0$)")
        col1, col2 = st.columns(2)
        min_A0 = col1.number_input("Min $A_0$", min_value=1, value=1)
        max_A0 = col2.number_input("Max $A_0$", min_value=min_A0, value=30)
        
        st.header("🎯 2. Target Vectors")
        manual_mods = st.text_input("Target Moduli ($p$):", value="5")
        manual_bases = st.text_input("Step Bases ($R$):", value="25")

    st.subheader("1. Define Parametric Series")
    st.info("Powered by the Global Symbolic Engine. Supports additions, subtractions, and special functions like `\\psi(q)`.")
    user_input = st.text_area("Enter Series LaTeX Formula:", value=r"\frac{1}{f_1 f_2^2}")
    st.latex(user_input)
    st.markdown("---")

    if st.button("🚀 Execute Deep Sieve", type="primary", use_container_width=True):
        try:
            test_mods = [int(m.strip()) for m in manual_mods.split(",") if m.strip().isdigit()]
            test_bases = [int(b.strip()) for b in manual_bases.split(",") if b.strip().isdigit()]
            
            if not test_mods or not test_bases:
                st.error("Please enter valid numbers."); st.stop()

            with st.spinner(f"Generating first {N:,} terms algebraically (Smart Cached)..."):
                start_time = time.time()
                if cache_mode.startswith("Temporarily"):
                    coeffs = get_smart_expansion(user_input, N, persist_to_disk=False)
                else:
                    coeffs = get_smart_expansion(user_input, N, persist_to_disk=True)
                coeffs = require_integral_coefficients(coeffs, "the congruence sieve")
                
            st.success(f"Series expansion $O(q^{{{N}}})$ ready in {time.time() - start_time:.3f} seconds.")
            
            all_families = []
            all_raw_hits = {}
            
            with st.spinner("Sieving vectors and applying Triviality Filter..."):
                for mod in test_mods:
                    raw_hits = ifm_targeted_sieve(coeffs, mod, max_k, test_bases, min_A0, max_A0, safety_divisor)
                    if raw_hits:
                        all_raw_hits[mod] = raw_hits
                        families = ifm_detect_infinite_families(raw_hits, mod)
                        all_families.extend(families)

            st.subheader("📊 Analysis Results")
            tab1, tab2, tab3 = st.tabs(["✨ Conjectural Geometric Families", "🎯 Finite-data Progressions", "🧮 Series Expansion Data"])
            
            with tab1:
                if not all_families:
                    st.warning("No three-level geometric pattern was detected in this finite search space.")
                else:
                    st.warning(f"Found {len(all_families)} conjectural geometric pattern(s). These are not yet infinite-family proofs.")
                    collected_latex_lines = []
                    
                    for fam in all_families:
                        mod, A0, R, c1, c2 = fam['mod'], fam['A0'], fam['R'], fam['c1'], fam['c2']
                        c1_str = f"\\frac{{{abs(c1.numerator)}}}{{{c1.denominator}}}" if c1.denominator != 1 else str(abs(c1.numerator))
                        c2_str = f"\\frac{{{abs(c2.numerator)}}}{{{c2.denominator}}}" if c2.denominator != 1 else str(abs(c2.numerator))
                        
                        c1_sign = "+" if c1 >= 0 else "-"
                        c2_sign = "+" if c2 >= 0 else "-"
                        
                        display_str = rf"c\left( {A0} \cdot {R}^k \cdot n {c1_sign} {c1_str} \cdot {R}^k {c2_sign} {c2_str} \right) \overset{{?}}{{\equiv}} 0 \pmod {{{mod}}} \quad (k\ge 0)"
                        aligned_str = rf"c\left( {A0} \cdot {R}^k \cdot n {c1_sign} {c1_str} \cdot {R}^k {c2_sign} {c2_str} \right) &\overset{{?}}{{\equiv}} 0 \pmod {{{mod}}} \quad (k\ge 0)"
                        
                        st.latex(display_str)
                        collected_latex_lines.append(aligned_str)
                        
                    bulk_latex_string = "\\begin{aligned}\n" + " \\\\\n".join(collected_latex_lines) + "\n\\end{aligned}"
                    add_to_clipboard("Conjectural geometric families", bulk_latex_string)
                    st.info("The conjectural formulas were sent to the LaTeX clipboard with a question mark over the congruence sign.")
                        
            with tab2:
                if not all_raw_hits: st.warning("No standalone progressions found.")
                else:
                    for mod, hits in all_raw_hits.items():
                        st.markdown(f"### Modulo {mod}")
                        st.dataframe(pd.DataFrame(hits, columns=["A (Step)", "B (Offset)"]), use_container_width=True)
                        
            with tab3:
                st.write(coeffs[:100])

        except SyntaxError as e:
            st.error(f"❌ **Syntax Error:** `{e}`. Ensure you use standard notation.")
        except Exception as e:
            st.error(f"Execution Error. Details: {e}")

# ==========================================
# --- MODULE 2: CONGRUENCE MINER ---
# ==========================================
def run_congruence_miner():
    st.title("⛏️ Computational $q$-Series Congruence Miner")
    st.warning("A finite coefficient check finds candidates and counterexamples. It proves a congruence only when a separate exact-dissection or Sturm certificate is supplied.")

    with st.sidebar:
        st.header("⚙️ 1. Series Definition")
        template_cols = st.columns([3, 1])
        with template_cols[0]:
            template = st.selectbox("📖 Insert Special Function:", ["Select a template...", r"\frac{1}{f_1 \psi(q^3)}", r"\varphi(q^2)"])
        with template_cols[1]:
            st.write(""); st.write("")
            if st.button("Inject") and template != "Select a template...":
                st.session_state.miner_latex_input = template
                st.rerun()
                
        if "miner_latex_input" not in st.session_state: st.session_state.miner_latex_input = r"\frac{1}{f_1 \psi(q^3)}"
        latex_input = st.text_area("Enter LaTeX Formula:", value=st.session_state.miner_latex_input, height=80)
        st.latex(latex_input)
        st.divider()

        st.markdown("### 🧮 Inject False Theta $\\Psi(a,b)$")
        col_a, col_b = st.columns(2)
        psi_a = col_a.number_input("Parameter a (power of q)", value=1, min_value=0, key="psi_a")
        psi_b = col_b.number_input("Parameter b (power of q)", value=2, min_value=0, key="psi_b")
        
        if st.button("Inject $\\Psi(q^a, q^b)$"):
            st.session_state.miner_latex_input = rf"\Psi(q^{{{psi_a}}}, q^{{{psi_b}}})"
            st.rerun()
            
        st.divider()
        
        st.header("🔍 2. Analysis Mode")
        mode = st.radio("Select Tool:", [
            "Single Pattern Check", 
            "Full Progression Sweep", 
            "Hunter Mode (Run until found)", 
            "Parametric Family Search",
            "Prime Sieve Sweep (Primes ≤ n)"
        ])
        st.divider()
        
        if mode == "Single Pattern Check":
            col_k, col_r, col_M = st.columns(3)
            A_val, B_val, M_val = col_k.number_input("k", value=5), col_r.number_input("r", value=4), col_M.number_input("M", value=5)
        elif mode == "Full Progression Sweep":
            col_k, col_M = st.columns(2)
            sweep_k, sweep_M = col_k.number_input("Stride (k)", value=5), col_M.number_input("Modulus (M)", value=5)
        elif mode == "Prime Sieve Sweep (Primes ≤ n)":
            col_p, col_k = st.columns(2)
            max_p = col_p.number_input("Max Prime (n)", value=13, min_value=2)
            hunt_max = col_k.number_input("Max k to search", value=50)
        elif mode == "Parametric Family Search":
            col_min, col_max = st.columns(2)
            x_min, x_max = col_min.number_input("X Start", value=1), col_max.number_input("X End", value=5)
            hunt_M, hunt_max = st.number_input("Modulus", value=5), st.number_input("Stop k", value=20)
        else:
            hunt_M = st.number_input("Modulus", value=5)
            hunt_strategy = st.radio("Strategy:", ["Stop at First", "Collect Multiple"])
            hunt_bounty_limit = st.number_input("Max Bounties", value=10) if hunt_strategy == "Collect Multiple" else 1 
            hunt_max = st.number_input("Stop k", value=100)
            
        st.divider()
        limit = st.number_input("Terms to compute (N)", value=3000, step=100)
        
        st.markdown("### Memory / Caching")
        cache_mode = st.radio("Save Computations:", ["Temporarily (RAM)", "Permanently (Disk)"], key="miner_cache")
        run_btn = st.button("🚀 Run Miner", type="primary", use_container_width=True)

    if run_btn:
        try:
            if cache_mode.startswith("Temporarily"):
                F_q = get_smart_expansion(latex_input, limit, persist_to_disk=False)
            else:
                F_q = get_smart_expansion(latex_input, limit, persist_to_disk=True)
            F_q = require_integral_coefficients(F_q, "the congruence miner")

            if mode == "Parametric Family Search":
                def build_env(x_val=1):
                    q_obj = QSeries([0, 1] + [0]*limit, limit)
                    def f(n): 
                        if int(n) <= 0: return QSeries([1] + [0]*limit, limit)
                        return QSeries(generate_base_pochhammer(int(n), limit), limit)
                    return {"f": f, "q": q_obj, "X": x_val, "phi": lambda k: gen_phi(int(k), limit), "psi": lambda k: gen_psi(int(k), limit), "G": lambda k: gen_G(int(k), limit), "H": lambda k: gen_H(int(k), limit), "R": lambda k: gen_R(int(k), limit), "fab": lambda a, b: gen_fab(int(a), int(b), limit), "Psi": lambda a, b: gen_Psi_ab(int(a), int(b), limit), "__builtins__": {}}
                
                family_results = []
                python_formula = latex_to_python(latex_input)
                with st.spinner("Scanning..."):
                    for x_val in range(int(x_min), int(x_max) + 1):
                        try:
                            final_series = restricted_eval(python_formula, build_env(x_val))
                            if not isinstance(final_series, QSeries): final_series = QSeries([int(final_series)] + [0]*limit, limit)
                            F_q_param = require_integral_coefficients(final_series.coeffs, f"the X={x_val} congruence search")
                            found_for_x = []
                            fundamental_hits = []
                            
                            for current_k in range(2, hunt_max + 1):
                                for r in range(current_k):
                                    max_n = (limit - r) // current_k
                                    if max_n < 5: continue 
                                    
                                    is_trivial = False
                                    for hit_k, hit_r in fundamental_hits:
                                        if current_k % hit_k == 0 and r % hit_k == hit_r:
                                            is_trivial = True; break
                                    if is_trivial: continue
                                    
                                    is_congruent = True
                                    for n_val in range(max_n + 1):
                                        idx = current_k * n_val + r
                                        if idx == 0: continue 
                                        if idx <= limit and F_q_param[idx] % hunt_M != 0:
                                            is_congruent = False; break
                                    if is_congruent: 
                                        fundamental_hits.append((current_k, r))
                                        found_for_x.append(rf"c({current_k}n + {r}) \equiv 0 \pmod{{{hunt_M}}}")
                                        
                            if found_for_x: 
                                family_results.append({"X Value": x_val, f"Finite-data candidates mod {hunt_M}": ", ".join(found_for_x)})
                                add_to_clipboard(f"Parametric Congruences (X={x_val})", " \\\\\n".join(found_for_x))
                        except Exception as e: pass
                st.info(f"Trivial sub-progressions were filtered. Every displayed row was checked only through q^{limit}.")
                st.table(pd.DataFrame(family_results))

            elif mode == "Single Pattern Check":
                checked, failures = 0, []
                max_n = (limit - B_val) // A_val
                for n_val in range(max_n + 1):
                    idx = A_val * n_val + B_val
                    if idx == 0:
                        continue
                    if idx > limit:
                        break
                    checked += 1
                    if F_q[idx] % M_val != 0:
                        failures.append({"n": n_val, "index": idx, "coefficient": F_q[idx], "residue": F_q[idx] % M_val})
                if checked == 0:
                    st.warning("No positive-index term in this progression lies inside the selected expansion range.")
                elif failures:
                    st.error(f"Counterexample found after checking {checked} term(s).")
                    st.dataframe(pd.DataFrame(failures[:20]), use_container_width=True, hide_index=True)
                else:
                    st.success(f"No counterexample among {checked} checked term(s), through coefficient index {limit}.")
                    lat_str = rf"c({A_val}n + {B_val}) \overset{{?}}{{\equiv}} 0 \pmod{{{M_val}}}"
                    st.latex(lat_str)
                    add_to_clipboard("Finite-data congruence candidate", lat_str)
                    
            elif mode == "Full Progression Sweep":
                found_congruences = []
                fundamental_hits = []
                for r in range(sweep_k):
                    max_n = (limit - r) // sweep_k
                    if max_n < 5: continue 
                    
                    is_congruent = True
                    for n_val in range(max_n + 1):
                        idx = sweep_k * n_val + r
                        if idx == 0: continue 
                        if idx <= limit and F_q[idx] % sweep_M != 0: 
                            is_congruent = False; break
                    if is_congruent: 
                        found_congruences.append((sweep_k, r, max_n + 1))
                        
                if found_congruences:
                    st.success(f"Found {len(found_congruences)} finite-data candidate progression(s), checked only through q^{limit}.")
                    lat_strs = [rf"c({k}n + {r}) \equiv 0 \pmod{{{sweep_M}}}" for k, r, _ in found_congruences]
                    for ls in lat_strs: st.latex(ls)
                    add_to_clipboard("Sweep Congruences", " \\\\\n".join(lat_strs))

            elif mode == "Prime Sieve Sweep (Primes ≤ n)":
                primes = [p for p in range(2, int(max_p) + 1) if is_prime(p)]
                sieve_results = []
                progress_bar = st.progress(0)

                with st.spinner(f"Sieving primes up to {int(max_p)}..."):
                    for idx, p in enumerate(primes):
                        found_for_p = False
                        for current_k in range(2, int(hunt_max) + 1):
                            if found_for_p: break
                            for r in range(current_k):
                                max_n = (limit - r) // current_k
                                if max_n < 5: continue

                                is_congruent = True
                                for n_val in range(max_n + 1):
                                    idx_q = current_k * n_val + r
                                    if idx_q == 0: continue
                                    if idx_q <= limit and F_q[idx_q] % p != 0:
                                        is_congruent = False; break

                                if is_congruent:
                                    res_lat = rf"c({current_k}n + {r}) \equiv 0 \pmod{{{p}}}"
                                    sieve_results.append({"Prime (p)": p, "k": current_k, "r": r, "Congruence": res_lat})
                                    add_to_clipboard(f"Finite-data sieve candidate mod {p}", res_lat)
                                    found_for_p = True
                                    break
                        progress_bar.progress((idx + 1) / len(primes))

                if sieve_results:
                    st.success(f"Found finite-data candidates for {len(sieve_results)} prime(s), each checked only through q^{limit}.")
                    for item in sieve_results:
                        st.latex(item["Congruence"])
                    st.dataframe(pd.DataFrame(sieve_results).drop(columns=["Congruence"]), use_container_width=True)
                else:
                    st.warning("No congruences found for these primes within the search limit.")

            else:
                found_matches = []
                for current_k in range(2, hunt_max + 1):
                    for r in range(current_k):
                        max_n = (limit - r) // current_k
                        if max_n < 5: continue 
                        
                        is_trivial = False
                        for hit in found_matches:
                            if current_k % hit['k'] == 0 and r % hit['k'] == hit['r']:
                                is_trivial = True; break
                        if is_trivial: continue
                        
                        is_congruent = True
                        for n_val in range(max_n + 1):
                            idx = current_k * n_val + r
                            if idx == 0: continue 
                            if idx <= limit and F_q[idx] % hunt_M != 0: 
                                is_congruent = False; break
                        if is_congruent:
                            found_matches.append({"k": current_k, "r": r, "terms": max_n + 1})
                            if len(found_matches) >= hunt_bounty_limit: break
                    if len(found_matches) >= hunt_bounty_limit: break
                    
                if found_matches:
                    st.success(f"Found {len(found_matches)} finite-data candidate(s); trivial subsets were ignored and checking stopped at q^{limit}.")
                    lat_strs = [rf"c({hit['k']}n + {hit['r']}) \equiv 0 \pmod{{{hunt_M}}}" for hit in found_matches]
                    for ls in lat_strs: st.latex(ls)
                    add_to_clipboard(f"Mined Congruences Mod {hunt_M}", " \\\\\n".join(lat_strs))
                    
        except Exception as e: st.error(f"Failed: {e}")

# ==========================================
# --- MODULE 3: EULER PRODUCT EXPLORER ---
# ==========================================
def run_euler_explorer():
    st.title("🌀 Universal Euler Product Explorer")

    with st.sidebar:
        st.header("⚙️ 1. Series Definition")
        latex_input = st.text_area("Enter LaTeX Formula:", value=r"\frac{f_2^5}{f_1^2 f_3^2}")
        st.header("🔍 2. Search Parameters")
        max_degree = st.number_input("Max Degree (q-expansion)", value=200, step=50)
        progression = st.number_input("Base Progression (m)", value=2)
        offset = st.number_input("Offset (r)", value=0)
        
        st.markdown("### Memory / Caching")
        cache_mode = st.radio("Save Computations:", ["Temporarily (RAM)", "Permanently (Disk)"], key="euler_cache")
        run_btn = st.button("🚀 Calculate Exponents", type="primary", use_container_width=True)

    if run_btn:
        try:
            if cache_mode.startswith("Temporarily"):
                G_coeffs = get_smart_expansion(latex_input, max_degree, persist_to_disk=False)
            else:
                G_coeffs = get_smart_expansion(latex_input, max_degree, persist_to_disk=True)
            
            H_coeffs_raw = [G_coeffs[i] for i in range(offset, max_degree + 1, progression)]
            first_term = Fraction(H_coeffs_raw[0])
            if first_term == 0:
                raise ValueError("The extracted progression has zero constant term, so it cannot be normalized as an Euler product without first removing its initial q-power.")
            H_coeffs = [Fraction(c) / first_term for c in H_coeffs_raw]
            a_exponents = compute_euler_exponents(H_coeffs, len(H_coeffs) - 1)

            is_clean = all(isinstance(val, int) for val in a_exponents[1:])
            
            if is_clean:
                seq = a_exponents[1:]
                seq_len = len(seq)
                best_stride, best_coverage, best_components = 1, 0, {}
                for stride in range(1, 13):
                    components, covered_indices = {}, 0
                    for r in range(1, stride + 1):
                        sub_seq = [seq[i] for i in range(r - 1, seq_len, stride)]
                        if len(sub_seq) < 3: components[r] = {"is_periodic": False}; continue
                        detected_p = None
                        for p in range(1, min(20, len(sub_seq) // 3 + 1)):
                            is_p = True
                            for i in range(len(sub_seq)):
                                if abs(sub_seq[i] - sub_seq[i % p]) > 1e-4: is_p = False; break
                            if is_p: detected_p = p; break
                        if detected_p is not None:
                            components[r] = {"is_periodic": True, "p": detected_p, "pattern": [int(x) for x in sub_seq[:detected_p]]}
                            covered_indices += len(sub_seq)
                        else: components[r] = {"is_periodic": False}
                    if covered_indices > best_coverage:
                        best_coverage, best_stride, best_components = covered_indices, stride, components
                    if covered_indices == seq_len: break

                if best_coverage > 0:
                    num_str, den_str, unknown_r = [], [], []
                    for r in range(1, best_stride + 1):
                        comp = best_components[r]
                        if comp["is_periodic"]:
                            p, pattern = comp["p"], comp["pattern"]
                            for j in range(p):
                                a_val = pattern[j]
                                if a_val == 0: continue
                                base_power, step_power = r + j * best_stride, best_stride * p
                                r_str = "q" if base_power == 1 else f"q^{{{base_power}}}"
                                P_str = "q" if step_power == 1 else f"q^{{{step_power}}}"
                                term = rf"({r_str}; {P_str})_\infty"
                                if a_val < 0:
                                    if abs(a_val) == 1: num_str.append(term)
                                    else: num_str.append(term + rf"^{{{abs(a_val)}}}")
                                elif a_val > 0:
                                    if a_val == 1: den_str.append(term)
                                    else: den_str.append(term + rf"^{{{a_val}}}")
                        else: unknown_r.append(r)
                            
                    num_final = " ".join(num_str) if num_str else "1"
                    den_final = " ".join(den_str) if den_str else "1"
                    unknown_str = r" \times F_{\text{unknown}}(q)" if unknown_r else ""
                        
                    if den_final == "1": final_latex = rf"\sum c({progression}n+{offset})q^n = {num_final}{unknown_str}"
                    elif num_final == "1": final_latex = rf"\sum c({progression}n+{offset})q^n = \frac{{1}}{{{den_final}}}{unknown_str}"
                    else: final_latex = rf"\sum c({progression}n+{offset})q^n = \frac{{{num_final}}}{{{den_final}}}{unknown_str}"
                        
                    st.success("### Extracted Product Equation")
                    st.latex(final_latex)
                    add_to_clipboard(f"Euler Product ({progression}n+{offset})", final_latex)
                    
        except Exception as e: st.error(f"Failed to evaluate expression: {e}")

# ==========================================
# --- MODULE 4: ETA-MULTIPLIER PRO ---
# ==========================================
def run_eta_multiplier():
    st.title("🛡️ Correct Eta-Quotient & Multiplier Lab")
    st.markdown(
        "This module applies the Newman/Gordon–Hughes modularity conditions and "
        "Ligozat cusp orders. It searches for a pole-clearing eta multiplier; it is not "
        "a substitute for the separate Radu progression algorithm. The certificate implemented here is for integral-weight eta quotients."
    )

    with st.sidebar:
        st.header("1. Base f-product")
        latex_input = st.text_area("F(q)", value=r"\frac{1}{f_1 f_2^{36}}", height=90, key="eta_input")
        st.latex(latex_input)
        auto_level = st.checkbox("Automatically raise level to contain all subscripts", value=True)
        requested_N = st.number_input("Requested level N", min_value=1, value=4, step=1)
        st.divider()
        st.header("2. Multiplier search")
        search_all = st.checkbox("Use every divisor of N", value=True)
        targeted = []
        if not search_all:
            targeted = st.multiselect("Allowed multiplier subscripts", get_divisors(int(requested_N)), default=[1])
        c1, c2 = st.columns(2)
        min_e = c1.number_input("Minimum exponent", value=0, step=1)
        max_e = c2.number_input("Maximum exponent", value=24, step=1)
        target_weight_on = st.checkbox("Fix target weight")
        target_k = st.number_input("Target weight", value=12, min_value=1, step=1, disabled=not target_weight_on)
        c3, c4 = st.columns(2)
        max_results = c3.number_input("Maximum results", value=20, min_value=1, max_value=200)
        max_sturm = c4.number_input("Maximum Sturm bound", value=500, min_value=1)
        max_combinations = st.number_input("Maximum search combinations", value=250000, min_value=1000, step=10000)
        run_btn = st.button("Run rigorous eta analysis", type="primary", use_container_width=True)

    if not run_btn:
        return
    try:
        base = parse_eta_product(latex_input)
        support_lcm = lcm_list(list(base)) if base else 1
        N = lcm(int(requested_N), support_lcm) if auto_level else int(requested_N)
        if N != requested_N:
            st.info(f"The level was raised from {requested_N} to {N}, the least common multiple with all f-subscripts.")

        base_analysis = analyze_eta_quotient(base, N)
        tabs = st.tabs(["Base diagnosis", "Valid multipliers"])
        with tabs[0]:
            st.latex(rf"F(q)=q^{{-{format_latex_frac(base_analysis['q_shift'])}}}\,{eta_product_latex(base, 'eta')}")
            rows = [
                ["Weight", str(base_analysis["weight"])],
                [r"Σ δrδ", f"{base_analysis['sum_T']}  (mod 24 = {base_analysis['sum_T']%24})"],
                [r"Σ (N/δ)rδ", f"{base_analysis['sum_S']}  (mod 24 = {base_analysis['sum_S']%24})"],
                ["Integral weight", base_analysis["integral_weight"]],
                ["Newman modularity", base_analysis["modular"]],
                ["Holomorphic at every cusp", base_analysis["holomorphic"]],
            ]
            st.dataframe(pd.DataFrame(rows, columns=["Test", "Value"]), use_container_width=True, hide_index=True)
            cusp_rows = []
            for c, order in base_analysis["orders"].items():
                label = f"c={c} (1/{c})" + (" ≃ ∞" if c == N else "")
                cusp_rows.append([label, str(order), order >= 0])
            st.dataframe(pd.DataFrame(cusp_rows, columns=["Cusp denominator", "Order", "Holomorphic"]), use_container_width=True, hide_index=True)

        allowed = None if search_all else targeted
        with st.spinner("Checking exact modularity conditions and cusp orders..."):
            results, checked, truncated = find_eta_multipliers(
                N, tuple(base.items()), int(min_e), int(max_e),
                int(target_k) if target_weight_on else None,
                tuple(allowed) if allowed else None,
                int(max_results), int(max_sturm), int(max_combinations)
            )
        with tabs[1]:
            st.caption(f"Checked {checked:,} exponent vectors." + (" Search cap reached." if truncated else ""))
            if not results:
                st.warning("No multiplier satisfying all integral-weight, mod-24, and cusp-holomorphy conditions was found in this box.")
                return
            st.success(f"Found {len(results)} rigorously valid candidate(s).")
            for i, item in enumerate(results, 1):
                with st.expander(f"Candidate {i}: weight {item['weight']}, Sturm bound {item['sturm']}", expanded=i == 1):
                    st.latex(rf"M(q)={eta_product_latex(item['multiplier'], 'f')}")
                    st.latex(rf"q^{{{format_latex_frac(item['q_shift'])}}}F(q)M(q)={eta_product_latex(item['total'], 'eta')}")
                    st.write(f"Newman sums: {item['sum_T']} and {item['sum_S']} (both divisible by 24).")
                    st.write(rf"Nebentypus candidate: $\chi(d)=\left(\frac{{{item['character_D']}}}{{d}}\right)$.")
                    cusp_df = pd.DataFrame([
                        {"c": c, "cusp": "∞" if c == N else f"1/{c}", "order": str(v)}
                        for c, v in item["orders"].items()
                    ])
                    st.dataframe(cusp_df, use_container_width=True, hide_index=True)
                    export = generate_latex_export(base, item)
                    st.code(export, language="latex")
                    if st.button("Add certificate to LaTeX clipboard", key=f"eta_cert_{i}"):
                        add_to_clipboard(f"Eta certificate {i}", export)
                        st.toast("Certificate added.")
    except Exception as exc:
        st.error(f"Eta analysis failed: {exc}")

# ==========================================
# --- MODULE 5: VERIFIED DISSECTION ENGINE ---
# ==========================================
def get_sym_env():
    def f(n):
        return SymExpr([SymTerm(1, 0, {int(n): 1})])
    def R(k):
        return SymExpr([SymTerm(1, 0, {}, {("R", int(k)): 1})])
    q_obj = SymExpr([SymTerm(1, 1)])
    return {"f": f, "R": R, "q": q_obj, "X": 1, "__builtins__": {}}


def load_dissections():
    common2 = "Baruah–Das / Hirschhorn; coefficient-verified in app"
    common3 = "Baruah–Das and standard theta dissections; coefficient-verified in app"
    rr5 = "Ramanujan 5-dissection with R(q)=(q,q^4;q^5)_∞/(q^2,q^3;q^5)_∞"
    return [
        {"p":2,"name":"f_1^2","nice_name":"f₁²","latex_lhs":r"f_1^2","latex_rhs":r"\frac{f_2 f_8^5}{f_4^2 f_{16}^2}-2q\frac{f_2 f_{16}^2}{f_8}","source":common2},
        {"p":2,"name":"1/f_1^2","nice_name":"1/f₁²","latex_lhs":r"\frac{1}{f_1^2}","latex_rhs":r"\frac{f_8^5}{f_2^5 f_{16}^2}+2q\frac{f_4^2 f_{16}^2}{f_2^5 f_8}","source":common2},
        {"p":2,"name":"f_1^4","nice_name":"f₁⁴","latex_lhs":r"f_1^4","latex_rhs":r"\frac{f_4^{10}}{f_2^2 f_8^4}-4q\frac{f_2^2 f_8^4}{f_4^2}","source":common2},
        {"p":2,"name":"1/f_1^4","nice_name":"1/f₁⁴","latex_lhs":r"\frac{1}{f_1^4}","latex_rhs":r"\frac{f_4^{14}}{f_2^{14} f_8^4}+4q\frac{f_4^2 f_8^4}{f_2^{10}}","source":common2},
        {"p":2,"name":"f_1 f_3","nice_name":"f₁f₃","latex_lhs":r"f_1f_3","latex_rhs":r"\frac{f_2 f_8^2 f_{12}^4}{f_4^2 f_6 f_{24}^2}-q\frac{f_4^4 f_6 f_{24}^2}{f_2 f_8^2 f_{12}^2}","source":common2},
        {"p":2,"name":"1/(f_1 f_3)","nice_name":"1/(f₁f₃)","latex_lhs":r"\frac{1}{f_1f_3}","latex_rhs":r"\frac{f_8^2 f_{12}^5}{f_2^2 f_4 f_6^4 f_{24}^2}+q\frac{f_4^5 f_{24}^2}{f_2^4 f_6^2 f_8^2 f_{12}}","source":common2},
        {"p":2,"name":"f_3/f_1^3","nice_name":"f₃/f₁³","latex_lhs":r"\frac{f_3}{f_1^3}","latex_rhs":r"\frac{f_4^6 f_6^3}{f_2^9 f_{12}^2}+3q\frac{f_4^2 f_6 f_{12}^2}{f_2^7}","source":common2},
        {"p":2,"name":"f_3^3/f_1","nice_name":"f₃³/f₁","latex_lhs":r"\frac{f_3^3}{f_1}","latex_rhs":r"\frac{f_4^3 f_6^2}{f_2^2 f_{12}}+q\frac{f_{12}^3}{f_4}","source":common2},
        {"p":2,"name":"f_1/f_3","nice_name":"f₁/f₃","latex_lhs":r"\frac{f_1}{f_3}","latex_rhs":r"\frac{f_2 f_{16} f_{24}^2}{f_6^2 f_8 f_{48}}-q\frac{f_2 f_8^2 f_{12} f_{48}}{f_4 f_6^2 f_{16} f_{24}}","source":common2},
        {"p":2,"name":"f_3/f_1","nice_name":"f₃/f₁","latex_lhs":r"\frac{f_3}{f_1}","latex_rhs":r"\frac{f_4 f_6 f_{16} f_{24}^2}{f_2^2 f_8 f_{12} f_{48}}+q\frac{f_6 f_8^2 f_{48}}{f_2^2 f_{16} f_{24}}","source":common2},
        {"p":2,"name":"f_1^2/f_3^2","nice_name":"f₁²/f₃²","latex_lhs":r"\frac{f_1^2}{f_3^2}","latex_rhs":r"\frac{f_2 f_4^2 f_{12}^4}{f_6^5 f_8 f_{24}}-2q\frac{f_2^2 f_8 f_{12} f_{24}}{f_4 f_6^4}","source":common2},
        {"p":2,"name":"f_1/f_5","nice_name":"f₁/f₅","latex_lhs":r"\frac{f_1}{f_5}","latex_rhs":r"\frac{f_2 f_8 f_{20}^3}{f_4 f_{10}^3 f_{40}}-q\frac{f_4^2 f_{40}}{f_8 f_{10}^2}","source":common2},
        {"p":2,"name":"f_5/f_1","nice_name":"f₅/f₁","latex_lhs":r"\frac{f_5}{f_1}","latex_rhs":r"\frac{f_8 f_{20}^2}{f_2^2 f_{40}}+q\frac{f_4^3 f_{10} f_{40}}{f_2^3 f_8 f_{20}}","source":common2},
        {"p":3,"name":"f_1^2/f_2","nice_name":"f₁²/f₂","latex_lhs":r"\frac{f_1^2}{f_2}","latex_rhs":r"\frac{f_9^2}{f_{18}}-2q\frac{f_3 f_{18}^2}{f_6 f_9}","source":common3},
        {"p":3,"name":"f_2/f_1^2","nice_name":"f₂/f₁²","latex_lhs":r"\frac{f_2}{f_1^2}","latex_rhs":r"\frac{f_6^4 f_9^6}{f_3^8 f_{18}^3}+2q\frac{f_6^3 f_9^3}{f_3^7}+4q^2\frac{f_6^2 f_{18}^3}{f_3^6}","source":common3},
        {"p":3,"name":"f_1 f_4/f_2","nice_name":"f₁f₄/f₂","latex_lhs":r"\frac{f_1f_4}{f_2}","latex_rhs":r"\frac{f_3 f_{12} f_{18}^5}{f_6^2 f_9^2 f_{36}^2}-q\frac{f_9 f_{36}}{f_{18}}","source":common3},
        {"p":3,"name":"f_2/(f_1 f_4)","nice_name":"f₂/(f₁f₄)","latex_lhs":r"\frac{f_2}{f_1f_4}","latex_rhs":r"\frac{f_{18}^9}{f_3^2 f_9^3 f_{12}^2 f_{36}^3}+q\frac{f_6^2 f_{18}^3}{f_3^3 f_{12}^3}+q^2\frac{f_6^4 f_9^3 f_{36}^3}{f_3^4 f_{12}^4 f_{18}^3}","source":common3},
        {"p":3,"name":"f_1^3","nice_name":"f₁³","latex_lhs":r"f_1^3","latex_rhs":r"\frac{f_6 f_9^6}{f_3 f_{18}^3}-3qf_9^3+4q^3\frac{f_3^2 f_{18}^6}{f_6^2 f_9^3}","source":common3},
        {"p":3,"name":"f_1 f_2","nice_name":"f₁f₂","latex_lhs":r"f_1f_2","latex_rhs":r"\frac{f_6 f_9^4}{f_3 f_{18}^2}-qf_9f_{18}-2q^2\frac{f_3 f_{18}^4}{f_6 f_9^2}","source":common3},
        {"p":3,"name":"f_2^2/f_1","nice_name":"f₂²/f₁","latex_lhs":r"\frac{f_2^2}{f_1}","latex_rhs":r"\frac{f_6 f_9^2}{f_3 f_{18}}+q\frac{f_{18}^2}{f_9}","source":"Jacobi triple product; uploaded three-core note; coefficient-verified"},
        {"p":5,"name":"f_1","nice_name":"f₁ via R","latex_lhs":r"f_1","latex_rhs":r"f_{25}\left(\frac{1}{R(q^5)}-q-q^2R(q^5)\right)","source":rr5},
        {"p":5,"name":"1/f_1","nice_name":"1/f₁ via R","latex_lhs":r"\frac{1}{f_1}","latex_rhs":r"\frac{f_{25}^5}{f_5^6}\left(\frac{1}{R(q^5)^4}+\frac{q}{R(q^5)^3}+\frac{2q^2}{R(q^5)^2}+\frac{3q^3}{R(q^5)}+5q^4-3q^5R(q^5)+2q^6R(q^5)^2-q^7R(q^5)^3+q^8R(q^5)^4\right)","source":"Ramanujan reciprocal 5-dissection; uploaded DSOME note; coefficient-verified"},
    ]


def symexpr_to_qseries(expr, limit):
    q_series = QSeries([0, 1], limit)
    cache_f, cache_R = {}, {}
    total = QSeries.zero(limit)
    for term in expr.terms:
        if term.q_power < 0:
            raise ValueError("Negative explicit q-powers are not supported in a power-series verification.")
        series = QSeries.one(limit)*term.coeff
        if term.q_power:
            series = series*(q_series**term.q_power)
        for k, exponent in term.etas.items():
            cache_f.setdefault(k, QSeries(generate_base_pochhammer(k, limit), limit))
            series = series*(cache_f[k]**exponent)
        for (name, k), exponent in term.specials.items():
            if name != "R":
                raise ValueError(f"Unknown special factor {name}.")
            cache_R.setdefault(k, gen_R(k, limit))
            series = series*(cache_R[k]**exponent)
        total = total+series
    return total


def verify_dissection_identity(item, limit=90):
    try:
        lhs = _core_expansion_engine(item["latex_lhs"], limit)
        rhs = _core_expansion_engine(item["latex_rhs"], limit)
        mismatch = next((n for n, (a, b) in enumerate(zip(lhs, rhs)) if a != b), None)
        return {"verified": mismatch is None, "mismatch": mismatch, "limit": limit}
    except Exception as exc:
        return {"verified": False, "mismatch": None, "limit": limit, "error": str(exc)}


def verified_dissection_database(limit=90):
    db = load_dissections()
    for item in db:
        item.update(verify_dissection_identity(item, limit))
    return db


def scaled_vector(vector, scale):
    return {k*scale: v for k, v in vector.items()}


def vector_subtract(a, b, multiple=1):
    result = dict(a)
    for k, v in b.items():
        result[k] = result.get(k, 0)-multiple*v
        if not result[k]:
            result.pop(k)
    return result


def sign_compatible(candidate, remaining, p):
    active = False
    for k, v in candidate.items():
        if k % p == 0:
            continue
        active = True
        rem = remaining.get(k, 0)
        if rem == 0 or (rem > 0) != (v > 0) or abs(v) > abs(rem):
            return False
    return active


def find_dissection_plans(target, p, db, max_scale=30, max_identity_power=8,
                           max_terms=1500, max_plans=5):
    candidates = []
    max_index = max(target, default=1)
    env = get_sym_env()
    for item in db:
        if item["p"] != p or not item.get("verified"):
            continue
        lhs = parse_eta_product(item["latex_lhs"])
        rhs = restricted_eval(latex_to_python(item["latex_rhs"]), env)
        minimum = min(lhs)
        upper = min(max_scale, max(1, max_index//minimum + 1))
        for scale in range(1, upper+1):
            vector = scaled_vector(lhs, scale)
            if not any(k % p and target.get(k, 0) for k in vector):
                continue
            candidates.append({"item": item, "scale": scale, "vector": vector,
                               "rhs": rhs.substitute_q(scale), "branches": max(1, rhs.term_count)})

    plans = []
    memo = set()

    def dfs(remaining, chosen, term_estimate):
        active = tuple(sorted((k, v) for k, v in remaining.items() if k % p and v))
        if not active:
            plans.append({"chosen": list(chosen), "residual": remaining, "term_estimate": term_estimate})
            return len(plans) >= max_plans
        state = (active, tuple((c[0], c[1]) for c in chosen), term_estimate)
        if state in memo:
            return False
        memo.add(state)
        coordinate = min(active, key=lambda kv: abs(kv[1]))[0]
        options = [c for c in candidates if c["vector"].get(coordinate) and sign_compatible(c["vector"], remaining, p)]
        options.sort(key=lambda c: (c["branches"], sum(abs(v) for k, v in c["vector"].items() if k % p)))
        for candidate in options:
            rem = remaining
            for count in range(1, max_identity_power+1):
                if not sign_compatible(candidate["vector"], rem, p):
                    break
                new_estimate = term_estimate*(candidate["branches"]**count)
                if new_estimate > max_terms:
                    break
                rem = vector_subtract(rem, candidate["vector"], 1)
                chosen.append((candidates.index(candidate), count))
                if dfs(rem, chosen, new_estimate):
                    return True
                chosen.pop()
        return False

    # The repeated-choice bookkeeping above stores cumulative count entries; normalize after search.
    dfs(dict(target), [], 1)
    normalized = []
    for plan in plans:
        counts = {}
        for idx, count in plan["chosen"]:
            counts[idx] = counts.get(idx, 0)+count
        normalized.append({"factors": [(candidates[idx], count) for idx, count in counts.items()],
                           "residual": plan["residual"], "term_estimate": plan["term_estimate"]})
    normalized.sort(key=lambda pl: (pl["term_estimate"], len(pl["factors"])))
    return normalized


def build_dissection_expression(plan):
    env = get_sym_env()
    residual = SymExpr([SymTerm(1, 0, plan["residual"])])
    expression = residual
    lhs_parts = []
    for candidate, count in plan["factors"]:
        expression = expression*(candidate["rhs"]**count)
        lhs = scale_latex_lhs(candidate["item"]["latex_lhs"], candidate["scale"])
        lhs_parts.append(rf"\left({lhs}\right)^{{{count}}}" if count != 1 else rf"\left({lhs}\right)")
    return expression, lhs_parts


def format_truncated_component(coeffs, max_display=14):
    pieces = []
    for n, coefficient in enumerate(coeffs):
        if coefficient == 0:
            continue
        c = int(coefficient) if isinstance(coefficient, Fraction) and coefficient.denominator == 1 else coefficient
        if n == 0:
            pieces.append(str(c))
        else:
            qpart = "q" if n == 1 else f"q^{{{n}}}"
            if c == 1:
                pieces.append(qpart)
            elif c == -1:
                pieces.append("-"+qpart)
            else:
                pieces.append(f"{c}{qpart}")
        if len(pieces) >= max_display:
            break
    if not pieces:
        return "0"
    return " + ".join(pieces).replace("+ -", "- ")



def format_exact_number(value):
    value = value if isinstance(value, Fraction) else Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return rf"\frac{{{value.numerator}}}{{{value.denominator}}}"


def dissection_library_latex(items):
    lines = []
    for item in items:
        status = "verified" if item.get("verified") else "not verified"
        lines.append(
            rf"% {item['p']}-dissection; {status} through q^{{{item.get('limit', '?')}}}; {item['source']}\n"
            rf"{item['latex_lhs']} &= {item['latex_rhs']}"
        )
    return "\\begin{aligned}\n" + " \\\\\n".join(lines) + "\n\\end{aligned}"


def component_equation_latex(p, r, rhs):
    return rf"\sum_{{n\ge 0}}a({p}n+{r})q^n={rhs}"


def _parenthesize_latex(value):
    value = str(value).strip()
    if value in {"", "1"}:
        return "1"
    return rf"\left({value}\right)"


def _product_latex(factors):
    clean = [str(f).strip() for f in factors if str(f).strip() not in {"", "1"}]
    return r"\,".join(clean) if clean else "1"


def _power_latex(base, exponent):
    base = str(base).strip()
    exponent = int(exponent)
    if exponent == 1:
        return _parenthesize_latex(base)
    return rf"\left({base}\right)^{{{exponent}}}"


def _term_prefactor_expression(term):
    return SymExpr([SymTerm(term.coeff, term.q_power, {}, term.specials)])


def _plan_residual_expression(plan):
    return SymExpr([SymTerm(1, 0, plan.get("residual", {}))])


def _identity_trace_record(candidate, count):
    item = candidate["item"]
    scale = int(candidate["scale"])
    return {
        "name": item.get("nice_name", item.get("name", "identity")),
        "source": item.get("source", "Stored verified identity"),
        "count": int(count),
        "scale": scale,
        "base_lhs": item["latex_lhs"],
        "base_rhs": item["latex_rhs"],
        "scaled_lhs": scale_latex_lhs(item["latex_lhs"], scale),
        "scaled_rhs": candidate["rhs"].to_latex(),
        "verified_through": item.get("limit"),
    }


def build_term_derivation_record(row, term_index):
    term_expr = SymExpr([row["term"]])
    prefactor = _term_prefactor_expression(row["term"])
    residual = _plan_residual_expression(row["plan"])
    identities = [_identity_trace_record(candidate, count) for candidate, count in row["plan"]["factors"]]

    factorized_factors = []
    substituted_factors = []
    prefactor_latex = prefactor.to_latex()
    residual_latex = residual.to_latex()
    if prefactor_latex != "1":
        factorized_factors.append(_parenthesize_latex(prefactor_latex))
        substituted_factors.append(_parenthesize_latex(prefactor_latex))
    if residual_latex != "1":
        factorized_factors.append(_parenthesize_latex(residual_latex))
        substituted_factors.append(_parenthesize_latex(residual_latex))
    for identity in identities:
        factorized_factors.append(_power_latex(identity["scaled_lhs"], identity["count"]))
        substituted_factors.append(_power_latex(identity["scaled_rhs"], identity["count"]))

    return {
        "index": int(term_index),
        "input": term_expr.to_latex(),
        "prefactor": prefactor_latex,
        "residual": residual_latex,
        "identities": identities,
        "factorized": _product_latex(factorized_factors),
        "substituted": _product_latex(substituted_factors),
        "result": row["result"].to_latex(),
    }


def build_exact_derivation_data(input_expr, exact, p):
    if not exact.get("success"):
        return None
    p = int(p)
    terms = [build_term_derivation_record(row, i) for i, row in enumerate(exact["certificate"], 1)]
    component_rows = []
    for r in range(p):
        component = exact["components"][r]
        component_rows.append({
            "r": r,
            "function": component.to_latex(),
            "equation": component_equation_latex(p, r, component.to_latex()),
        })
    return {
        "p": p,
        "input": input_expr.to_latex(),
        "terms": terms,
        "combined": exact["expression"].to_latex(),
        "components": component_rows,
        "verified_through": exact.get("verified_through"),
    }


def exact_derivation_latex(input_expr, exact, p, heading="Step-by-step dissection derivation"):
    data = build_exact_derivation_data(input_expr, exact, p)
    if data is None:
        return "% No exact derivation was available."

    rowbreak = r"\\" + "\n"

    def aligned(rows):
        return "\\[\n\\begin{aligned}\n" + rowbreak.join(rows) + "\n\\end{aligned}\n\\]"

    lines = [
        rf"\subsection*{{{heading}}}",
        "Let",
        rf"\[F(q)={data['input']}=\sum_{{n\ge0}}a(n)q^n.\]",
        rf"We construct the {data['p']}-dissection term by term. Every identity below is taken from the verified identity library.",
    ]

    for term in data["terms"]:
        lines.append(rf"\paragraph{{Term {term['index']}.}}")
        lines.append(rf"Start with \[T_{{{term['index']}}}(q)={term['input']}.\]")
        lines.append(rf"Separate the factors already depending only on $q^{{{data['p']}}}$ and factor the remaining eta quotient as")
        lines.append(aligned([rf"T_{{{term['index']}}}(q)&={term['factorized']}."]))

        for j, identity in enumerate(term["identities"], 1):
            lines.append(rf"\medskip\noindent\textbf{{Identity {term['index']}.{j}.}}")
            lines.append(rf"% Source: {identity['source']}")
            identity_rows = [rf"{identity['base_lhs']}&={identity['base_rhs']}"]
            if identity["scale"] != 1:
                identity_rows.append(
                    rf"{identity['scaled_lhs']}&={identity['scaled_rhs']}\qquad(q\mapsto q^{{{identity['scale']}}})"
                )
            lines.append(aligned(identity_rows))
            if identity["count"] != 1:
                lines.append(rf"This identity is used to the power ${identity['count']}$." )

        lines.append("Substituting these identities and simplifying gives")
        lines.append(aligned([
            rf"T_{{{term['index']}}}(q)&={term['substituted']}",
            rf"&={term['result']}.",
        ]))

    sum_terms = "+".join(rf"T_{{{term['index']}}}(q)" for term in data["terms"])
    lines.extend([
        r"\paragraph{Recombination.}",
        aligned([
            rf"F(q)&={sum_terms}",
            rf"&={data['combined']}.",
        ]),
        r"Now collect terms according to their exponent modulo $p$. Write",
        rf"\[F(q)=\sum_{{r=0}}^{{{data['p']-1}}}q^rF_r(q^{{{data['p']}}}).\]",
    ])
    for component in data["components"]:
        lines.append(rf"\[F_{{{component['r']}}}(q)={component['function']}.\]")
    lines.append(r"Therefore, retain the powers $q^{pn+r}$, divide by $q^r$, and replace $q^p$ by $q$. This yields")
    lines.append(aligned([row["equation"].replace("=", "&=", 1) for row in data["components"]]))
    if data["verified_through"] is not None:
        lines.append(rf"The final identity was independently coefficient-checked through $q^{{{data['verified_through']}}}$." )
    return "\n\n".join(lines)

def render_exact_derivation_path(input_expr, exact, p, key_prefix, show_export=True):
    data = build_exact_derivation_data(input_expr, exact, p)
    if data is None:
        st.info("No exact derivation path is available because no exact symbolic dissection was completed.")
        return None

    identity_count = sum(len(term["identities"]) for term in data["terms"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Input terms", len(data["terms"]))
    m2.metric("Identity substitutions", identity_count)
    m3.metric("Coefficient audit", f"q^{data['verified_through']}" if data["verified_through"] is not None else "—")
    st.markdown(
        '<span class="proof-badge">Exact symbolic path</span>'
        '<span class="proof-badge">Verified identity library</span>'
        '<span class="proof-badge">Independent coefficient audit</span>',
        unsafe_allow_html=True,
    )

    for term in data["terms"]:
        with st.expander(f"Term {term['index']}: show the complete substitution path", expanded=(term["index"] == 1)):
            st.markdown('<div class="derivation-step"><strong>Step A — Isolate the term.</strong><br>Separate the scalar, explicit power of q, and factors already depending only on qᵖ.</div>', unsafe_allow_html=True)
            st.latex(rf"T_{{{term['index']}}}(q)={term['input']}")
            st.latex(rf"T_{{{term['index']}}}(q)={term['factorized']}")

            st.markdown('<div class="derivation-step"><strong>Step B — Apply the verified identities.</strong><br>The base identity and the scaled version actually used are both shown.</div>', unsafe_allow_html=True)
            for j, identity in enumerate(term["identities"], 1):
                st.markdown(f"**Identity {term['index']}.{j}: {identity['name']}**")
                left, right = st.columns(2)
                with left:
                    st.caption("Stored identity")
                    st.latex(rf"{identity['base_lhs']}={identity['base_rhs']}")
                with right:
                    st.caption("Identity used in this calculation")
                    st.latex(rf"{identity['scaled_lhs']}={identity['scaled_rhs']}")
                scale_text = "without scaling" if identity["scale"] == 1 else rf"after replacing q by q^{identity['scale']}"
                power_text = "once" if identity["count"] == 1 else f"to the power {identity['count']}"
                st.markdown(
                    f'<div class="identity-note">Used {scale_text}, {power_text}. Source: {identity["source"]}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="derivation-step"><strong>Step C — Substitute and simplify.</strong><br>Replace every selected left-hand side by its verified right-hand side and expand algebraically.</div>', unsafe_allow_html=True)
            st.latex(rf"T_{{{term['index']}}}(q)={term['substituted']}")
            st.latex(rf"T_{{{term['index']}}}(q)={term['result']}")

    st.markdown("### Recombine the transformed terms")
    st.latex(rf"F(q)={data['combined']}")
    st.markdown("### Separate the residue classes")
    st.latex(rf"F(q)=\sum_{{r=0}}^{{{data['p']-1}}}q^rF_r(q^{{{data['p']}}})")
    for component in data["components"]:
        st.latex(rf"F_{{{component['r']}}}(q)={component['function']}")
        st.latex(component["equation"])
    st.info(r"Extraction rule: retain q^{pn+r}, divide by q^r, and replace q^p by q.")

    latex_code = exact_derivation_latex(input_expr, exact, p)
    if show_export:
        render_latex_export(
            "Complete step-by-step LaTeX derivation",
            latex_code,
            key=f"{key_prefix}_derivation",
            filename=f"{safe_widget_key(key_prefix).lower()}_step_by_step_derivation.tex",
        )
    return latex_code


def deep_derivation_latex(initial_expr, p, residue, deep):
    if not deep.get("success"):
        return "% No exact deep-extraction derivation was available."
    p = int(p)
    digits = base_p_digits(int(residue), p, len(deep["records"]))
    rowbreak = r"\\" + "\n"

    def aligned(rows):
        return "\\[\n\\begin{aligned}\n" + rowbreak.join(rows) + "\n\\end{aligned}\n\\]"

    lines = [
        r"\subsection*{Step-by-step iterated residue extraction}",
        rf"Set $A_0(q)={initial_expr.to_latex()}$.",
        rf"The residue ${residue}$ has least-significant-first base-${p}$ digits $({', '.join(map(str, digits))})$.",
    ]
    current = initial_expr
    current_residue = 0
    modulus = 1
    for level, record in enumerate(deep["records"], 1):
        digit = int(record["digit"])
        lines.append(rf"\subsubsection*{{Level {level}: extract residue {digit} modulo {p}}}")
        lines.append(exact_derivation_latex(current, record["dissection"], p, heading=f"Level {level} dissection"))
        current_residue += modulus * digit
        modulus *= p
        next_expr = record["expression"].to_latex()
        lines.append(rf"Write $A_{{{level-1}}}(q)=\sum_{{n\ge0}}b_{{{level-1}}}(n)q^n$. Then")
        lines.append(aligned([
            rf"A_{{{level}}}(q)&=\sum_{{n\ge0}}b_{{{level-1}}}({p}n+{digit})q^n",
            rf"&={next_expr}.",
        ]))
        lines.append(rf"Thus $A_{{{level}}}(q)=\sum_{{n\ge0}}a({modulus}n+{current_residue})q^n$.")
        current = record["expression"]
    return "\n\n".join(lines)

def render_deep_derivation_path(initial_expr, p, residue, deep, key_prefix):
    if not deep.get("success"):
        st.info("The exact iteration stopped before a complete deep derivation could be produced.")
        return None
    p = int(p)
    current = initial_expr
    current_residue = 0
    modulus = 1
    digits = base_p_digits(int(residue), p, len(deep["records"]))
    st.markdown(f"Base-{p} extraction digits, used from first to last: **{digits}**")
    for level, record in enumerate(deep["records"], 1):
        digit = int(record["digit"])
        current_residue += modulus * digit
        modulus *= p
        with st.expander(f"Level {level}: extract digit {digit}, producing a({modulus}n+{current_residue})", expanded=(level == 1)):
            st.markdown('<div class="derivation-step"><strong>Dissect the current generating function.</strong><br>Each eta monomial is replaced using verified scaled identities.</div>', unsafe_allow_html=True)
            st.latex(rf"A_{{{level-1}}}(q)={current.to_latex()}")
            for term_idx, row in enumerate(record["dissection"]["certificate"], 1):
                term_record = build_term_derivation_record(row, term_idx)
                st.markdown(f"**Term {term_idx} identities**")
                for identity in term_record["identities"]:
                    st.latex(rf"{identity['scaled_lhs']}={identity['scaled_rhs']}")
                    st.caption(f"{identity['name']} — {identity['source']}")
            st.markdown('<div class="derivation-step"><strong>Select the required residue.</strong><br>Keep the indicated q-exponents, divide by the residue power, and replace qᵖ by q.</div>', unsafe_allow_html=True)
            st.latex(rf"A_{{{level-1}}}(q)=\sum_{{n\ge0}}b_{{{level-1}}}(n)q^n")
            st.latex(rf"A_{{{level}}}(q)=\sum_{{n\ge0}}b_{{{level-1}}}({p}n+{digit})q^n={record['expression'].to_latex()}")
            st.success(f"This is the generating function for a({modulus}n+{current_residue}).")
        current = record["expression"]

    latex_code = deep_derivation_latex(initial_expr, p, residue, deep)
    render_latex_export(
        "Complete iterated-extraction LaTeX derivation",
        latex_code,
        key=f"{key_prefix}_deep_derivation",
        filename=f"{safe_widget_key(key_prefix).lower()}_deep_derivation.tex",
    )
    return latex_code


def coefficient_derivation_latex(input_expr, p, coeffs, max_display=14):
    p = int(p)
    degree = len(coeffs) - 1
    rows = []
    for r in range(p):
        component = coeffs[r::p]
        rows.append(truncated_component_latex(component, p, r, max_display=max_display))
    rowbreak = r"\\" + "\n"
    aligned = "\\[\n\\begin{aligned}\n" + rowbreak.join(
        row.replace("=", "&=", 1) for row in rows
    ) + "\n\\end{aligned}\n\\]"
    return "\n\n".join([
        r"\subsection*{Coefficient-based dissection path}",
        rf"Start with $F(q)={input_expr.to_latex()}=\sum_{{n\ge0}}a(n)q^n$ and compute its coefficients through $q^{{{degree}}}$.",
        rf"For each $r=0,1,\ldots,{p-1}$, retain the coefficients whose indices are congruent to $r$ modulo ${p}$:",
        rf"\[F_r(q)=\sum_{{n\ge0}}a({p}n+r)q^n.\]",
        aligned,
        rf"The truncated reconstruction is $F(q)=\sum_{{r=0}}^{{{p-1}}}q^rF_r(q^{{{p}}})+O(q^{{{degree+1}}})$.",
        r"This is a finite coefficient calculation, not an identity proof. No stored dissection identity was used.",
    ])


def render_coefficient_derivation_path(input_expr, p, coeffs, key_prefix):
    p = int(p)
    st.warning("No exact identity path was found within the selected limits. The path below explains the coefficient extraction that produced the truncated result.")
    st.markdown('<div class="derivation-step"><strong>Step A — Expand.</strong><br>Compute the q-series coefficients to the selected precision.</div>', unsafe_allow_html=True)
    st.latex(rf"F(q)={input_expr.to_latex()}=\sum_{{n\ge0}}a(n)q^n")
    st.markdown('<div class="derivation-step"><strong>Step B — Sort by residue.</strong><br>Place a(n) into the component determined by n modulo p.</div>', unsafe_allow_html=True)
    for r in range(p):
        st.latex(truncated_component_latex(coeffs[r::p], p, r))
    st.markdown('<div class="derivation-step"><strong>Step C — Reconstruct.</strong><br>Use F(q)=Σ qʳFᵣ(qᵖ) up to the computed precision.</div>', unsafe_allow_html=True)
    st.info("This route uses coefficient comparison only; it does not claim an exact closed-form proof.")
    code = coefficient_derivation_latex(input_expr, p, coeffs)
    render_latex_export(
        "Coefficient-path LaTeX",
        code,
        key=f"{key_prefix}_coefficient_path",
        filename=f"{safe_widget_key(key_prefix).lower()}_coefficient_path.tex",
    )
    return code


def parse_eta_linear_combination(latex_input):
    """Parse finite sums/differences of eta monomials into SymExpr."""
    obj = restricted_eval(latex_to_python(latex_input), get_sym_env())
    if isinstance(obj, SymTerm):
        obj = SymExpr([obj])
    elif isinstance(obj, (int, Fraction)):
        obj = SymExpr([SymTerm(obj)])
    if not isinstance(obj, SymExpr):
        raise ValueError("Enter a finite sum or difference of eta products/quotients.")
    if any(term.q_power < 0 for term in obj.terms):
        raise ValueError("Negative explicit powers of q are not supported.")
    return obj


def compare_symbolic_series(lhs, rhs, limit):
    left = symexpr_to_qseries(lhs, limit).coeffs
    right = symexpr_to_qseries(rhs, limit).coeffs
    mismatch = next((n for n, (a, b) in enumerate(zip(left, right)) if a != b), None)
    return mismatch


def dissect_symbolic_expression_once(expr, p, db, max_scale=30, max_power=8,
                                      max_terms=1500, verify_terms=100):
    """Dissect every eta monomial of a finite linear combination and recombine exactly."""
    total = SymExpr([SymTerm(0)])
    certificate = []
    for term_number, term in enumerate(expr.terms, 1):
        bad_specials = [(name, k) for (name, k) in term.specials if k % p]
        if bad_specials:
            return {
                "success": False,
                "reason": f"Term {term_number} contains a special factor not visibly depending on q^{p}: {bad_specials}.",
            }
        plans = find_dissection_plans(
            term.etas, p, db, int(max_scale), int(max_power), int(max_terms), 8
        )
        if not plans:
            return {
                "success": False,
                "reason": f"No verified {p}-dissection plan was found for term {term_number}: {SymExpr([term]).to_latex()}.",
            }

        accepted = None
        accepted_plan = None
        for plan in plans:
            try:
                expanded, _ = build_dissection_expression(plan)
                prefactor = SymExpr([SymTerm(term.coeff, term.q_power, {}, term.specials)])
                candidate = prefactor * expanded
                if candidate.term_count > max_terms:
                    continue
                if compare_symbolic_series(SymExpr([term]), candidate, int(verify_terms)) is None:
                    accepted = candidate
                    accepted_plan = plan
                    break
            except Exception:
                continue
        if accepted is None:
            return {
                "success": False,
                "reason": f"Candidate plans for term {term_number} failed the independent coefficient audit.",
            }
        total = total + accepted
        if total.term_count > max_terms:
            return {
                "success": False,
                "reason": f"The exact expression exceeded the selected limit of {max_terms} symbolic terms.",
            }
        certificate.append({"term": term, "plan": accepted_plan, "result": accepted})

    mismatch = compare_symbolic_series(expr, total, int(verify_terms))
    if mismatch is not None:
        return {"success": False, "reason": f"Whole-expression verification failed first at q^{mismatch}."}
    try:
        components = total.components(int(p))
    except Exception as exc:
        return {"success": False, "reason": f"The assembled result is not visibly separated by residues: {exc}"}
    return {
        "success": True,
        "expression": total,
        "components": components,
        "certificate": certificate,
        "verified_through": int(verify_terms),
    }


def q_log_product_exponents(coeffs, fit_limit):
    """Return e_n in F(q)=prod_{n>=1}(1-q^n)^{e_n}, using exact arithmetic."""
    fit_limit = min(int(fit_limit), len(coeffs) - 1)
    series = QSeries(coeffs[: fit_limit + 1], fit_limit)
    if series.coeffs[0] != 1:
        raise ValueError("The normalized series must have constant term 1.")
    q_derivative = QSeries([n * series.coeffs[n] for n in range(fit_limit + 1)], fit_limit)
    log_derivative = q_derivative * series.inv()
    product_exponents = [Fraction(0)] * (fit_limit + 1)
    for n in range(1, fit_limit + 1):
        weighted_previous = sum(
            d * product_exponents[d]
            for d in get_divisors(n)
            if d < n
        )
        product_exponents[n] = (-log_derivative.coeffs[n] - weighted_previous) / n
    return product_exponents


def recognize_f_product(component_coeffs, fit_limit=80, min_tail=12):
    """Find a finite f-product candidate by exact Euler-exponent inversion and verify it."""
    exact = [c if isinstance(c, Fraction) else Fraction(c) for c in component_coeffs]
    first = next((n for n, c in enumerate(exact) if c), None)
    if first is None:
        return {"success": True, "zero": True, "latex": "0", "verified_through": len(exact) - 1}
    leading = exact[first]
    normalized = [c / leading for c in exact[first:]]
    available = len(normalized) - 1
    if available < 12:
        return {"success": False, "reason": "Too few coefficients for product recognition."}
    fit_limit = min(int(fit_limit), available)
    try:
        cyclotomic = q_log_product_exponents(normalized, fit_limit)
    except Exception as exc:
        return {"success": False, "reason": str(exc)}
    if any(x.denominator != 1 for x in cyclotomic[1:]):
        return {"success": False, "reason": "Euler exponents are not integral."}

    f_exponents = [Fraction(0)] * (fit_limit + 1)
    for n in range(1, fit_limit + 1):
        f_exponents[n] = cyclotomic[n] - sum(
            f_exponents[d] for d in get_divisors(n) if d < n
        )
    if any(x.denominator != 1 for x in f_exponents[1:]):
        return {"success": False, "reason": "The inferred f-product exponents are not integral."}
    nonzero = [n for n in range(1, fit_limit + 1) if f_exponents[n]]
    last = max(nonzero, default=0)
    if last and fit_limit - last < min(int(min_tail), max(5, fit_limit // 5)):
        return {"success": False, "reason": "No stable zero tail in the inferred f-product exponents."}
    eta_map = {n: int(f_exponents[n]) for n in nonzero}
    candidate = SymExpr([SymTerm(leading, first, eta_map)])
    verification_limit = len(exact) - 1
    candidate_coeffs = symexpr_to_qseries(candidate, verification_limit).coeffs
    mismatch = next((n for n, (a, b) in enumerate(zip(candidate_coeffs, exact)) if a != b), None)
    if mismatch is not None:
        return {"success": False, "reason": f"Candidate fails at q^{mismatch}."}
    latex = candidate.to_latex()
    return {
        "success": True,
        "zero": False,
        "latex": latex,
        "expression": candidate,
        "f_exponents": eta_map,
        "verified_through": verification_limit,
        "leading_shift": first,
    }


def base_p_digits(residue, p, depth):
    digits = []
    value = int(residue)
    for _ in range(int(depth)):
        digits.append(value % int(p))
        value //= int(p)
    return digits


def progression_chain_latex(p, residue, depth):
    digits = base_p_digits(residue, p, depth)
    modulus, current = 1, 0
    labels = []
    for digit in digits:
        current += modulus * digit
        modulus *= p
        labels.append(rf"a({modulus}n+{current})")
    return r"\longrightarrow ".join(labels)


def deep_exact_extraction(expr, p, residue, depth, db, max_scale, max_power,
                          max_terms, verify_terms):
    current = expr
    records = []
    for level, digit in enumerate(base_p_digits(residue, p, depth), 1):
        dissected = dissect_symbolic_expression_once(
            current, p, db, max_scale, max_power, max_terms, verify_terms
        )
        if not dissected.get("success"):
            return {
                "success": False,
                "level": level,
                "reason": dissected.get("reason", "Unknown failure."),
                "records": records,
            }
        current = dissected["components"][digit]
        if current.term_count > max_terms:
            return {
                "success": False,
                "level": level,
                "reason": "The extracted expression became too large.",
                "records": records,
            }
        records.append({"level": level, "digit": digit, "expression": current, "dissection": dissected})
    return {"success": True, "expression": current, "records": records}


def truncated_component_latex(coeffs, modulus, residue, max_display=18):
    rhs = format_truncated_component(coeffs, max_display=max_display)
    return rf"\sum_{{n\ge0}}a({modulus}n+{residue})q^n={rhs}+O(q^{{{len(coeffs)}}})"


def run_dissection_dictionary():
    st.title("📚 Verified Dissection Library & LaTeX Vault")
    st.markdown(
        "Every stored identity is coefficient-audited before use. Each identity and the complete library "
        "can now be copied or downloaded directly as LaTeX."
    )
    verification_limit = st.slider("Verification precision", 30, 180, 100, 10)
    db = verified_dissection_database(verification_limit)
    verified_count = sum(bool(item.get("verified")) for item in db)
    c1, c2, c3 = st.columns(3)
    c1.metric("Stored identities", len(db))
    c2.metric("Passed audit", verified_count)
    c3.metric("Supported dissections", "2, 3, 5")

    p_filter = st.radio("Show", ["All", 2, 3, 5], horizontal=True)
    shown = db if p_filter == "All" else [x for x in db if x["p"] == p_filter]
    all_export = dissection_library_latex(shown)
    with st.expander("Copy/export the complete displayed library", expanded=False):
        render_latex_export(
            "Complete verified dissection library",
            all_export,
            key=f"all_library_{p_filter}_{verification_limit}",
            filename=f"verified_{p_filter}_dissections.tex",
        )
        st.download_button(
            "Download complete standalone LaTeX document",
            data=latex_document("Verified dissection identities", all_export),
            file_name=f"verified_{p_filter}_dissections_document.tex",
            mime="text/x-tex",
            key=f"doc_library_{p_filter}_{verification_limit}",
            use_container_width=True,
        )

    status_df = pd.DataFrame([{
        "p": item["p"], "identity": item["name"], "verified through": item["limit"],
        "status": "verified" if item["verified"] else f"FAILED at {item.get('mismatch')}",
        "source": item["source"]
    } for item in shown])
    st.dataframe(status_df, use_container_width=True, hide_index=True)

    for idx, item in enumerate(shown):
        status_icon = "✅" if item["verified"] else "❌"
        with st.expander(f"{status_icon} {item['p']}-dissection: {item['nice_name']}"):
            identity = rf"{item['latex_lhs']}={item['latex_rhs']}"
            st.latex(identity)
            st.caption(item["source"])
            if st.button("Explain identity", key=f"explain_identity_{p_filter}_{idx}_{verification_limit}", use_container_width=True):
                open_identity_explanation(item)
            render_latex_export(
                f"LaTeX for {item['nice_name']}",
                identity,
                key=f"identity_{p_filter}_{idx}_{verification_limit}",
                filename=f"{safe_widget_key(item['name']).lower()}_{item['p']}_dissection.tex",
            )


def run_auto_dissection():
    st.title("🧩 Automatic p-Dissection Solver")
    st.markdown(
        "Enter either a single eta product/quotient or a finite sum or difference of eta monomials. "
        "For p=2,3,5 the solver first tries the verified identity library; p=7,11 are available through exact finite coefficient extraction. "
        "It recombines components, checks coefficients independently, and explains every justified identity substitution in readable and LaTeX form."
    )
    with st.sidebar:
        st.header("Dissection input")
        latex_input = st.text_area(
            "F(q)",
            value=r"\frac{f_1^2}{f_2}-\frac{f_1^6}{f_2^3}",
            height=100,
            key="auto_dissection_input",
        )
        st.latex(latex_input)
        p_value = st.selectbox("p-dissection", [2, 3, 5, 7, 11], index=1, key="auto_p")
        verify_terms = st.number_input("Verification terms", min_value=40, value=140, step=10, key="auto_verify")
        max_scale = st.number_input("Maximum identity scale", min_value=1, value=30, step=1, key="auto_scale")
        max_power = st.number_input("Maximum identity repetitions", min_value=1, value=8, step=1, key="auto_power")
        max_symbolic_terms = st.number_input("Maximum symbolic branches", min_value=20, value=1800, step=50, key="auto_branches")
        run_btn = st.button("Find p-dissection", type="primary", use_container_width=True, key="auto_run")
    if not run_btn:
        st.info("This solver now accepts sums and differences directly; use the Composite Lab for deeper progressions such as a(8n+7).")
        return

    try:
        input_expr = parse_eta_linear_combination(latex_input)
        db = verified_dissection_database(min(110, int(verify_terms)))
        exact = dissect_symbolic_expression_once(
            input_expr,
            int(p_value),
            db,
            int(max_scale),
            int(max_power),
            int(max_symbolic_terms),
            int(verify_terms),
        )

        tabs = st.tabs(["Exact symbolic result", "Residue extraction", "Coefficient fallback", "Step-by-step derivation"])
        exact_success = bool(exact.get("success"))
        exact_expr = exact.get("expression")
        exact_components = exact.get("components")

        with tabs[0]:
            if exact_success:
                st.success(
                    f"Exact term-by-term {p_value}-dissection assembled and independently checked through q^{verify_terms}."
                )
                st.latex(rf"F(q)={exact_expr.to_latex()}")
                full_code = rf"F(q)&={exact_expr.to_latex()}"
                render_latex_export(
                    "Exact dissection LaTeX",
                    "\\begin{aligned}\n" + full_code + "\n\\end{aligned}",
                    key=f"auto_exact_{hashlib.md5(latex_input.encode()).hexdigest()}_{p_value}",
                    filename=f"exact_{p_value}_dissection.tex",
                )
            else:
                st.warning("No exact finite closed form could be assembled within the selected identity and branch limits.")
                st.code(exact.get("reason", "No reason returned."))

        coeffs = _core_expansion_engine(latex_input, int(verify_terms))
        with tabs[1]:
            component_lines = []
            for r in range(int(p_value)):
                st.markdown(f"#### Extract coefficients of $q^{{{p_value}n+{r}}}$")
                if exact_success:
                    rhs = exact_components[r].to_latex()
                    equation = component_equation_latex(int(p_value), r, rhs)
                    if rhs == "0":
                        st.success(f"The component a({p_value}n+{r}) vanishes identically in the exact symbolic result.")
                else:
                    component = coeffs[r::int(p_value)]
                    equation = truncated_component_latex(component, int(p_value), r)
                st.latex(equation)
                component_lines.append(equation)
                render_latex_export(
                    f"Component a({p_value}n+{r})",
                    equation,
                    key=f"auto_component_{p_value}_{r}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename=f"component_{p_value}n_plus_{r}.tex",
                )
            if component_lines:
                render_latex_export(
                    "All residue components",
                    "\\begin{aligned}\n" + " \\\\\n".join(line.replace("=", "&=", 1) for line in component_lines) + "\n\\end{aligned}",
                    key=f"auto_all_components_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename=f"all_{p_value}_components.tex",
                )
            st.info(r"Extraction rule: retain powers q^{pn+r}, divide by q^r, and replace q^p by q.")

        with tabs[2]:
            st.info("These are coefficient truncations. They remain available even when the identity library cannot produce a closed form.")
            rows = []
            fallback_lines = []
            for r in range(int(p_value)):
                component = coeffs[r::int(p_value)]
                equation = truncated_component_latex(component, int(p_value), r)
                st.latex(equation)
                fallback_lines.append(equation)
                rows.append({"r": r, "first coefficients": ", ".join(str(x) for x in component[:14])})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            render_latex_export(
                "Truncated coefficient dissection",
                "\\begin{aligned}\n" + " \\\\\n".join(line.replace("=", "&=", 1) for line in fallback_lines) + "\n\\end{aligned}",
                key=f"auto_fallback_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                filename=f"truncated_{p_value}_dissection.tex",
            )

        with tabs[3]:
            if not exact_success:
                render_coefficient_derivation_path(
                    input_expr,
                    int(p_value),
                    coeffs,
                    key_prefix=f"auto_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                )
            else:
                render_exact_derivation_path(
                    input_expr,
                    exact,
                    int(p_value),
                    key_prefix=f"auto_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    show_export=True,
                )
    except Exception as exc:
        st.error(f"Dissection analysis failed: {exc}")

def run_composite_dissection_lab():
    st.title("🧪 Composite 2/3-Dissection & Residue Laboratory")
    st.markdown(
        "This module accepts finite sums and differences of eta products. It first performs exact term-by-term "
        "dissection, then compares coefficients, recognizes simple f-products, and supports iterated extractions "
        "such as a(2n+1), a(4n+3), a(8n+7), or a(3^j n+r)."
    )
    with st.sidebar:
        st.header("Composite expression")
        latex_input = st.text_area(
            "F(q)=Σ a(n)qⁿ",
            value=r"\frac{f_1^2}{f_2}-\frac{f_1^6}{f_2^3}",
            height=110,
            key="composite_input",
        )
        st.latex(latex_input)
        p_value = st.selectbox("Dissection base", [2, 3], index=1, key="composite_p")
        verify_terms = st.number_input("Coefficient audit terms", min_value=50, value=180, step=10, key="composite_verify")
        max_scale = st.number_input("Maximum identity scale", min_value=1, value=30, step=1, key="composite_scale")
        max_power = st.number_input("Maximum repetitions", min_value=1, value=10, step=1, key="composite_power")
        max_terms = st.number_input("Maximum symbolic terms", min_value=30, value=2500, step=50, key="composite_terms")
        max_depth_allowed = 4 if int(p_value) == 2 else 3
        default_depth = 3 if int(p_value) == 2 else 2
        depth = st.number_input("Deep extraction depth", min_value=1, max_value=max_depth_allowed, value=default_depth, step=1, key="composite_depth")
        modulus = int(p_value) ** int(depth)
        default_residue = modulus - 1
        residue = st.number_input("Target residue r", min_value=0, max_value=modulus - 1, value=default_residue, step=1, key="composite_residue")
        run_btn = st.button("Run composite laboratory", type="primary", use_container_width=True, key="composite_run")
    if not run_btn:
        st.info("The default example is a difference of two eta quotients. Choose base 3 to obtain a compact exact dissection.")
        return

    try:
        input_expr = parse_eta_linear_combination(latex_input)
        db = verified_dissection_database(min(110, int(verify_terms)))
        exact = dissect_symbolic_expression_once(
            input_expr, int(p_value), db, int(max_scale), int(max_power), int(max_terms), int(verify_terms)
        )
        coeffs = _core_expansion_engine(latex_input, int(verify_terms))
        tabs = st.tabs([
            "Exact composite dissection",
            "Residue components",
            "Deep progression extraction",
            "Coefficient/product recognition",
            "Step-by-step derivation",
            "LaTeX report",
        ])
        export_sections = []

        with tabs[0]:
            if exact.get("success"):
                expression = exact["expression"]
                st.success(
                    f"Exact term-by-term {p_value}-dissection found; full coefficient comparison agrees through q^{verify_terms}."
                )
                st.latex(rf"F(q)={expression.to_latex()}")
                code = "\\begin{aligned}\n" + rf"F(q)&={expression.to_latex()}" + "\n\\end{aligned}"
                export_sections.append(("Exact composite dissection", code))
                render_latex_export(
                    "Exact composite dissection",
                    code,
                    key=f"composite_exact_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename=f"composite_exact_{p_value}_dissection.tex",
                )
                st.info("Open the Step-by-step derivation tab to see every identity, scaling, substitution, recombination, and extraction rule.")
                derivation_code = exact_derivation_latex(input_expr, exact, int(p_value))
                export_sections.append(("Step-by-step exact derivation", derivation_code))
            else:
                st.warning("Exact symbolic assembly was not available.")
                st.code(exact.get("reason", "No reason returned."))
                st.info("The coefficient and product-recognition tabs still provide useful finite-data output.")

        with tabs[1]:
            component_export = []
            cards = st.columns(int(p_value))
            for r in range(int(p_value)):
                with cards[r]:
                    st.metric("Residue", f"{p_value}n+{r}")
                if exact.get("success"):
                    rhs = exact["components"][r].to_latex()
                    equation = component_equation_latex(int(p_value), r, rhs)
                    complexity = exact["components"][r].term_count
                    st.latex(equation)
                    if rhs == "0":
                        st.success(f"The extraction a({p_value}n+{r}) vanishes identically in the exact symbolic result.")
                    elif complexity <= 4:
                        st.success(f"Simple exact component: {complexity} symbolic term(s).")
                    else:
                        st.caption(f"Exact component with {complexity} symbolic terms.")
                else:
                    component = coeffs[r::int(p_value)]
                    equation = truncated_component_latex(component, int(p_value), r)
                    st.latex(equation)
                component_export.append(equation)
                render_latex_export(
                    f"Extracted component a({p_value}n+{r})",
                    equation,
                    key=f"composite_component_{p_value}_{r}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename=f"a_{p_value}n_plus_{r}.tex",
                )
            all_components = "\\begin{aligned}\n" + " \\\\\n".join(
                line.replace("=", "&=", 1) for line in component_export
            ) + "\n\\end{aligned}"
            export_sections.append(("Residue components", all_components))
            st.info(r"To extract a(pn+r): retain q^{pn+r}, divide by q^r, and replace q^p by q.")

        with tabs[2]:
            modulus = int(p_value) ** int(depth)
            residue = int(residue)
            st.markdown(f"### Target progression: $a({modulus}n+{residue})$")
            st.latex(progression_chain_latex(int(p_value), residue, int(depth)))
            deep = deep_exact_extraction(
                input_expr, int(p_value), residue, int(depth), db,
                int(max_scale), int(max_power), int(max_terms), int(verify_terms)
            )
            direct_component = coeffs[residue::modulus]
            deep_equation = None
            if deep.get("success"):
                rhs = deep["expression"].to_latex()
                deep_equation = rf"\sum_{{n\ge0}}a({modulus}n+{residue})q^n={rhs}"
                # Compare against the direct coefficient extraction in its own q variable.
                direct_limit = len(direct_component) - 1
                symbolic_coeffs = symexpr_to_qseries(deep["expression"], direct_limit).coeffs
                mismatch = next((n for n, (a, b) in enumerate(zip(symbolic_coeffs, direct_component)) if a != b), None)
                if mismatch is None:
                    st.success("Exact iterated extraction succeeded and agrees with direct coefficient extraction.")
                    st.latex(deep_equation)
                    if deep["expression"].term_count <= 5:
                        st.success(f"The resulting form is simple: {deep['expression'].term_count} symbolic term(s).")
                    export_sections.append((f"Deep extraction a({modulus}n+{residue})", deep_equation))
                    render_latex_export(
                        f"Exact deep extraction a({modulus}n+{residue})",
                        deep_equation,
                        key=f"deep_exact_{modulus}_{residue}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                        filename=f"a_{modulus}n_plus_{residue}.tex",
                    )
                    deep_path_code = deep_derivation_latex(input_expr, int(p_value), residue, deep)
                    export_sections.append((f"Step-by-step path to a({modulus}n+{residue})", deep_path_code))
                    st.markdown("#### Path used for the iterated extraction")
                    render_deep_derivation_path(
                        input_expr,
                        int(p_value),
                        residue,
                        deep,
                        key_prefix=f"deep_{modulus}_{residue}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    )
                else:
                    st.warning(f"The symbolic deep result failed direct comparison at coefficient q^{mismatch}; it has been suppressed.")
                    deep_equation = None
            else:
                st.warning(f"Exact iteration stopped at level {deep.get('level', '?')}: {deep.get('reason', 'unknown reason')}")

            if deep_equation is None:
                fallback = truncated_component_latex(direct_component, modulus, residue)
                st.latex(fallback)
                st.caption("Finite coefficient extraction only; this is not an identity proof.")
                export_sections.append((f"Truncated a({modulus}n+{residue})", fallback))
                render_latex_export(
                    f"Truncated extraction a({modulus}n+{residue})",
                    fallback,
                    key=f"deep_truncated_{modulus}_{residue}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename=f"truncated_a_{modulus}n_plus_{residue}.tex",
                )

            recognition = recognize_f_product(direct_component, fit_limit=min(90, len(direct_component)-1))
            if recognition.get("success"):
                if recognition.get("zero"):
                    st.success(f"All computed coefficients in a({modulus}n+{residue}) are zero through the available range.")
                else:
                    candidate = rf"\sum_{{n\ge0}}a({modulus}n+{residue})q^n\overset{{?}}{{=}}{recognition['latex']}"
                    st.markdown("#### Coefficient-recognized simple product candidate")
                    st.latex(candidate)
                    st.caption(
                        f"The candidate agrees through q^{recognition['verified_through']}; a separate proof is still required unless it matches the exact symbolic result above."
                    )

        with tabs[3]:
            st.markdown("### Automatic coefficient comparison across residue classes")
            st.caption(
                "The recognizer converts each extracted series into Euler product exponents and Möbius-inverts them to search for a finite f-product. Matches are computational candidates unless supported by the exact tab."
            )
            rows = []
            recognized_lines = []
            max_scan_depth = min(int(depth), 3)
            for level in range(1, max_scan_depth + 1):
                mod = int(p_value) ** level
                for r in range(mod):
                    component = coeffs[r::mod]
                    rec = recognize_f_product(component, fit_limit=min(80, len(component)-1))
                    if rec.get("success"):
                        if rec.get("zero"):
                            kind, form = "zero in computed range", "0"
                        else:
                            kind, form = "finite f-product candidate", rec["latex"]
                            recognized_lines.append(
                                rf"\sum_{{n\ge0}}a({mod}n+{r})q^n&\overset{{?}}{{=}}{form}"
                            )
                        rows.append({
                            "progression": f"a({mod}n+{r})",
                            "classification": kind,
                            "recognized form": form,
                            "checked coefficients": len(component),
                        })
                    else:
                        nonzero_first = sum(1 for c in component[:20] if c)
                        if nonzero_first <= 3:
                            rows.append({
                                "progression": f"a({mod}n+{r})",
                                "classification": "sparse first 20 terms",
                                "recognized form": "—",
                                "checked coefficients": len(component),
                            })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.info("No especially simple or sparse progression was detected within the selected range.")
            if recognized_lines:
                recognized_code = "\\begin{aligned}\n" + " \\\\\n".join(recognized_lines) + "\n\\end{aligned}"
                export_sections.append(("Coefficient-recognized product candidates", recognized_code))
                render_latex_export(
                    "All recognized product candidates",
                    recognized_code,
                    key=f"recognized_all_{p_value}_{depth}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename="recognized_dissection_candidates.tex",
                )

        with tabs[4]:
            if exact.get("success"):
                path_code = render_exact_derivation_path(
                    input_expr,
                    exact,
                    int(p_value),
                    key_prefix=f"composite_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    show_export=True,
                )
                if path_code and not any(title == "Step-by-step exact derivation" for title, _ in export_sections):
                    export_sections.append(("Step-by-step exact derivation", path_code))
            else:
                fallback_path = render_coefficient_derivation_path(
                    input_expr,
                    int(p_value),
                    coeffs,
                    key_prefix=f"composite_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                )
                export_sections.append(("Coefficient-based dissection path", fallback_path))

        with tabs[5]:
            if not export_sections:
                st.info("No exportable result was produced.")
            else:
                report_body = "\n\n".join(
                    f"% --- {title} ---\n{code}" for title, code in export_sections
                )
                render_latex_export(
                    "Complete analysis LaTeX",
                    report_body,
                    key=f"composite_report_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    filename="composite_dissection_report.tex",
                )
                st.download_button(
                    "Download standalone LaTeX report",
                    data=latex_document("Composite dissection analysis", report_body),
                    file_name="composite_dissection_report_standalone.tex",
                    mime="text/x-tex",
                    key=f"composite_standalone_{p_value}_{hashlib.md5(latex_input.encode()).hexdigest()}",
                    use_container_width=True,
                )
    except Exception as exc:
        st.error(f"Composite dissection analysis failed: {exc}")


# ==========================================
# --- RESEARCH SUITE ENHANCEMENTS (V5) ---
# ==========================================

def _integer_coefficients_for_external_tools(formula, limit):
    coeffs = _core_expansion_engine(formula, int(limit))
    require_integral_coefficients(coeffs, "this external-tool operation")
    return [int(c) for c in coeffs]


def _series_latex(coeffs, symbol="q", max_terms=16):
    pieces = []
    shown = 0
    for n, value in enumerate(coeffs):
        value = Fraction(value)
        if value == 0:
            continue
        sign = "+" if value > 0 else "-"
        av = abs(value)
        if n == 0:
            monomial = ""
        elif n == 1:
            monomial = symbol
        else:
            monomial = f"{symbol}^{{{n}}}"
        coeff = "" if av == 1 and monomial else format_latex_frac(av)
        term = f"{coeff}{monomial}" or "1"
        if not pieces:
            pieces.append(("-" if value < 0 else "") + term)
        else:
            pieces.append(f" {sign} {term}")
        shown += 1
        if shown >= max_terms:
            break
    return "".join(pieces) if pieces else "0"


def apply_u_operator(coeffs, p, out_limit=None):
    p = int(p)
    out_limit = int(out_limit if out_limit is not None else (len(coeffs)-1)//p)
    return [coeffs[p*n] if p*n < len(coeffs) else 0 for n in range(out_limit+1)]


def apply_v_operator(coeffs, p, out_limit=None):
    p = int(p)
    out_limit = int(out_limit if out_limit is not None else (len(coeffs)-1)*p)
    out = [0]*(out_limit+1)
    for n, value in enumerate(coeffs):
        idx = p*n
        if idx <= out_limit:
            out[idx] = value
    return out


def apply_theta_operator(coeffs, order=1):
    order = int(order)
    return [(n**order)*value for n, value in enumerate(coeffs)]


def apply_integral_hecke(coeffs, p, weight, chi_p=1, out_limit=None):
    p, weight = int(p), int(weight)
    out_limit = int(out_limit if out_limit is not None else (len(coeffs)-1)//p)
    out = []
    for n in range(out_limit+1):
        first = coeffs[p*n] if p*n < len(coeffs) else 0
        second = 0
        if n % p == 0 and n//p < len(coeffs):
            second = int(chi_p)*(p**(weight-1))*coeffs[n//p]
        out.append(first+second)
    return out


def _legendre_symbol(n, p):
    n %= p
    if n == 0:
        return 0
    return 1 if pow(n, (p-1)//2, p) == 1 else -1


def apply_half_integral_hecke_p2(coeffs, p, lam, epsilon_p=1, chi_p2=1, out_limit=None):
    """Convention: weight lam+1/2 and effective middle multiplier epsilon_p."""
    p, lam = int(p), int(lam)
    out_limit = int(out_limit if out_limit is not None else (len(coeffs)-1)//(p*p))
    out = []
    for n in range(out_limit+1):
        first = coeffs[p*p*n] if p*p*n < len(coeffs) else 0
        middle = int(epsilon_p)*_legendre_symbol(n, p)*(p**(lam-1))*coeffs[n]
        last = 0
        if n % (p*p) == 0 and n//(p*p) < len(coeffs):
            last = int(chi_p2)*(p**(2*lam-1))*coeffs[n//(p*p)]
        out.append(first+middle+last)
    return out


def run_operator_sandbox():
    st.title("⚙️ Hecke, U/V & Differential Operator Sandbox")
    st.markdown(
        "Apply coefficient operators to any supported q-series. Integral-weight $T_p$ is implemented exactly; "
        "the half-integral $T(p^2)$ panel states the convention and exposes the effective character multipliers."
    )
    with st.sidebar:
        formula = st.text_area("Input series $F(q)$", value=r"\eta(z)^2\eta(11z)^2" if False else r"f_1^2 f_{11}^2", height=90, key="op_formula")
        operator = st.selectbox("Operator", ["U_p", "V_p", "Integral-weight T_p", "Half-integral T(p^2)", "Theta = q d/dq"], key="op_kind")
        p = st.number_input("Prime p", min_value=2, value=3, step=1, key="op_p")
        output_terms = st.number_input("Output degree", min_value=10, value=80, step=10, key="op_terms")
        weight = 2
        chi_p = 1
        lam = 1
        epsilon_p = 1
        chi_p2 = 1
        theta_order = 1
        if operator == "Integral-weight T_p":
            weight = st.number_input("Integral weight k", min_value=1, value=2, step=1, key="op_weight")
            chi_p = st.selectbox(r"$\chi(p)$", [-1, 0, 1], index=2, key="op_chip")
        elif operator == "Half-integral T(p^2)":
            lam = st.number_input(r"$\lambda$ in weight $\lambda+\frac12$", min_value=1, value=1, step=1, key="op_lam")
            epsilon_p = st.selectbox(r"Effective middle multiplier $\varepsilon_p$", [-1, 0, 1], index=2, key="op_eps")
            chi_p2 = st.selectbox(r"$\chi(p^2)$", [-1, 0, 1], index=2, key="op_chip2")
        elif operator == "Theta = q d/dq":
            theta_order = st.number_input("Iteration order", min_value=1, value=1, step=1, key="op_theta_order")
        run = st.button("Apply operator", type="primary", use_container_width=True, key="op_run")
    if not run:
        st.info("Example: apply $T_3$ to a weight-2 eta product, or use $U_5$ to extract coefficients $a(5n)$.")
        return
    try:
        p = int(p)
        out_n = int(output_terms)
        required = out_n
        if operator == "U_p" or operator == "Integral-weight T_p":
            required = p*out_n
        elif operator == "Half-integral T(p^2)":
            required = p*p*out_n
        coeffs = _core_expansion_engine(formula, required)
        if operator == "U_p":
            result = apply_u_operator(coeffs, p, out_n)
            law = rf"(F\mid U_{{{p}}})(q)=\sum_{{n\ge0}}a({p}n)q^n"
        elif operator == "V_p":
            result = apply_v_operator(coeffs, p, out_n)
            law = rf"(F\mid V_{{{p}}})(q)=F(q^{{{p}}})"
        elif operator == "Integral-weight T_p":
            result = apply_integral_hecke(coeffs, p, int(weight), int(chi_p), out_n)
            law = rf"b(n)=a({p}n)+{int(chi_p)}\,{p}^{{{int(weight)-1}}}a(n/{p})"
        elif operator == "Half-integral T(p^2)":
            result = apply_half_integral_hecke_p2(coeffs, p, int(lam), int(epsilon_p), int(chi_p2), out_n)
            law = rf"b(n)=a({p}^2n)+{int(epsilon_p)}\left(\frac{{n}}{{{p}}}\right){p}^{{{int(lam)-1}}}a(n)+{int(chi_p2)}{p}^{{{2*int(lam)-1}}}a(n/{p}^2)"
        else:
            result = apply_theta_operator(coeffs[:out_n+1], int(theta_order))
            law = rf"\Theta^{{{int(theta_order)}}}F=\sum_{{n\ge0}}n^{{{int(theta_order)}}}a(n)q^n"
        st.success("Operator applied with exact rational arithmetic.")
        st.latex(law)
        st.latex(rf"\text{{Result}}={_series_latex(result, max_terms=18)}+O(q^{{{len(result)}}})")
        df = pd.DataFrame({"n": range(len(result)), "coefficient": [str(x) for x in result]})
        st.dataframe(df, use_container_width=True, hide_index=True)
        latex = "\\begin{aligned}\n" + law + r"\\" + "\n" + rf"(F\mid\mathcal O)(q)&={_series_latex(result, max_terms=30)}+O(q^{{{len(result)}}})" + "\n\\end{aligned}"
        render_latex_export("Operator calculation", latex, key=f"operator_{operator}_{p}_{hashlib.md5(formula.encode()).hexdigest()}")
    except Exception as exc:
        st.error(f"Operator calculation failed: {exc}")


def _eta_congruence_certificate(lhs_formula, rhs_formula, level, modulus):
    lhs_eta = parse_eta_product(lhs_formula)
    rhs_eta = parse_eta_product(rhs_formula)
    lhs_info = analyze_eta_quotient(lhs_eta, int(level))
    rhs_info = analyze_eta_quotient(rhs_eta, int(level))
    blockers = []
    for label, info in [("left", lhs_info), ("right", rhs_info)]:
        if not info["modular"]:
            blockers.append(f"The {label} eta quotient fails an integral-weight Newman congruence.")
        if not info["holomorphic"]:
            blockers.append(f"The {label} eta quotient has a pole at a cusp.")
    if lhs_info["weight"] != rhs_info["weight"]:
        blockers.append("The two forms have different weights.")
    if lhs_info["character_D"] != rhs_info["character_D"]:
        blockers.append("The two forms have different encoded quadratic characters.")
    if lhs_info["q_shift"] != rhs_info["q_shift"]:
        blockers.append("The f-product-to-eta q-shifts differ, so direct coefficient comparison is not a same-form congruence.")
    bound = max(lhs_info.get("sturm") or 0, rhs_info.get("sturm") or 0)
    if blockers:
        return {"certified": False, "blockers": blockers, "lhs": lhs_info, "rhs": rhs_info, "bound": bound}
    lhs_coeffs = _core_expansion_engine(lhs_formula, bound)
    rhs_coeffs = _core_expansion_engine(rhs_formula, bound)
    failures = [n for n in range(bound+1) if (lhs_coeffs[n]-rhs_coeffs[n]) % int(modulus) != 0]
    return {
        "certified": not failures,
        "blockers": [],
        "lhs": lhs_info,
        "rhs": rhs_info,
        "bound": bound,
        "failures": failures,
        "checked": bound+1,
    }


def run_sturm_verifier():
    st.title("✅ Automatic Sturm-Bound Certificate")
    st.markdown(
        "This module certifies congruences between holomorphic integral-weight eta quotients of the same level, "
        "weight, character, and q-shift. It refuses to call a finite check a proof when these hypotheses are missing."
    )
    c1, c2 = st.columns(2)
    with c1:
        lhs = st.text_area("Left side", value=r"f_1^2 f_{11}^2", height=90, key="sturm_lhs")
    with c2:
        rhs = st.text_area("Right side", value=r"f_1^2 f_{11}^2", height=90, key="sturm_rhs")
    level_col, mod_col = st.columns(2)
    level = level_col.number_input("Level N", min_value=1, value=11, step=1, key="sturm_level")
    modulus = mod_col.number_input("Congruence modulus M", min_value=2, value=5, step=1, key="sturm_mod")
    if not st.button("Build Sturm certificate", type="primary", use_container_width=True, key="sturm_run"):
        st.info("For a nontrivial test, enter two eta quotients known or conjectured to be congruent modulo M.")
        return
    try:
        cert = _eta_congruence_certificate(lhs, rhs, int(level), int(modulus))
        a, b, c = st.columns(3)
        a.metric("Weight", str(cert["lhs"]["weight"]))
        b.metric("Sturm bound", cert["bound"])
        c.metric("Character kernel", cert["lhs"]["character_D"])
        if cert["blockers"]:
            st.error("A Sturm proof cannot be issued.")
            for reason in cert["blockers"]:
                st.write(f"- {reason}")
        elif cert["certified"]:
            st.success(f"Certified: all coefficients through the Sturm bound B={cert['bound']} vanish modulo {int(modulus)}.")
        else:
            first = cert["failures"][0]
            st.error(f"The congruence fails; the first failing coefficient is n={first}.")
        table = []
        for side, info in [("LHS", cert["lhs"]), ("RHS", cert["rhs"])]:
            table.append({"side": side, "weight": str(info["weight"]), "q-shift": str(info["q_shift"]), "modular": info["modular"], "holomorphic": info["holomorphic"], "Sturm": info["sturm"], "character D": info["character_D"]})
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
        proof = (
            rf"\text{{On }}\Gamma_0({int(level)}),\quad k={format_latex_frac(cert['lhs']['weight'])},\quad B={cert['bound']}." "\\\n"
            rf"{lhs}&\equiv {rhs}\pmod{{{int(modulus)}}}."
        )
        render_latex_export("Sturm certificate", "\\begin{aligned}\n"+proof+"\n\\end{aligned}", key=f"sturm_{level}_{modulus}_{hashlib.md5((lhs+rhs).encode()).hexdigest()}")
    except Exception as exc:
        st.error(f"Sturm analysis failed: {exc}")


def _normalize_relation(values):
    vals = [int(v) for v in values]
    g = 0
    for v in vals:
        g = math.gcd(g, abs(v))
    if g:
        vals = [v//g for v in vals]
    for v in vals:
        if v:
            if v < 0:
                vals = [-x for x in vals]
            break
    return vals


def find_series_relations(formulas, degree=30, use_lll=True, tail_scale=1000):
    import sympy as sp
    vectors = []
    for formula in formulas:
        coeffs = _core_expansion_engine(formula, int(degree))
        den = lcm_list([Fraction(c).denominator for c in coeffs])
        vectors.append([int(Fraction(c)*den) for c in coeffs])
    A = sp.Matrix(int(degree)+1, len(formulas), lambda i, j: vectors[j][i])
    exact = []
    for vec in A.nullspace():
        den = lcm_list([sp.Rational(x).q for x in vec])
        exact.append(_normalize_relation([int(sp.Rational(x)*den) for x in vec]))
    lll_hits = []
    if use_lll and len(formulas) >= 2:
        rows = []
        for i, vector in enumerate(vectors):
            row = [0]*len(formulas)
            row[i] = 1
            row += [int(tail_scale)*v for v in vector]
            rows.append(row)
        reduced = sp.Matrix(rows).lll()
        for row in reduced.tolist():
            head = row[:len(formulas)]
            tail = row[len(formulas):]
            if any(head) and all(v == 0 for v in tail):
                relation = _normalize_relation(head)
                if relation not in exact and relation not in lll_hits:
                    lll_hits.append(relation)
    return {"exact": exact, "lll": lll_hits, "vectors": vectors}


def _relation_latex(relation, names):
    pieces = []
    for coefficient, name in zip(relation, names):
        if not coefficient:
            continue
        sign = "+" if coefficient > 0 else "-"
        absolute = abs(coefficient)
        factor = "" if absolute == 1 else str(absolute)
        term = f"{factor}\\left({name}\\right)"
        if not pieces:
            pieces.append(("-" if coefficient < 0 else "")+term)
        else:
            pieces.append(f" {sign} {term}")
    return "".join(pieces)+"=0"


def run_relation_finder():
    st.title("🧮 Exact / LLL Relation Finder")
    st.markdown("Enter one q-series per line. The engine first computes the exact rational nullspace and then uses LLL to search for short integer relations.")
    formulas_text = st.text_area(
        "Series list",
        value="\n".join([r"f_1^2", r"\frac{f_2 f_8^5}{f_4^2 f_{16}^2}", r"q\frac{f_2 f_{16}^2}{f_8}"]),
        height=150,
        key="lll_formulas",
    )
    c1, c2 = st.columns(2)
    degree = c1.number_input("Coefficient degree", min_value=8, value=40, step=5, key="lll_degree")
    tail_scale = c2.number_input("LLL tail scale", min_value=10, value=1000, step=10, key="lll_scale")
    if not st.button("Find relations", type="primary", use_container_width=True, key="lll_run"):
        return
    formulas = [line.strip() for line in formulas_text.splitlines() if line.strip()]
    if len(formulas) < 2:
        st.error("Enter at least two series.")
        return
    try:
        result = find_series_relations(formulas, int(degree), True, int(tail_scale))
        relations = result["exact"] + [x for x in result["lll"] if x not in result["exact"]]
        if not relations:
            st.warning("No exact short relation was detected at this truncation.")
        for idx, relation in enumerate(relations, 1):
            latex = _relation_latex(relation, formulas)
            st.latex(latex)
            st.caption("Exact nullspace relation" if relation in result["exact"] else "LLL short relation; verify at higher precision before publication.")
            render_latex_export(f"Relation {idx}", latex, key=f"relation_{idx}_{hashlib.md5(formulas_text.encode()).hexdigest()}")
        matrix_preview = pd.DataFrame({f"F{j+1}": vector[:min(20, len(vector))] for j, vector in enumerate(result["vectors"])})
        st.dataframe(matrix_preview, use_container_width=True)
    except Exception as exc:
        st.error(f"Relation search failed: {exc}")


def _bivar_one(N):
    out = [dict() for _ in range(N+1)]
    out[0][0] = 1
    return out


def _bivar_add(A, B, N):
    out = [dict(row) for row in A]
    for n in range(N+1):
        for z, value in B[n].items():
            out[n][z] = out[n].get(z, 0)+value
            if out[n][z] == 0:
                out[n].pop(z)
    return out


def _bivar_geom_multiply(A, q_step, z_step, N):
    out = [dict() for _ in range(N+1)]
    for n in range(N+1):
        for z, value in A[n].items():
            k = 0
            while n+k*q_step <= N:
                nn = n+k*q_step
                zz = z+k*z_step
                out[nn][zz] = out[nn].get(zz, 0)+value
                k += 1
    return out


def crank_distribution(N):
    B = _bivar_one(N)
    for j in range(1, N+1):
        B = _bivar_geom_multiply(B, j, 1, N)
        B = _bivar_geom_multiply(B, j, -1, N)
    f1 = generate_base_pochhammer(1, N)
    out = [dict() for _ in range(N+1)]
    for i, a in enumerate(f1):
        if not a:
            continue
        for n in range(N-i+1):
            for z, value in B[n].items():
                out[n+i][z] = out[n+i].get(z, 0)+a*value
    return out


def rank_distribution(N):
    total = _bivar_one(N)
    denominator = _bivar_one(N)
    n = 1
    while n*n <= N:
        denominator = _bivar_geom_multiply(denominator, n, 1, N)
        denominator = _bivar_geom_multiply(denominator, n, -1, N)
        shifted = [dict() for _ in range(N+1)]
        for qdeg in range(N-n*n+1):
            shifted[qdeg+n*n] = dict(denominator[qdeg])
        total = _bivar_add(total, shifted, N)
        n += 1
    return total


def distribution_moment(distribution, order):
    return [sum((m**order)*count for m, count in row.items()) for row in distribution]


def run_moment_lab():
    st.title("📐 Theta, Rank & Crank Moment Laboratory")
    mode = st.radio("Analysis", ["Theta operator on a series", "Rank/crank moments"], horizontal=True, key="moment_mode")
    if mode == "Theta operator on a series":
        formula = st.text_area("F(q)", value=r"\frac{1}{f_1}", height=80, key="moment_formula")
        c1, c2 = st.columns(2)
        order = c1.number_input("Theta order", min_value=1, value=1, step=1, key="moment_theta_order")
        N = c2.number_input("Degree", min_value=10, value=80, step=10, key="moment_theta_N")
        if st.button("Apply theta", type="primary", use_container_width=True, key="moment_theta_run"):
            try:
                coeffs = _core_expansion_engine(formula, int(N))
                transformed = apply_theta_operator(coeffs, int(order))
                st.latex(rf"\Theta^{{{int(order)}}}F(q)={_series_latex(transformed, max_terms=20)}+O(q^{{{int(N)+1}}})")
                st.dataframe(pd.DataFrame({"n": range(len(transformed)), "a(n)": [str(x) for x in coeffs], "n^r a(n)": [str(x) for x in transformed]}), use_container_width=True, hide_index=True)
            except Exception as exc:
                st.error(str(exc))
    else:
        c1, c2, c3 = st.columns(3)
        statistic = c1.selectbox("Statistic", ["Crank", "Rank", "Crank minus rank"], key="moment_stat")
        order = c2.selectbox("Moment order", [2, 4, 6], key="moment_order")
        N = c3.number_input("Maximum n", min_value=5, max_value=60, value=25, step=5, key="moment_N")
        if st.button("Compute moments", type="primary", use_container_width=True, key="moment_run"):
            with st.spinner("Expanding the two-variable generating function..."):
                crank = crank_distribution(int(N)) if statistic != "Rank" else None
                rank = rank_distribution(int(N)) if statistic != "Crank" else None
                if statistic == "Crank":
                    values = distribution_moment(crank, int(order))
                    label = f"M_{int(order)}(n)"
                elif statistic == "Rank":
                    values = distribution_moment(rank, int(order))
                    label = f"N_{int(order)}(n)"
                else:
                    cm = distribution_moment(crank, int(order))
                    rm = distribution_moment(rank, int(order))
                    values = [a-b for a, b in zip(cm, rm)]
                    label = f"M_{int(order)}(n)-N_{int(order)}(n)"
            st.success("Moment sequence computed from the two-variable generating functions.")
            st.dataframe(pd.DataFrame({"n": range(len(values)), label: values}), use_container_width=True, hide_index=True)
            st.latex(rf"\sum_{{n\ge0}}{label}q^n={_series_latex(values, max_terms=18)}+O(q^{{{int(N)+1}}})")


def oeis_search(sequence, max_results=5):
    import requests
    query = ",".join(str(int(x)) for x in sequence)
    response = requests.get(
        "https://oeis.org/search",
        params={"q": query, "fmt": "json"},
        headers={"User-Agent": "Ramanujan-Laboratory/5.0 (research sequence lookup)"},
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", payload if isinstance(payload, list) else [])
    return results[:int(max_results)]


def _oeis_result_number(item):
    number = item.get("number")
    if number is None:
        return ""
    try:
        return f"A{int(number):06d}"
    except Exception:
        return str(number)


def run_oeis_lookup():
    st.title("🔎 OEIS Sequence Identification")
    st.warning("This optional module sends only the displayed integer coefficient list to OEIS. The original formula is not transmitted.")
    formula = st.text_area("Series", value=r"\frac{1}{f_1}", height=80, key="oeis_formula")
    c1, c2 = st.columns(2)
    terms = c1.number_input("Terms sent", min_value=6, max_value=50, value=20, step=1, key="oeis_terms")
    max_results = c2.number_input("Maximum matches", min_value=1, max_value=10, value=5, step=1, key="oeis_results")
    if not st.button("Search OEIS", type="primary", use_container_width=True, key="oeis_run"):
        return
    try:
        coeffs = _integer_coefficients_for_external_tools(formula, int(terms)-1)
        st.code(", ".join(str(x) for x in coeffs))
        matches = oeis_search(coeffs, int(max_results))
        if not matches:
            st.warning("OEIS returned no match for this initial segment.")
            return
        for item in matches:
            number = _oeis_result_number(item)
            name = item.get("name", "Unnamed sequence")
            with st.expander(f"{number}: {name}", expanded=False):
                st.write(item.get("data", ""))
                if item.get("formula"):
                    st.write("**Formula notes:**", item.get("formula")[:3] if isinstance(item.get("formula"), list) else item.get("formula"))
                st.link_button("Open OEIS entry", f"https://oeis.org/{number}")
    except Exception as exc:
        st.error(f"OEIS lookup failed. Internet access or the OEIS service may be unavailable: {exc}")


def p_adic_valuation(value, p):
    value = int(value)
    p = int(p)
    if value == 0:
        return None
    value = abs(value)
    valuation = 0
    while value % p == 0:
        valuation += 1
        value //= p
    return valuation


def run_visualization_studio():
    st.title("📊 Coefficient Visualization & Congruence Heatmaps")
    formula = st.text_area("F(q)", value=r"\frac{1}{f_1}", height=80, key="viz_formula")
    c1, c2, c3 = st.columns(3)
    N = c1.number_input("Degree", min_value=30, value=300, step=50, key="viz_N")
    prime = c2.number_input("p for p-adic valuation", min_value=2, value=5, step=1, key="viz_prime")
    modulus = c3.number_input("Heatmap modulus", min_value=2, value=5, step=1, key="viz_mod")
    max_stride = st.slider("Maximum progression stride", 2, 40, 15, key="viz_stride")
    if not st.button("Build visual analysis", type="primary", use_container_width=True, key="viz_run"):
        return
    try:
        coeffs = _integer_coefficients_for_external_tools(formula, int(N))
        import plotly.graph_objects as go
        tabs = st.tabs(["Coefficient plot", "p-adic valuations", "Congruence heatmap"])
        x = list(range(len(coeffs)))
        with tabs[0]:
            step = max(5, len(coeffs)//12)
            frames = [go.Frame(data=[go.Scatter(x=x[:end], y=coeffs[:end], mode="lines")], name=str(end)) for end in range(step, len(coeffs)+step, step)]
            fig = go.Figure(data=[go.Scatter(x=x[:step], y=coeffs[:step], mode="lines")], frames=frames)
            fig.update_layout(title="Animated coefficient growth", xaxis_title="n", yaxis_title="a(n)", updatemenus=[{"type":"buttons","buttons":[{"label":"Play","method":"animate","args":[None,{"frame":{"duration":180,"redraw":True},"fromcurrent":True}]}]}])
            st.plotly_chart(fig, use_container_width=True)
        with tabs[1]:
            vals = [p_adic_valuation(v, int(prime)) for v in coeffs]
            plot_vals = [None if v is None else v for v in vals]
            fig = go.Figure(go.Scatter(x=x, y=plot_vals, mode="markers"))
            fig.update_layout(title=rf"$p$-adic valuations for p={int(prime)}", xaxis_title="n", yaxis_title="ord_p(a(n))")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Zero coefficients are omitted because their p-adic valuation is infinite.")
        with tabs[2]:
            rows = list(range(2, int(max_stride)+1))
            cols = list(range(int(max_stride)))
            matrix = []
            hover = []
            for k in rows:
                row, hrow = [], []
                for r in cols:
                    if r >= k:
                        row.append(None); hrow.append("")
                        continue
                    subseq = coeffs[r::k]
                    rate = 100*sum(v % int(modulus) == 0 for v in subseq)/max(1, len(subseq))
                    row.append(rate)
                    hrow.append(f"k={k}, r={r}, {rate:.1f}% divisible")
                matrix.append(row); hover.append(hrow)
            fig = go.Figure(go.Heatmap(z=matrix, x=cols, y=rows, text=hover, hoverinfo="text", zmin=0, zmax=100, colorbar={"title":"% divisible"}))
            fig.update_layout(title=f"Finite divisibility heatmap modulo {int(modulus)}", xaxis_title="residue r", yaxis_title="stride k")
            st.plotly_chart(fig, use_container_width=True)
            st.warning("A 100% cell is finite computational evidence, not automatically a theorem.")
    except Exception as exc:
        st.error(f"Visualization failed: {exc}")


def explain_identity_text(item):
    p = item.get("p")
    return (
        f"This is a {p}-dissection: its right side separates powers of q according to residues modulo {p}. "
        "The automatic solver may scale it by replacing q with q^m, raise it to an integer power, and multiply it "
        "by factors already depending on q^p. The built-in coefficient audit checks the stored equality before it is used. "
        f"Provenance note: {item.get('source', 'not recorded')}."
    )


def open_identity_explanation(item):
    def body():
        st.latex(rf"{item['latex_lhs']}={item['latex_rhs']}")
        st.write(explain_identity_text(item))
        verification = verify_dissection_identity(item, 120)
        if verification.get("verified"):
            st.success("Independent coefficient audit passed through q^120.")
        else:
            st.error(f"Audit failed: {verification}")
    if hasattr(st, "dialog"):
        @st.dialog(f"Explain: {item.get('nice_name', item.get('name'))}")
        def _dialog():
            body()
        _dialog()
    else:
        with st.expander("Identity explanation", expanded=True):
            body()


IDENTITY_DB_PATH = os.path.join(DATA_DIR, "identity_vault.sqlite3")


def _vault_connect():
    conn = sqlite3.connect(IDENTITY_DB_PATH, timeout=20)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, salt TEXT NOT NULL, password_hash TEXT NOT NULL, created TEXT NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS identities (id INTEGER PRIMARY KEY AUTOINCREMENT, owner TEXT NOT NULL, name TEXT NOT NULL, p INTEGER, lhs TEXT NOT NULL, rhs TEXT NOT NULL, source TEXT, notes TEXT, created TEXT NOT NULL)")
    conn.commit()
    return conn


def _password_hash(password, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200000).hex()


def vault_register(username, password):
    username = username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,40}", username):
        raise ValueError("Username must contain 3-40 letters, numbers, dots, dashes, or underscores.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    salt = secrets.token_hex(16)
    with _vault_connect() as conn:
        conn.execute("INSERT INTO users(username,salt,password_hash,created) VALUES(?,?,?,?)", (username, salt, _password_hash(password, salt), _dt.datetime.utcnow().isoformat()))
    return username


def vault_login(username, password):
    with _vault_connect() as conn:
        row = conn.execute("SELECT salt,password_hash FROM users WHERE username=?", (username.strip(),)).fetchone()
    return bool(row and hmac.compare_digest(_password_hash(password, row[0]), row[1]))


def vault_list(owner):
    with _vault_connect() as conn:
        rows = conn.execute("SELECT id,name,p,lhs,rhs,source,notes,created FROM identities WHERE owner=? ORDER BY id DESC", (owner,)).fetchall()
    keys = ["id","name","p","lhs","rhs","source","notes","created"]
    return [dict(zip(keys,row)) for row in rows]


def run_identity_vault():
    st.title("🔐 Personal Identity Library")
    st.warning("On hosts without a persistent disk, saved accounts may disappear after a restart. Export your library JSON regularly.")
    if "vault_user" not in st.session_state:
        st.session_state.vault_user = None
    if not st.session_state.vault_user:
        login_tab, register_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            user = st.text_input("Username", key="vault_login_user")
            password = st.text_input("Password", type="password", key="vault_login_password")
            if st.button("Log in", key="vault_login_button", use_container_width=True):
                if vault_login(user, password):
                    st.session_state.vault_user = user.strip(); st.rerun()
                else:
                    st.error("Invalid credentials.")
        with register_tab:
            user = st.text_input("New username", key="vault_register_user")
            password = st.text_input("New password", type="password", key="vault_register_password")
            if st.button("Create account", key="vault_register_button", use_container_width=True):
                try:
                    vault_register(user, password)
                    st.success("Account created. Use the Log in tab.")
                except sqlite3.IntegrityError:
                    st.error("That username already exists.")
                except Exception as exc:
                    st.error(str(exc))
        return
    owner = st.session_state.vault_user
    top1, top2 = st.columns([3,1])
    top1.success(f"Logged in as {owner}")
    if top2.button("Log out", use_container_width=True):
        st.session_state.vault_user = None; st.rerun()
    with st.expander("Add a personal identity", expanded=True):
        name = st.text_input("Identity name", key="vault_name")
        p = st.selectbox("Dissection base", [2,3,5,7,11], key="vault_p")
        lhs = st.text_area("Left side", value=r"f_1^2", key="vault_lhs")
        rhs = st.text_area("Right side", value=r"\frac{f_2 f_8^5}{f_4^2f_{16}^2}-2q\frac{f_2f_{16}^2}{f_8}", key="vault_rhs")
        source = st.text_input("Source/reference", key="vault_source")
        notes = st.text_area("Notes", key="vault_notes")
        verify_degree = st.number_input("Verification degree", min_value=20, value=100, step=10, key="vault_verify")
        if st.button("Verify and save", type="primary", use_container_width=True, key="vault_save"):
            try:
                left = _core_expansion_engine(lhs, int(verify_degree)); right = _core_expansion_engine(rhs, int(verify_degree))
                mismatch = next((n for n,(a,b) in enumerate(zip(left,right)) if a != b), None)
                if mismatch is not None:
                    st.error(f"Identity not saved: first mismatch at q^{mismatch}.")
                else:
                    with _vault_connect() as conn:
                        conn.execute("INSERT INTO identities(owner,name,p,lhs,rhs,source,notes,created) VALUES(?,?,?,?,?,?,?,?)", (owner, name or "Unnamed identity", int(p), lhs, rhs, source, notes, _dt.datetime.utcnow().isoformat()))
                    st.success("Verified identity saved.")
            except Exception as exc:
                st.error(str(exc))
    records = vault_list(owner)
    st.subheader("Saved identities")
    if not records:
        st.info("No saved identities yet.")
    for record in records:
        with st.expander(f"{record['name']} · {record['p']}-dissection"):
            st.latex(rf"{record['lhs']}={record['rhs']}")
            st.write(record.get("source") or "No source entered.")
            if st.button("Delete", key=f"vault_delete_{record['id']}"):
                with _vault_connect() as conn:
                    conn.execute("DELETE FROM identities WHERE id=? AND owner=?", (record["id"], owner))
                st.rerun()
    export_data = json.dumps(records, indent=2)
    st.download_button("Export personal library JSON", export_data, file_name="ramanujan_identity_library.json", mime="application/json", use_container_width=True)
    uploaded = st.file_uploader("Import library JSON", type=["json"], key="vault_import")
    if uploaded and st.button("Import verified records", key="vault_import_button"):
        try:
            data = json.load(uploaded)
            count = 0
            with _vault_connect() as conn:
                for record in data:
                    lhs, rhs = record["lhs"], record["rhs"]
                    if _core_expansion_engine(lhs, 80) == _core_expansion_engine(rhs, 80):
                        conn.execute("INSERT INTO identities(owner,name,p,lhs,rhs,source,notes,created) VALUES(?,?,?,?,?,?,?,?)", (owner, record.get("name","Imported identity"), int(record.get("p",2)), lhs, rhs, record.get("source",""), record.get("notes",""), _dt.datetime.utcnow().isoformat()))
                        count += 1
            st.success(f"Imported {count} coefficient-verified identities.")
        except Exception as exc:
            st.error(f"Import failed: {exc}")


def encode_share_state(payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode().rstrip("=")


def decode_share_state(token):
    padding = "="*((4-len(token)%4)%4)
    return json.loads(zlib.decompress(base64.urlsafe_b64decode(token+padding)).decode())


def public_base_url():
    try:
        headers = dict(st.context.headers)
        host = headers.get("x-forwarded-host") or headers.get("host")
        proto = headers.get("x-forwarded-proto") or "https"
        if host:
            return f"{proto}://{host}/"
    except Exception:
        pass
    return ""


def apply_shared_state_once():
    if st.session_state.get("shared_state_applied"):
        return
    try:
        token = st.query_params.get("state")
    except Exception:
        token = None
    if not token:
        return
    try:
        payload = decode_share_state(token)
        module = payload.get("module")
        formula = payload.get("formula")
        p = payload.get("p")
        if module:
            st.session_state["main_menu"] = module
        if formula:
            for key in ["auto_dissection_input", "composite_input", "viz_formula", "op_formula"]:
                st.session_state.setdefault(key, formula)
        if p in [2,3,5,7,11]:
            st.session_state.setdefault("auto_p", p)
        st.session_state["shared_state_applied"] = True
        st.toast("Shared analysis state loaded.")
    except Exception as exc:
        st.session_state["shared_state_applied"] = True
        st.warning(f"The shared state could not be decoded: {exc}")


def run_share_link_studio():
    st.title("🔗 Shareable Analysis Links")
    modules = ["🧩 Automatic p-Dissection Solver", "🧪 Composite & Residue Dissection Lab", "⚙️ Hecke & Operator Sandbox", "📊 Visualization Studio"]
    module = st.selectbox("Destination module", modules, key="share_module")
    formula = st.text_area("Formula", value=r"\frac{f_1^2}{f_2}-\frac{f_1^6}{f_2^3}", height=90, key="share_formula")
    p = st.selectbox("p", [2,3,5,7,11], key="share_p")
    notes = st.text_input("Optional note", key="share_note")
    payload = {"module": module, "formula": formula, "p": int(p), "note": notes}
    token = encode_share_state(payload)
    relative = f"?state={token}"
    absolute = public_base_url()+relative if public_base_url() else relative
    st.code(absolute)
    st.link_button("Open shared state", relative, use_container_width=True)
    st.caption("The formula and options are compressed into the URL. No server-side account is needed.")


def compile_latex_pdf(tex_source):
    engine = shutil.which("pdflatex") or shutil.which("tectonic")
    if engine:
        with tempfile.TemporaryDirectory() as tmp:
            tex_path = os.path.join(tmp, "report.tex")
            with open(tex_path, "w", encoding="utf-8") as handle:
                handle.write(tex_source)
            if os.path.basename(engine).startswith("tectonic"):
                cmd = [engine, "report.tex"]
            else:
                cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "report.tex"]
            completed = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=60)
            pdf_path = os.path.join(tmp, "report.pdf")
            if completed.returncode == 0 and os.path.exists(pdf_path):
                return open(pdf_path, "rb").read(), completed.stdout[-4000:], "LaTeX engine"
            log = completed.stdout+"\n"+completed.stderr
    else:
        log = "No LaTeX engine is installed on this host."
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from xml.sax.saxutils import escape
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
        styles = getSampleStyleSheet()
        code_style = ParagraphStyle("WrappedCode", parent=styles["Code"], fontName="Courier", fontSize=7.2, leading=9, wordWrap="CJK")
        wrapped_source = escape(tex_source).replace("\n", "<br/>").replace(" ", "&nbsp;")
        story = [Paragraph("Ramanujan Laboratory Report", styles["Title"]), Spacer(1,12), Paragraph("LaTeX source (fallback rendering)", styles["Heading2"]), Paragraph(wrapped_source, code_style)]
        doc.build(story)
        return buffer.getvalue(), log, "ReportLab fallback"
    except Exception as exc:
        raise RuntimeError(f"PDF generation unavailable. {log} Fallback error: {exc}")


def run_report_studio():
    st.title("📄 LaTeX & PDF Report Studio")
    default_body = "\n\n".join(st.session_state.get("latex_clipboard", [])) or r"\[\frac{f_1^2}{f_2}=\frac{f_9^2}{f_{18}}-2q\frac{f_3f_{18}^2}{f_6f_9}.\]"
    body = st.text_area("Report body (LaTeX)", value=default_body, height=320, key="report_body")
    title = st.text_input("Report title", value="Ramanujan Laboratory Computation", key="report_title")
    tex = latex_document(title.replace("_", r"\_"), body)
    st.download_button("Download .tex", tex, file_name="ramanujan_report.tex", mime="text/x-tex", use_container_width=True)
    if st.button("Compile PDF", type="primary", use_container_width=True, key="report_compile"):
        try:
            pdf, log, method = compile_latex_pdf(tex)
            st.success(f"PDF created using {method}.")
            st.download_button("Download PDF", pdf, file_name="ramanujan_report.pdf", mime="application/pdf", use_container_width=True)
            with st.expander("Compiler log"):
                st.code(log or "No log output.")
        except Exception as exc:
            st.error(str(exc))


def _background_expand_task(formula, limit):
    started = time.time()
    coeffs = _core_expansion_engine(formula, int(limit))
    return {"formula": formula, "limit": int(limit), "coefficients": [str(c) for c in coeffs], "elapsed": time.time()-started}


@st.cache_resource
def get_background_executor():
    return concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="ramanujan")


def render_job_status():
    jobs = st.session_state.get("compute_jobs", {})
    if not jobs:
        st.info("No jobs in this browser session.")
        return
    for job_id, job in list(jobs.items()):
        future = job["future"]
        if future.done():
            try:
                result = future.result()
                st.success(f"{job_id}: completed in {result['elapsed']:.3f} seconds")
                st.download_button("Download coefficients JSON", json.dumps(result, indent=2), file_name=f"{job_id}.json", mime="application/json", key=f"job_download_{job_id}")
            except Exception as exc:
                st.error(f"{job_id}: failed — {exc}")
        else:
            st.info(f"{job_id}: running")


def run_compute_queue():
    st.title("🧵 Background Computation Queue")
    st.markdown("Submit a heavy expansion and continue using the page while the worker runs. Jobs are session-local and disappear if the server restarts.")
    formula = st.text_area("Formula", value=r"\frac{1}{f_1 f_3}", height=80, key="queue_formula")
    limit = st.number_input("Expansion degree", min_value=100, value=5000, step=500, key="queue_limit")
    if "compute_jobs" not in st.session_state:
        st.session_state.compute_jobs = {}
    if st.button("Submit expansion job", type="primary", use_container_width=True, key="queue_submit"):
        job_id = f"job-{len(st.session_state.compute_jobs)+1}-{int(time.time())}"
        future = get_background_executor().submit(_background_expand_task, formula, int(limit))
        st.session_state.compute_jobs[job_id] = {"future": future, "created": time.time()}
        st.success(f"Submitted {job_id}.")
    if hasattr(st, "fragment"):
        @st.fragment(run_every="2s")
        def _job_fragment():
            render_job_status()
        _job_fragment()
    else:
        render_job_status()
        if st.button("Refresh status", key="queue_refresh"):
            st.rerun()


def run_external_services():
    st.title("🌐 SageMath Bridge & REST API")
    st.markdown("The Streamlit app is fully usable without Sage. This page connects to optional companion services included in the deployment package.")
    sage_url = st.text_input("Sage bridge URL", value=os.getenv("SAGE_BRIDGE_URL", "http://localhost:8001"), key="sage_url")
    api_url = st.text_input("Ramanujan REST API URL", value=os.getenv("RAMANUJAN_API_URL", "http://localhost:8000"), key="api_url")
    c1, c2 = st.columns(2)
    if c1.button("Test Sage bridge", use_container_width=True):
        try:
            import requests
            data = requests.get(sage_url.rstrip("/")+"/health", timeout=5).json()
            st.success(data)
        except Exception as exc:
            st.error(f"Sage bridge unavailable: {exc}")
    if c2.button("Test REST API", use_container_width=True):
        try:
            import requests
            data = requests.get(api_url.rstrip("/")+"/health", timeout=5).json()
            st.success(data)
        except Exception as exc:
            st.error(f"REST API unavailable: {exc}")
    st.subheader("Sage dimension/Sturm query")
    a,b = st.columns(2)
    level = a.number_input("Level", min_value=1, value=11, key="sage_level")
    weight = b.number_input("Weight", min_value=1, value=2, key="sage_weight")
    if st.button("Ask Sage", use_container_width=True):
        try:
            import requests
            result = requests.post(sage_url.rstrip("/")+"/modular/dimension", json={"level":int(level),"weight":int(weight)}, timeout=20).json()
            st.json(result)
        except Exception as exc:
            st.error(f"Sage request failed: {exc}")
    st.info("FastAPI automatically exposes interactive API documentation at the companion service's /docs route.")


MANUAL_PAGES = [
("1. Orientation and reliability", r'''
## Purpose of the laboratory

Ramanujan Laboratory Pro is a research assistant for eta products, formal q-series, dissections, arithmetic progressions, modular-form certificates, and exploratory computation. The program is designed around a strict separation between three kinds of output.

**Exact symbolic output** is obtained by algebraic substitution from a verified identity. The app records every identity, scaling, power, and recombination. **Certified modular output** is obtained only after the eta-quotient hypotheses and the Sturm bound have been checked. **Computational evidence** is based on finitely many coefficients and is displayed as a conjectural or experimental result.

### First example
Enter
\[
F(q)=\frac{f_1^2}{f_2}-\frac{f_1^6}{f_2^3}
\]
in the Automatic p-Dissection Solver and select p=3. The app searches its verified identity library term by term, constructs the three residue components, checks the resulting equality by expanding both sides, and generates a proof trace in readable text and LaTeX.

### Navigation
The left menu is divided into exact algebra, modular certification, exploratory tools, external services, and documentation. Start with Home or the Automatic p-Dissection Solver. Use the Composite & Residue Lab when you need iterated progressions such as a(8n+7). Use the Sturm Certificate only when both sides are eta quotients of the same modular type.

### Reliability rule
A long successful coefficient check is not automatically a proof. It becomes a Sturm proof only when the app verifies the relevant modular-form hypotheses and checks through the exact bound. The manual repeats this distinction because it is the most important methodological safeguard in computational partition theory.
'''),
("2. Input notation and q-series engine", r'''
## Supported notation

The fundamental symbol is
\[
f_m=(q^m;q^m)_\infty.
\]
Write `f_1`, `f_{24}`, `f_1^3`, products, quotients, sums, and differences. Standard examples are
\[
\frac{1}{f_1f_3},\qquad \frac{f_2^5}{f_1^2f_4},\qquad f_1^2-f_2^2.
\]
The parser also supports selected theta functions such as `\varphi(q^2)`, `\psi(q^3)`, Ramanujan's general theta function, and the Rogers-Ramanujan auxiliary product used in the stored 5-dissections.

## Exact arithmetic
The coefficient engine uses rational arithmetic. Division is allowed only for formal power series with a nonzero constant term. Therefore expressions such as 1/f_1 are legitimate, while division by a series beginning with q is rejected.

## Truncation
A requested degree N means that calculations are performed modulo q^(N+1). Products and inverses are truncated consistently. When an operator needs a(pn), the engine automatically computes far enough to obtain the requested output degree.

## Safe evaluation
The LaTeX-like input is converted to a restricted expression tree. Arbitrary Python attributes, imports, and function calls are not allowed. This is important on a public webpage.

## Example
For 1/f_1, request degree 10. The app returns the partition numbers
\[
1,1,2,3,5,7,11,15,22,30,42.
\]
Use this simple test whenever you deploy a new version. It checks parsing, inversion, multiplication, and coefficient display simultaneously.
'''),
("3. Dissections and identity paths", r'''
## Meaning of a p-dissection
If F(q)=sum a(n)q^n, its p-dissection is
\[
F(q)=F_0(q^p)+qF_1(q^p)+\cdots+q^{p-1}F_{p-1}(q^p),
\]
where
\[
F_r(q)=\sum_{n\ge0}a(pn+r)q^n.
\]
The exact solver uses stored identities for p=2,3,5. Bases 7 and 11 are available through coefficient extraction even when no finite eta-product identity is stored.

## Step-by-step path
For each term, the app identifies a matching left side, records a possible scaling q -> q^m, raises the identity to the necessary power, multiplies by factors already depending on q^p, and then recombines all terms. Every step appears in the Derivation tab and in the LaTeX export.

## Example
The identity
\[
\frac{f_1^2}{f_2}=\frac{f_9^2}{f_{18}}-2q\frac{f_3f_{18}^2}{f_6f_9}
\]
is a 3-dissection. The first term contains only powers divisible by 3 and the second lies in residue 1. Thus the residue-2 component is zero.

## Identity explanation
In the verified library, press Explain identity. The dialog gives the role of the identity, the stored provenance note, and a fresh coefficient audit. For publication, replace generic provenance notes with the exact bibliographic equation number in your personal identity library.
'''),
("4. Composite expressions and deep extraction", r'''
## Sums and differences
The Composite & Residue Lab accepts finite linear combinations of eta monomials. This is essential for functions constructed as differences, where cancellation may create stronger congruences than either summand has separately.

## Direct extraction
For p=2, the components are a(2n) and a(2n+1). For p=3, they are a(3n), a(3n+1), and a(3n+2). Select the residue and inspect both the symbolic component and its coefficient check.

## Deep extraction
To obtain a(8n+7), write 7 in base 2:
\[
7=1+2+4=(111)_2.
\]
The app successively selects the odd component three times:
\[
a(2n+1)\longrightarrow a(4n+3)\longrightarrow a(8n+7).
\]
At every level it records the current generating function, the identity substitutions, and the selected digit.

## Product recognition
When no closed symbolic expression is found, the app computes the component coefficients and applies logarithmic derivatives and Möbius inversion. If the Euler exponents stabilize to a simple finite pattern, it proposes an f-product. This is a recognition step, not a proof, until the proposed identity is independently established.

## Practical advice
Use a moderate branch limit first. Large powers of multi-term dissections can grow exponentially. If the symbolic search becomes too large, use coefficient extraction to identify the likely simple component and then add a suitable identity to the personal library.
'''),
("5. Eta quotients, characters, and Sturm proofs", r'''
## Eta conversion
Because
\[
f_m=q^{-m/24}\eta(mz),
\]
an f-product has a q-shift that must be tracked. For an eta quotient product eta(delta z)^{r_delta}, the candidate weight is one half of the exponent sum.

## Modularity checks
At level N, the app verifies that every delta divides N and checks
\[
\sum_{\delta\mid N}\delta r_\delta\equiv0\pmod{24},\qquad
\sum_{\delta\mid N}\frac{N}{\delta}r_\delta\equiv0\pmod{24}.
\]
It then computes every cusp order using Ligozat's formula. Nonnegative orders give holomorphy; positive orders give cuspidality.

## Character
For an integral-weight eta quotient, the app displays the encoded quadratic character kernel D, corresponding to a Kronecker-symbol character. Two forms used in a Sturm congruence must have the same weight and character.

## Sturm certificate
The certificate module checks the hypotheses on both sides, confirms equal q-shifts, computes
\[
B=\left\lfloor \frac{k}{12}[SL_2(\mathbb Z):\Gamma_0(N)]\right\rfloor,
\]
and tests coefficients through B. Only then does it display Certified.

## Limitation
A progression a(pn+r) is not automatically a modular form on the original group. The app will not infer a Sturm proof for a progression merely from a finite extraction. Supply a proven modular representation of the extracted series first.
'''),
("6. Congruence mining and infinite families", r'''
## Finite searches
The Congruence Miner tests whether a(kn+r) is divisible by M through a chosen coefficient limit. Full sweeps examine all residues for a fixed stride. Hunter mode searches across strides and removes obvious subprogressions of earlier hits.

## Heatmaps
The Visualization Studio displays the percentage of tested coefficients divisible by M for many pairs (k,r). A cell at 100 percent is a useful signal but remains finite evidence.

## Infinite-family detection
The Infinite Family Miner looks for progressions whose steps and offsets fit geometric formulas. This pattern detection can suggest Tang-type or p-adic families. It does not prove induction in the exponent. A proof usually requires an operator matrix, modular equation, or recurrence.

## Recommended workflow
First generate enough terms to avoid accidental short patterns. Second filter trivial refinements. Third identify a plausible operator or dissection mechanism. Fourth prove the base case and recurrence. Finally use the app's LaTeX report to document the computational discovery separately from the proof.

## Example
If a function appears to satisfy a(5^alpha n + lambda_alpha) congruent to 0 modulo 5^alpha, use the miner to estimate lambda_alpha, then apply U_5 repeatedly in the Operator Sandbox and search for a stable finite-dimensional matrix action.
'''),
("7. Hecke operators, theta, rank, and crank", r'''
## U and V operators
For F=sum a(n)q^n,
\[
F\mid U_p=\sum a(pn)q^n,\qquad F\mid V_p=F(q^p).
\]
These operators are useful for progression extraction and oldform constructions.

## Integral-weight Hecke operator
For p not dividing the level,
\[
b(n)=a(pn)+\chi(p)p^{k-1}a(n/p).
\]
The app lets you enter k and chi(p). Terms with nonintegral n/p are treated as zero.

## Half-integral convention
The T(p^2) panel implements the displayed convention with an effective middle multiplier epsilon_p. Because authors normalize the character factor differently, copy the formula from the panel and verify that it matches the convention in your source before using it in a paper.

## Theta operator
Theta=q d/dq sends a(n) to n a(n). Iterating it produces n^r a(n), useful for weighted partition statistics and modular congruences.

## Rank and crank moments
The Moment Lab expands the standard two-variable rank and crank generating functions and computes even moments. Select Crank minus rank to explore smallest-parts-type differences. The current implementation is intended for moderate N because bivariate expansion is more expensive than ordinary q-series multiplication.
'''),
("8. Relations, OEIS, and visual exploration", r'''
## Exact and LLL relations
Enter several series of the same expected modular type. The app forms a coefficient matrix. Rational nullspace gives exact relations at the selected truncation; LLL searches for short integer combinations. Increase the precision to reject accidental relations.

A useful application is basis recognition. If a modular-form space has known dimension d and you enter more than d candidate eta quotients, the relation finder can reveal dependencies.

## OEIS
The OEIS module sends only the integer coefficient list, not the formula. A match can suggest a known combinatorial interpretation or reference. Initial terms can be shifted or normalized before searching by editing the displayed list in a future extension; currently the search uses the coefficients beginning at n=0.

## Coefficient plots
The animated plot shows growth and sign changes. The p-adic plot shows ord_p(a(n)); zero coefficients are omitted because their valuation is infinite. The heatmap is effective for spotting residue classes.

## Caution
OEIS matches and LLL relations are discovery tools. Confirm index shifts, signs, normalizations, and enough additional coefficients before drawing mathematical conclusions.
'''),
("9. Saving, sharing, PDF, jobs, API, and Sage", r'''
## Personal identity vault
Create a username and password, verify an identity, and save it with source notes. Passwords are stored as salted PBKDF2 hashes. On ephemeral free hosting, the SQLite file can disappear after a restart, so export JSON frequently. A persistent disk is recommended for a public multiuser deployment.

## Share links
The Share Link Studio compresses the formula and selected options into a URL query parameter. Opening the link restores the corresponding module and formula without creating an account.

## PDF reports
The Report Studio first looks for pdflatex or Tectonic. The Docker deployment installs a LaTeX engine. If no engine is available, the app produces a fallback PDF containing the LaTeX source.

## Background jobs
Large expansions can run in a thread pool. Jobs are tied to the current browser session and server process; they are not a durable distributed queue. For production-scale computation, replace this layer with Redis and a worker system.

## REST API
The included FastAPI service exposes health, expansion, dissection, and congruence-check endpoints. Interactive documentation is available at /docs.

## Sage bridge
The optional Sage service computes modular-form dimensions and Sturm bounds using SageMath. Set SAGE_BRIDGE_URL to its address. The main app remains functional when the bridge is offline.
'''),
("10. Complete worked workflow and troubleshooting", r'''
## Worked workflow
Consider
\[
F(q)=\frac18\left(\frac{f_2}{f_1^2}-\frac{f_1^6}{f_2^3}\right).
\]
First enter the expression in the Automatic p-Dissection Solver with p=3. Export the exact derivation if available. Next open the Composite Lab and inspect each residue. If a component appears to vanish modulo a prime, run a higher coefficient check and visualize its p-adic valuations. If you obtain a simple eta quotient for the component, verify its level, weight, character, and cusp orders. Construct a same-space modular congruence and use the Sturm Certificate. Finally save the proven identity in the personal vault and generate a PDF report.

## Common errors
`unsupported operand type` usually indicates an expression was sent to a pure eta-product parser instead of the linear-combination parser; the current dissection pages use the correct parser. `Series is not invertible` means the denominator has zero constant term. A failed Newman condition means the proposed eta quotient is not certified on that level by the implemented theorem. A blank OEIS or Sage result usually means the external service is unavailable.

## Deployment
For Streamlit Community Cloud, upload app.py, requirements.txt, packages.txt, and the .streamlit directory. For the complete app plus REST API and LaTeX engine, use Docker Compose. For persistent identities, mount a volume at RAMANUJAN_DATA_DIR.

## Research discipline
Keep generated conjectures, computational verifications, and proofs in separate sections of your notes. Record the coefficient limit and software version for every experiment. Re-run important identities at higher precision before submission. The app's main purpose is not only speed, but transparent reproducibility.
''')
]


_MANUAL_EXTRA = [
    r'''### Operational checklist
Before trusting an output, record the formula exactly, the selected truncation degree, the dissection base, and the application version shown in the sidebar. Re-run the calculation after clearing the cache when a formula has been edited substantially. For an exact result, open the derivation tab and confirm that every stored identity is appropriate for the scale used. For a certified result, inspect the modularity table rather than relying only on the green status message. For an experimental result, export both the coefficient list and the conjectured formula so the computation can be reproduced independently.

The app is intended to shorten routine algebra, not to replace mathematical judgment. A clean workflow is: discovery, independent verification, theorem selection, proof construction, and final exposition. The same formula may pass through several modules during these stages.''',
    r'''### Parsing examples and diagnostics
Implicit multiplication is supported in standard eta-product notation, but unambiguous input is always better. Prefer `f_1^2*f_3` when debugging a difficult expression. Fractions should use complete braces, for example `\\frac{f_2^5}{f_1^2 f_4}`. If the parser reports an unknown symbol, remove decorative LaTeX commands and test the smallest subexpression first.

A useful diagnostic sequence is to compare the first coefficients with a trusted computer algebra system. Test `f_1`, `1/f_1`, and the proposed expression separately. When a denominator is present, check its constant coefficient. The formal inverse exists only when that coefficient is nonzero. Exact rational coefficients are retained throughout, so a nonintegral output is not silently rounded. External tools such as OEIS require integral coefficients and will stop with an explanatory message otherwise.''',
    r'''### How to add a new dissection safely
First enter the proposed identity in the Personal Identity Library and verify it to a reasonably high degree. Add a precise source: author, paper or book, equation number, and any notation conversion. Next test one or two scaled versions q -> q^m. Finally compare the extracted residue components directly. Only after these checks should the identity be promoted into the built-in library.

For p=7 or 11, the app always provides coefficient components. A finite closed form may involve auxiliary theta functions rather than eta products alone. In that case, use the coefficient output to determine the shape, add the required special function to the parser, and store the exact source identity. Avoid forcing a large component into an artificial eta quotient merely because a short coefficient fit exists.''',
    r'''### Deep-extraction example
Suppose the first odd extraction is G_1(q), the odd extraction of G_1 is G_2(q), and the odd extraction of G_2 is zero. Then the original series has a(8n+7)=0 identically. The derivation report records this as three applications of the 2-dissection operator, not as one unexplained leap.

For a general residue r modulo p^d, read the base-p digits from least significant to most significant. At level j, select the component indexed by the j-th digit. This order is important because the first extraction acts on the original index. The app displays the digit path and the corresponding progression after every stage. When an exact stage fails, the remaining coefficient extraction is still shown, but the proof trace ends at the last justified symbolic identity.''',
    r'''### Choosing a level
For an eta quotient, begin with the least common multiple of all eta subscripts, but do not assume it is automatically the optimal modular level. The Newman congruences may fail at that level and hold after multiplication by an auxiliary eta quotient or after increasing the level. The Eta-Multiplier Lab searches for pole-clearing and congruence-correcting factors, while displaying the resulting weight and Sturm cost.

A small Sturm bound is convenient but not the only objective. Prefer a multiplier that preserves the intended arithmetic progression and yields a character compatible with the comparison form. The app's search is combinatorial within chosen exponent bounds; it does not prove that no multiplier exists outside those bounds. Record the search range whenever a negative result is used to guide further work.''',
    r'''### Turning a pattern into a theorem
After the miner finds a progression, verify it at a substantially larger limit than the discovery limit. Examine neighboring residues to understand whether the result is isolated or part of a larger dissection. Apply U_p or repeated extraction to search for a recurrence. If a finite-dimensional space appears, use the Relation Finder to identify a basis and compute the operator matrix.

For an infinite family modulo p^alpha, the key step is usually an induction mechanism: a matrix whose entries gain p-adic valuation, a modular equation, or an explicit recurrence between extracted generating functions. The app can discover the likely matrix entries and test valuations, but the final proof should state why the recurrence holds for every alpha and why the initial vector has the required divisibility.''',
    r'''### Operator conventions
Before using a Hecke output in a manuscript, write the operator definition explicitly. Normalizations differ between sources, particularly in half-integral weight. The sandbox therefore displays the exact coefficient law used. Compare it with the theorem you intend to cite, including the placement of the character and the power of p.

A practical eigenform test is to compute T_p F for several primes not dividing the level, then use the Relation Finder to compare T_p F with F. If the space is one-dimensional and F is normalized, proportionality strongly suggests the eigenvalue a(p); a rigorous statement still depends on the modular-form membership and the dimension calculation. The Sage bridge can supply the dimension when available.''',
    r'''### Interpreting matches
An OEIS match may begin at a different offset, omit an initial zero, or use a sign convention. Read the entry carefully and compare more terms. Similarly, an LLL relation may be numerically short because the selected coefficient window is too small. Increase the degree and verify the relation using exact arithmetic.

Visualizations are most useful for questions that are difficult to see in a raw list: sudden growth, systematic zeros, periodic valuation spikes, or families of residue classes. Use the heatmap to formulate a precise candidate, then return to the Congruence Miner for the exact failing indices. Export plots for exploration, but base the proof on symbolic identities or modular certification rather than on visual appearance.''',
    r'''### Deployment choices
Streamlit Community Cloud is the simplest option for the main interface, but its filesystem is ephemeral and system-level LaTeX availability can vary. Docker Compose gives the complete experience: web app, REST API, TeX engine, and a persistent data volume. The Sage bridge is optional because its image is much larger.

For a public installation, set memory and coefficient limits conservatively. Background threads share the same process and memory. Use a reverse proxy with HTTPS, keep dependencies updated, and avoid placing secrets in the repository. The identity vault is a lightweight research convenience, not an institutional authentication system. For a multiuser production service, connect it to a managed database and established login provider.''',
    r'''### Final reproducibility checklist
A complete computational record should contain the input formula, notation definitions, coefficient limit, modulus, progression, identities used, source references, software version, and date. For a Sturm proof, include the level, weight, character, cusp orders, index, and exact bound. For a dissection proof, include the scaled identities and coefficient-extraction rule.

When troubleshooting deployment, first run `python -m py_compile app.py`, then start Streamlit locally, then test the health endpoint. For API problems, open `/docs` and submit a small expansion. For Sage problems, test `/health` and confirm that the service is running under Sage's Python rather than ordinary Python. These checks isolate syntax, dependency, web, and mathematical-service failures in a systematic order.'''
]
MANUAL_PAGES = [(title, content + "\n\n" + extra) for (title, content), extra in zip(MANUAL_PAGES, _MANUAL_EXTRA)]


def manual_markdown_document():
    parts = ["# Ramanujan Laboratory Pro — Research Manual\n"]
    for title, content in MANUAL_PAGES:
        parts.append(f"\n# {title}\n{content.strip()}\n")
    return "\n".join(parts)


def _manual_escape_text(text):
    text = text.replace("–", "-").replace("—", "-").replace("→", " to ")
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def _manual_inline_latex(text):
    replacements = []

    def reserve(kind, value):
        token = f"ZZ{kind}{len(replacements)}ZZ"
        replacements.append((token, kind, value))
        return token

    text = re.sub(r"`([^`]+)`", lambda m: reserve("CODE", m.group(1)), text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: reserve("BOLD", m.group(1)), text)
    text = _manual_escape_text(text)
    for token, kind, value in replacements:
        escaped_token = _manual_escape_text(token)
        escaped_value = _manual_escape_text(value)
        if kind == "CODE":
            latex = r"\texttt{" + escaped_value + "}"
        else:
            latex = r"\textbf{" + escaped_value + "}"
        text = text.replace(escaped_token, latex)
    return text


def _manual_markdown_to_latex(content):
    output = []
    in_math = False
    in_items = False
    paragraph = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            output.append(_manual_inline_latex(" ".join(x.strip() for x in paragraph)))
            output.append("")
            paragraph = []

    def close_items():
        nonlocal in_items
        if in_items:
            output.append(r"\end{itemize}")
            output.append("")
            in_items = False

    for raw_line in content.strip().splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if in_math:
            output.append(line)
            if stripped == r"\]":
                in_math = False
            continue
        if stripped == r"\[":
            flush_paragraph()
            close_items()
            output.append(line)
            in_math = True
            continue
        if not stripped:
            flush_paragraph()
            close_items()
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            close_items()
            output.append(r"\subsubsection*{" + _manual_inline_latex(stripped[4:]) + "}")
        elif stripped.startswith("## "):
            flush_paragraph()
            close_items()
            output.append(r"\subsection*{" + _manual_inline_latex(stripped[3:]) + "}")
        elif stripped.startswith("- "):
            flush_paragraph()
            if not in_items:
                output.append(r"\begin{itemize}")
                in_items = True
            output.append(r"\item " + _manual_inline_latex(stripped[2:]))
        else:
            paragraph.append(line)
    flush_paragraph()
    close_items()
    return "\n".join(output)


def manual_latex_document():
    body = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{amsmath,amssymb,geometry,hyperref}",
        r"\geometry{margin=1in}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{0.55em}",
        r"\sloppy",
        r"\title{Ramanujan Laboratory Pro: Research Manual}",
        r"\date{}",
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\newpage",
    ]
    for title, content in MANUAL_PAGES:
        body.append(r"\section{" + _manual_inline_latex(title) + "}")
        body.append(_manual_markdown_to_latex(content))
        body.append(r"\newpage")
    body.append(r"\end{document}")
    return "\n".join(body)


@st.cache_data
def manual_pdf_bytes():
    pdf, _log, _method = compile_latex_pdf(manual_latex_document())
    return pdf

def run_manual():
    st.title("📘 Ten-Page Research Manual")
    st.markdown("Use the page selector to read the manual inside the app. Each page contains a worked explanation and operational cautions.")
    titles = [title for title,_ in MANUAL_PAGES]
    selected = st.selectbox("Manual page", titles, key="manual_page")
    idx = titles.index(selected)
    title, content = MANUAL_PAGES[idx]
    st.markdown(f"## {title}")
    st.markdown(content)
    left, middle, right = st.columns(3)
    left.download_button("Download manual (.md)", manual_markdown_document(), file_name="ramanujan_lab_manual.md", mime="text/markdown", use_container_width=True)
    middle.download_button("Download manual (.tex)", manual_latex_document(), file_name="ramanujan_lab_manual.tex", mime="text/x-tex", use_container_width=True)
    right.download_button("Download manual (.pdf)", manual_pdf_bytes(), file_name="ramanujan_lab_manual.pdf", mime="application/pdf", use_container_width=True)
    st.progress((idx+1)/len(MANUAL_PAGES), text=f"Page {idx+1} of {len(MANUAL_PAGES)}")



# Backward-compatible strategist now delegates to the exact solver.
def run_strategy_suggestor():
    run_auto_dissection()


# ==========================================
# --- WEB HOME / QUICK START ---
# ==========================================
def run_home_page():
    st.markdown("## Mathematical workspace")
    st.markdown(
        "Use the menu on the left to open a laboratory. Every exact dissection is accompanied "
        "by a verification status, an identity path, and copyable LaTeX whenever available."
    )

    st.markdown(
        """
        <div class="home-grid">
          <div class="home-card"><h3>🧩 Automatic p-Dissection</h3><p>Enter an eta product, sum, or difference and request a 2-, 3-, or supported 5-dissection.</p></div>
          <div class="home-card"><h3>🧪 Composite & Residue Lab</h3><p>Extract a(2n+1), a(3n+2), a(8n+7), and other progressions with an explicit derivation path.</p></div>
          <div class="home-card"><h3>📚 Verified Identity Library</h3><p>Browse the stored dissection identities, inspect coefficient audits, and export the whole library as LaTeX.</p></div>
          <div class="home-card"><h3>🛡️ Eta-Multiplier Lab</h3><p>Check modularity congruences, cusp orders, weights, characters, and pole-clearing multipliers.</p></div>
          <div class="home-card"><h3>⛏️ Congruence Miner</h3><p>Search finite coefficient data for candidate arithmetic progressions, clearly separated from rigorous proofs.</p></div>
          <div class="home-card"><h3>🌀 Euler Product Explorer</h3><p>Use logarithmic-derivative and Möbius inversion data to recognize simple product structures.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("### Quick start")
        st.markdown(
            r"""
1. Open **Automatic p-Dissection Solver** or **Composite & Residue Dissection Lab**.
2. Enter a supported expression, for example
   \[
   \frac{f_1^2}{f_2}-\frac{f_1^6}{f_2^3}.
   \]
3. Choose \(p=2\) or \(p=3\), then run the analysis.
4. Open **Derivation path** to see every identity and substitution.
5. Copy the generated LaTeX or download the standalone report.
            """
        )
    with right:
        st.markdown("### Supported notation")
        st.code(
            """f_1, f_{24}, f_1^3
\\frac{f_2^5}{f_1^2 f_4}
\\varphi(q^2), \\psi(q^3)
f(q,q^5), G(q), H(q), R(q)""",
            language="latex",
        )
        st.caption("Expressions are parsed through a restricted mathematical evaluator; arbitrary Python code is not executed.")


    st.markdown("### Extended research tools")
    st.markdown(
        """
        <div class="home-grid">
          <div class="home-card"><h3>✅ Sturm Certificates</h3><p>Issue a proof badge only after weight, level, character, cusp orders, q-shift, and the exact bound agree.</p></div>
          <div class="home-card"><h3>⚙️ Operators & Moments</h3><p>Apply U, V, integral and half-integral Hecke operators, theta derivatives, and rank/crank moment expansions.</p></div>
          <div class="home-card"><h3>🧮 Relations & OEIS</h3><p>Find exact nullspace or short LLL relations and optionally identify integer sequences through OEIS.</p></div>
          <div class="home-card"><h3>📊 Visual Studio</h3><p>Animate coefficients, inspect p-adic valuations, and scan congruence residue classes with heatmaps.</p></div>
          <div class="home-card"><h3>🔐 Reproducible Workspace</h3><p>Save verified identities, create share links, compile reports, and export a complete research record.</p></div>
          <div class="home-card"><h3>🌐 API & Sage Bridge</h3><p>Call the q-series engine from notebooks or connect an optional SageMath service for dimensions and Sturm bounds.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Reliability labels")
    c1, c2, c3 = st.columns(3)
    c1.success("Exact identity path — symbolic transformation with independent coefficient checking.")
    c2.info("Coefficient identity — verified through the selected truncation order.")
    c3.warning("Candidate congruence — finite evidence only until a proof certificate is supplied.")

    with st.expander("Deployment and privacy notes"):
        st.markdown(
            "The application performs its calculations on the server hosting the webpage. "
            "The core calculations stay on the hosting server. The optional OEIS module sends only the displayed integer coefficient list to OEIS; it does not send the original formula. Cached expansions are stored in the host's temporary cache directory and may disappear when the service restarts."
        )

# ==========================================
# --- MASTER NAVIGATION CONTROLLER ---
# ==========================================
apply_shared_state_once()

MENU_OPTIONS = [
    "🏠 Home",
    "🧩 Automatic p-Dissection Solver",
    "🧪 Composite & Residue Dissection Lab",
    "📚 Verified Dissection Library",
    "🛡️ Correct Eta-Multiplier Lab",
    "✅ Sturm Certificate",
    "⚙️ Hecke & Operator Sandbox",
    "📐 Rank/Crank & Theta Moments",
    "🧮 Exact / LLL Relation Finder",
    "⛏️ Congruence Miner",
    "♾️ Infinite Family Miner",
    "🌀 Euler Product Explorer",
    "📊 Visualization Studio",
    "🔎 OEIS Lookup",
    "🔐 Personal Identity Library",
    "🔗 Share Link Studio",
    "📄 LaTeX & PDF Reports",
    "🧵 Background Compute Queue",
    "🌐 Sage & REST Services",
    "📘 Ten-Page Manual",
]
if st.session_state.get("main_menu") not in MENU_OPTIONS:
    st.session_state["main_menu"] = "🏠 Home"

st.sidebar.title("🧭 Research Suite")
st.sidebar.caption(f"{APP_VERSION} · public web build")
app_mode = st.sidebar.selectbox("Select Application Module:", MENU_OPTIONS, key="main_menu")

# --- GLOBAL CLIPBOARD & CACHE UI ---
st.sidebar.markdown("---")
st.sidebar.subheader("📋 System Controls")

col_clip, col_cache = st.sidebar.columns(2)
with col_clip:
    if st.button("🗑️ Clear Clipboard"):
        st.session_state.latex_clipboard = []
        st.rerun()
        
with col_cache:
    if st.button("🧹 Clear All Cache"):
        st.session_state.smart_ram_cache = {}
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR, exist_ok=True)
        st.cache_data.clear()
        st.success("Cache completely wiped!")
        time.sleep(1)
        st.rerun()

st.sidebar.divider()
if st.session_state.latex_clipboard:
    combined_latex = "\n\n".join(st.session_state.latex_clipboard)
    st.sidebar.info("Use the copy icon in the code block or open the PDF Report Studio.")
    st.sidebar.code(combined_latex, language="latex")
else:
    st.sidebar.info("Clipboard is empty. Run an analysis to collect LaTeX here.")
st.sidebar.divider()

ROUTES = {
    "🏠 Home": run_home_page,
    "🧩 Automatic p-Dissection Solver": run_auto_dissection,
    "🧪 Composite & Residue Dissection Lab": run_composite_dissection_lab,
    "📚 Verified Dissection Library": run_dissection_dictionary,
    "🛡️ Correct Eta-Multiplier Lab": run_eta_multiplier,
    "✅ Sturm Certificate": run_sturm_verifier,
    "⚙️ Hecke & Operator Sandbox": run_operator_sandbox,
    "📐 Rank/Crank & Theta Moments": run_moment_lab,
    "🧮 Exact / LLL Relation Finder": run_relation_finder,
    "⛏️ Congruence Miner": run_congruence_miner,
    "♾️ Infinite Family Miner": run_infinite_family_miner,
    "🌀 Euler Product Explorer": run_euler_explorer,
    "📊 Visualization Studio": run_visualization_studio,
    "🔎 OEIS Lookup": run_oeis_lookup,
    "🔐 Personal Identity Library": run_identity_vault,
    "🔗 Share Link Studio": run_share_link_studio,
    "📄 LaTeX & PDF Reports": run_report_studio,
    "🧵 Background Compute Queue": run_compute_queue,
    "🌐 Sage & REST Services": run_external_services,
    "📘 Ten-Page Manual": run_manual,
}
ROUTES[app_mode]()

st.markdown(
    f'<div class="app-footer">Ramanujan Laboratory Pro · {APP_VERSION} · Exact q-series arithmetic in the browser</div>',
    unsafe_allow_html=True,
)
