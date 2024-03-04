import functools

import matplotlib as mpl
import numpy as np
import pandas as pd
import scipy.stats as st
import seaborn as sns
from matplotlib import pyplot as plt

# %%
ALL_DATASETS = False

if ALL_DATASETS:
    import warnings
    from tqdm import tqdm
    from common_db import *
    from common_utils import *

    warnings.filterwarnings("ignore", category=UserWarning, message="The markers list has more values")
    mpl.rcParams['savefig.dpi'] = 300

    modes = None
    xcol = "xcol"
    name = "all-large"


    def load_dataset(index_file, coll_name):
        global modes
        df = pd.read_csv(index_file)
        modes = set()
        for doc in tqdm(db[coll_name].find(), file=sys.stdout):
            if doc["mode"] not in modes:
                modes.add(doc["mode"])
                df[doc["mode"]] = [{}] * len(df)
            file_nr = int(doc["file_nr"])
            if df.at[file_nr, "file"] == doc["file"]:
                df.at[file_nr, doc["mode"]] = doc
            else:
                file_nrs = df.loc[df["file"] == doc["file"].lstrip("./"), "nr"]
                print(
                    f"{doc['mode']} document claims file_nr {file_nr} for file {doc['file']}, but index says {file_nrs}")
                if len(file_nrs) == 1:
                    df.at[file_nrs.iat[0], doc["mode"]] = doc
        if 'cluster-crossing' in df:
            df["xcol"] = df['cluster-crossing']
        else:
            df["xcol"] = df["pipe-total-deg"]
        return df


    df = pd.concat([
        load_dataset("index-clusters-large.csv", "stats-clusters-large"),
        load_dataset("index-instances-pq.csv", "stats-instances-pq"),
        load_dataset("index-instances-sefe.csv", "stats-instances-sefe"),
    ])

else:
    from common import *

# %%


QUANTS = [0.25, 0.5, 0.75]  # faster for what percentage of the dataset
C = 0.75  # dampening of advantages learned from the training set
ALPHA = 0.05  # confidence interval


def binom_test_entry(test2, slow, fast, adv, quant):
    tf = ((test2[fast] * adv) < test2[slow]).value_counts()
    if tf.empty:
        return np.nan
    res = st.binomtest(tf.get(True, 0), tf.sum(), quant, alternative="greater")
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

MODES = {
    # "a": (cols,) * 2,
    "b": ([f"{s}.stats.time_ns" for s in [
        'PQPlanarity-c-i',
        'PQPlanarity-c-i-a',
        'PQPlanarity-c-i-r',
        'PQPlanarity-c-i-b',
        'PQPlanarity-c-i-b-s',
        'PQPlanarity-i',
        'PQPlanarity-c',
    ]],) * 2,
    "s": ([f"{s}.stats.time_ns" for s in [
        "PQPlanarity-c-i",
        "PQPlanarity-p-c-i",
        "PQPlanarity-p-i",
        "PQPlanarity-p-c",
        "PQPlanarity-p",
    ]],) * 2
}

SETS = {
    # "xs": (df[xcol] <= 1000),
    "s": (df[xcol] <= 5000),
    # "m": (df[xcol] > 5000) & (df[xcol] <= 50000),
    # "l": (df[xcol] > 50000),
    "ml": (df[xcol] > 5000),
    # "a": (df[xcol] > -1)
}

for mname, (fastcols, slowcols) in MODES.items():
    for sname, selection in SETS.items():
        # mname = "b"; sname = "ml"; fastcols, slowcols = MODES[mname]; selection = SETS[sname]
        test = df[selection]
        test1, test2 = test[test["nr"] % 2 == 0], test[test["nr"] % 2 == 1]
        print(f"Binom Test {mname} {sname}: {len(test1)}+{len(test2)}={len(test)}")

        advs = pd.DataFrame([
            (fast, slow, *test1[slow].div(test1[fast]).quantile([1 - q for q in QUANTS]))
            for fast in fastcols for slow in slowcols
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
            ax.set_xlabel(f"p = {quant}")
            for o in ax.findobj():
                o.set_clip_on(False)
            ax.figure.tight_layout()

        fig.set_size_inches(7.5, 3)
        plt.margins(0, 0)
        fig.subplots_adjust(top=0.99, bottom=0.3, left=0.08, right=0.99)
        fig.tight_layout(pad=0.1, h_pad=1.08, w_pad=1.08)
        fig.savefig(f"{OUT_DIR}/{name}-stats-time_ns-{mname}{sname}.pdf")
        fig.clear()
        plt.close(fig)
