import numpy as np
import seaborn as sns

from common import *
from common_utils import *

dfm["stats.time_ns"] = dfm["stats"].apply(lambda d: p(d, "time_ns", np.NAN))
dfm["stats.time_ns"] = dfm["stats.time_ns"].fillna(dfm["stats.time_ns"].max())


# dfm["value-c"] = dfm["value"].clip(upper=3e10)
ecs = dfm["exit_code"].unique()
ax = sns.scatterplot(
    dfm.sample(frac=1, random_state=42),
    x=xcol, y="stats.time_ns", alpha=0.6,
    hue="mode", style="exit_code",
    hue_order=[m for m in ORDER if m in modes],
    style_order=pd.Series(EXIT_CODE_ORDER + list(ecs)).unique())
# ax = sns.lineplot(dfm, x="bin", y="value", hue="variable",markers=MARKERS, ax=ax)
ax.set_yscale("log")
for t in ax.get_legend().texts:
    t.set_text(get_label(t.get_text()))
ax.set_xlabel("# Cluster-Edge Crossings")
ax.set_ylabel("")
ax.yaxis.set_major_formatter(format_ns)
ax.figure.set_size_inches(6, 4)
ax.figure.tight_layout()
if name.endswith("dsold"):
    ax.set_xlim(left=-1, right=100)
else:
    ax.set_xlim(left=-50, right=6000)
    ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns-big.png")
    ax.set_xlim(left=-10, right=1000)
ax.figure.savefig(f"{OUT_DIR}/{name}-time_ns.png")
ax.figure.clear()
