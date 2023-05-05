import functools

import matplotlib as mpl
import numpy as np
import scipy.stats as st
import seaborn as sns
from matplotlib import pyplot as plt

from common import *

QUANTS = [0.25, 0.5, 0.75]
C = 0.75
ALPHA = 0.05


def binom_test_entry(test2, slow, fast, adv, quant):
    tf = ((test2[fast] * adv) < test2[slow]).value_counts()
    if tf.empty:
        return np.nan
    res = st.binomtest(tf.get(True, 0), tf.sum())
    if res.statistic >= quant:
        return res.pvalue
    else:
        return np.nan


def binom_test_column(test2, col):
    quant, slow = col.name
    return pd.Series({
        fast: binom_test_entry(test2, slow, fast, adv, quant)
        for fast, adv in col.items()
    }, dtype="float")


cm = mpl.colors.LinearSegmentedColormap.from_list("conf", mpl.colormaps['Blues']([1.0, 0.25]))
cm.set_over("white")

cols = [f"{mode}.stats.time_ns" for mode in modes]
for mode in modes:
    df[f"{mode}.stats.time_ns"] = df[mode].apply(lambda doc: p(doc, "stats.time_ns")).fillna(60 * 60 * 1e9)

SETS = {
    "s": (df[xcol] <= 5000),
    "m": (df[xcol] > 5000) & (df[xcol] <= 50000),
    "l": (df[xcol] > 50000),
    "ml": (df[xcol] > 5000),
    "a": (slice(None))
}

for sname, selection in SETS.items():
    # sname, selection = "ml", (df[xcol] > 5000)
    test = df[selection]
    test1, test2 = test.iloc[:len(test) // 2], test.iloc[len(test) // 2:]
    print(f"Binom Test {sname}: {len(test1)}+{len(test2)}={len(test)}")

    advs = pd.DataFrame([
        (fast, slow, *test1[slow].div(test1[fast]).quantile([1 - q for q in QUANTS]))
        for fast in cols for slow in cols
    ], columns=["fast", "slow", *QUANTS])
    advs = advs.pivot(index="fast", columns="slow", values=QUANTS)
    advs = (advs * C).clip(lower=1)  # , upper=2)
    advs.sort_index(key=lambda cs: [col_idx(c) for c in cs], inplace=True)
    advs.sort_index(key=lambda cs: [col_idx(c) for c in cs], inplace=True, axis=1, level=1)
    advs.sort_index(kind='stable', sort_remaining=False, inplace=True, axis=1, level=0)
    binres = advs.apply(functools.partial(binom_test_column, test2))

    advs.rename(get_label, axis=1, level=1, inplace=True)
    advs.rename(get_label, axis=0, inplace=True)
    binres.rename(get_label, axis=1, level=1, inplace=True)
    binres.rename(get_label, axis=0, inplace=True)

    fig, axs = plt.subplots(1, len(QUANTS), sharey=True)
    for quant, ax in zip(QUANTS, axs):
        # ax = None; quant = 0.5
        ax = sns.heatmap(
            binres.loc[:, (quant,)], annot=advs.loc[:, (quant,)],
            vmin=0.0, vmax=ALPHA, cmap=cm, square=True,
            ax=ax, cbar=False,  # cbar=(ax == axs[-1]),
            xticklabels=True, yticklabels=True, linewidths=0.5, linecolor="lightgray"
        )
        ax.set_xlabel(f"q = {quant}")
        for o in ax.findobj():
            o.set_clip_on(False)
        ax.figure.tight_layout()

    fig.set_size_inches(20, 8)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/{name}-stats-time_ns-{sname}.pdf")
    fig.clear()
