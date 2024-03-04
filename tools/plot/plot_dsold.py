import numpy as np
import scipy
import seaborn as sns

from matplotlib.lines import Line2D
from matplotlib.markers import MarkerStyle
from matplotlib.patches import Patch

from common import *
from common_utils import *

dfm["stats.time_ns"] = dfm["stats"].apply(lambda d: p(d, "time_ns", np.NAN))
dfm["stats.time_ns"] = dfm["stats.time_ns"].fillna(dfm["stats.time_ns"].max())

dotted = (1, 1)
dashed = (5, 5)
dashdot = (3, 5, 1, 5)
solid = ""
DASHES = {"ILP": dashed, "HananiTutte": dotted, "HananiTutte-f": solid, "PQPlanarity-c-i": dashdot}
FILLS = {"ILP": "top", "HananiTutte": "left", "HananiTutte-f": "left", "PQPlanarity-c-i": "full"}
tab10 = matplotlib.colormaps.get_cmap("tab10").colors
COLORS = {
    "ILP": tab10[0], "HananiTutte": tab10[1], "HananiTutte-f": tab10[2], "PQPlanarity-c-i": tab10[3]
}
MARKERS = {"Y": "o", "N": "X", "TO": "P", "ERR": "s"}


def style_map(func):
    return {
        f"{m}/{e}": func(m, e)
        for m in ["ILP", "HananiTutte", "HananiTutte-f", "PQPlanarity-c-i"]
        for e in ["Y", "N", "TO", "ERR"]
    }


if "-dsold" in name or "-med" in name:
    dfm["bin"] = pd.qcut(dfm["cluster-crossing"], 10).apply(lambda b: b.mid)
    dfm["cat"] = dfm["mode"] + "/" + dfm["exit_code"].apply(str)

    # dfm["value-c"] = dfm["value"].clip(upper=3e10)
    ecs = dfm["exit_code"].unique()
    markers = style_map(lambda m, e: MarkerStyle(
        MARKERS[e]  # , fillstyle=FILLS[m]
    ))
    ax = sns.scatterplot(
        dfm.sample(frac=1, random_state=42),
        x=xcol, y="stats.time_ns", alpha=0.6,
        hue="mode", style="exit_code",
        hue_order=[m for m in ORDER if m in modes],
        style_order=pd.Series(EXIT_CODE_ORDER + list(ecs)).unique()
        # edgecolor='black'
    )
    # ax = sns.lineplot(dfm, x="bin", y="value", hue="variable",markers=MARKERS, ax=ax)
    ax.set_yscale("log")
    for t in ax.get_legend().texts:
        t.set_text(get_label(t.get_text()))
    ax.set_xlabel("# Cluster-Edge Crossings")
    ax.set_ylabel("")
    ax.yaxis.set_major_formatter(format_ns)
    ax.figure.set_size_inches(6, 4)
    ax.xaxis.grid(True, which='major')
    ax.yaxis.grid(True, which='major')
    ax.set_axisbelow(True)

    if name.endswith("dsold"):
        ax.set_xlim(left=-1, right=170)
        ax.figure.tight_layout()
        ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns-big.png")
        ax.set_xlim(left=-1, right=100)
    else:
        ax.set_xlim(left=-50, right=6000)
        ax.figure.tight_layout()
        ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns-big.png")
        ax.set_xlim(left=-10, right=1000)

    ax.figure.tight_layout()
    ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns.png")
    ax.figure.clear()

    ####

    maxy = 5 * 60 / scipy.constants.nano
    dfm.loc[dfm["exit_code"] == 124, "time_ns"] = maxy
    markers = style_map(lambda m, e: MARKERS[e])
    dashes = style_map(lambda m, e: DASHES[m])
    ax = sns.lineplot(
        dfm[dfm["exit_code"].isin(["Y", "N"])],
        x="bin", y="stats.time_ns", hue="mode", style="cat",
        palette=COLORS, markers=markers, dashes=dashes,
        estimator="median", errorbar=("pi", 50), legend=False, markersize=6)

    ax.axhline(maxy, color="black", alpha=0.5)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(format_ns)
    ax.set_xlim(-50, 200)
    ax.set_ylabel("")
    ax.set_xlabel("# Cluster-Edge Crossings")
    ax.xaxis.grid(True, which='major')
    ax.yaxis.grid(True, which='major')
    ax.figure.set_size_inches(6, 4)
    ax.set_axisbelow(True)

    legend = {
        "Mode": Patch(color='none', label='Mode'),
        "ILP": Line2D([0], [0], color=tab10[0], linestyle=(0, DASHES["ILP"]), lw=2),
        "HT": Line2D([0], [0], color=tab10[1], linestyle=(0, DASHES["HananiTutte"]), lw=2),
        "HT-f": Line2D([0], [0], color=tab10[2], linestyle=(0, DASHES["HananiTutte-f"]), lw=2),
        "SP[d]": Line2D([0], [0], color=tab10[3], linestyle=(0, DASHES["PQPlanarity-c-i"]), lw=2),
        "Result": Patch(color='none', label='Result'),
        "Y": Line2D([0], [0], marker=MARKERS["Y"], color="k", markersize=6, lw=0),
        "N": Line2D([0], [0], marker=MARKERS["N"], color="k", markersize=6, lw=0),
        # "TO": Line2D([0], [0], marker=MARKERS["TO"], color="k", markersize=6, lw=0),
        # "ERR": Line2D([0], [0], marker=MARKERS["ERR"], color="k", markersize=6, lw=0),
    }
    ax.legend(list(legend.values()), list(legend.keys()))

    if name.endswith("dsold"):
        ax.set_xlim(left=-1, right=170)
        ax.figure.tight_layout()
        ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns-lines-big.pdf")
        ax.set_xlim(left=-1, right=100)
    else:
        ax.set_xlim(left=-50, right=6000)
        ax.figure.tight_layout()
        ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns-lines-big.pdf")
        ax.set_xlim(left=-10, right=1000)

    ax.figure.tight_layout()
    ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns-lines.pdf")
    ax.figure.clear()
