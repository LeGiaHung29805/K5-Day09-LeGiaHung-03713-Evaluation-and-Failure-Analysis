"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb
from numbers import Integral

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge labels must have the same length")
    counts = dict.fromkeys(("tp", "fp", "fn", "tn"), 0)
    for expected, predicted in zip(human, judge):
        if expected not in ("PASS", POS) or predicted not in ("PASS", POS):
            raise ValueError("labels must be PASS or FAIL")
        if predicted == POS:
            counts["tp" if expected == POS else "fp"] += 1
        else:
            counts["fn" if expected == POS else "tn"] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    counts = confusion(human, judge)
    tp = counts["tp"]
    return tp / (tp + counts["fp"] or 1), tp / (tp + counts["fn"] or 1)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    counts = confusion(human, judge)
    tp, fp, fn, tn = (counts[key] for key in ("tp", "fp", "fn", "tn"))
    n = len(human)
    expected = (tp + fn) * (tp + fp) + (tn + fp) * (tn + fn)
    if expected == n * n:
        raise ValueError("Cohen's kappa is undefined when expected agreement is 1")
    return (n * (tp + tn) - expected) / (n * n - expected)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    if not all(0 <= p <= 1 for p in (observed_rate, sensitivity, specificity)):
        raise ValueError("rates must be in [0, 1]")
    informedness = sensitivity + specificity - 1
    if informedness == 0:
        raise ValueError("Rogan–Gladen is undefined when sensitivity + specificity = 1")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / informedness))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    left, right = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if left.ndim != 1 or right.shape != left.shape or not left.size:
        raise ValueError("bootstrap requires equal, non-empty one-dimensional samples")
    if not np.isfinite(left).all() or not np.isfinite(right).all():
        raise ValueError("bootstrap requires finite samples")
    delta = float(np.mean(left - right))
    if np.array_equal(left, right) or left.size == 1:
        return delta, delta, delta

    def mean_difference(x, y, axis):
        return np.mean(x - y, axis=axis)

    interval = bootstrap((left, right), mean_difference, paired=True, method="percentile",
                         n_resamples=n_resamples, confidence_level=confidence,
                         rng=np.random.default_rng(rng)).confidence_interval
    return delta, float(interval.low), float(interval.high)


def _validate_trials(n: int, c: int, k: int) -> None:
    if any(isinstance(x, bool) or not isinstance(x, Integral) for x in (n, c, k)):
        raise ValueError("n, c and k must be integers")
    if not (0 <= c <= n and 1 <= k <= n):
        raise ValueError("require 0 <= c <= n and 1 <= k <= n")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_trials(n, c, k)
    total = comb(n, k)
    return (total - comb(n - c, k)) / total


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_trials(n, c, k)
    return comb(c, k) / comb(n, k)
