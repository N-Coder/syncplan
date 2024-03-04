import sys

import matplotlib
import pandas as pd
import scipy.constants
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from tqdm import tqdm

from common_db import *
from common_utils import *

matplotlib.rcParams['savefig.dpi'] = 300

df = pd.concat(
    pd.DataFrame(
        tqdm(db[name].find({
            "mode": {"$in": ["HananiTutte", "PQPlanarity-c-i"]},
            # "exit_code": {"$in": [0, 9, ]},
        }, {
            "mode": "$mode", "exit_code": "$exit_code", "time_ns": "$stats.time_ns",
            "size": "$stats.init_stats.pipes_degrees", "ds": name, "file_nr": "$file_nr"
        }),
            file=sys.stdout)
    )
    for name in ["stats-dsold", "stats-clusters-medncp", "stats-clusters-med"]
)
df = df.drop("size", axis=1).merge(df[df["mode"] == "PQPlanarity-c-i"][["ds", "file_nr", "size"]], on=["ds", "file_nr"])
df["bin"] = pd.qcut(df["size"], 20).apply(lambda b: b.mid)
df["cat"] = df["mode"] + "/" + df["exit_code"].apply(str)

maxy = 5 * 60 / scipy.constants.nano
df.loc[df["exit_code"] == 124, "time_ns"] = maxy

dashed = (5, 5)
solid = ""
tab10 = matplotlib.colormaps.get_cmap("tab10").colors
colors = {
    "HananiTutte": tab10[1], "PQPlanarity-c-i": tab10[3]
}
markers = {
    "HananiTutte/0": "o", "HananiTutte/9": "X", "HananiTutte/124": "P",
    "PQPlanarity-c-i/0": "o", "PQPlanarity-c-i/9": "X", "PQPlanarity-c-i/124": "P",
}
dashes = {
    "HananiTutte/0": dashed, "HananiTutte/9": dashed, "HananiTutte/124": dashed,
    "PQPlanarity-c-i/0": "", "PQPlanarity-c-i/9": "", "PQPlanarity-c-i/124": "",
}

ax = sns.lineplot(df, x="bin", y="time_ns", hue="mode", style="cat",
                  palette=colors, markers=markers, dashes=dashes,
                  estimator="median", errorbar=("pi", 50), legend=False)

# ax.axhline(maxy, color="black", alpha=0.5)
ax.set_yscale("log")
ax.yaxis.set_major_formatter(format_ns)
ax.set_xlim(-50, 2500)
ax.set_ylabel("")
ax.set_xlabel("# Cluster-Edge Crossings")
ax.xaxis.grid(True, which='major')
ax.yaxis.grid(True, which='major')

legend = {
    "Mode": Patch(color='none', label='Mode'),
    "HT": Line2D([0], [0], color=tab10[1], linestyle="dashed", lw=2),
    "SP[d]": Line2D([0], [0], color=tab10[3], linestyle="solid", lw=2),
    "Result": Patch(color='none', label='Result'),
    "Y": Line2D([0], [0], marker="o", color="k", markersize=6, lw=0),
    "N": Line2D([0], [0], marker="X", color="k", markersize=6, lw=0),
    "TO": Line2D([0], [0], marker="P", color="k", markersize=6, lw=0),
}
ax.legend(list(legend.values()), list(legend.keys()))

ax.figure.set_size_inches(6, 4)
ax.figure.tight_layout()
ax.figure.savefig(OUT_DIR + "/plot-meds.pdf")
ax.figure.clear()
