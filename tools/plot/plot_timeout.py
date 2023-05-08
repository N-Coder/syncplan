import seaborn as sns
from matplotlib import ticker as mtick

from common import *
from common_utils import *

tofrac = dfm.reset_index().groupby(["variable", "bin", "exit_code"], )["md5"].count().reset_index(
    level="exit_code").pivot(columns="exit_code", values="md5")
if "TO" in tofrac:
    tofrac["frac"] = tofrac["TO"].div(tofrac.sum(axis=1))

    tofracp = tofrac.reset_index().pivot(columns="variable", values="frac", index="bin")
    tofract = pd.concat([
        tofracp.reset_index(drop=True).loc[:7].sum(),
        tofracp.reset_index(drop=True).loc[8],
        tofracp.reset_index(drop=True).loc[9]
    ], axis=1).T
    tofract["bins"] = ["<80%", "80-90%", ">90%"]
    tofract.set_index("bins", drop=True, inplace=True)
    tofract.sort_index(axis=1, inplace=True, key=lambda cs: [col_idx(c) for c in cs])
    tofract.rename(get_label, axis=1, inplace=True)
    print(tofract.applymap(lambda v: f"{v * 100:.0f}%").style.to_latex().replace("%", "\\%"))

    hue_order = sorted(tofrac.index.get_level_values("variable").unique(), key=col_idx)
    ax = sns.lineplot(
        tofrac.reset_index(),
        x="bin", y="frac",
        hue="variable", style="variable", hue_order=hue_order, style_order=hue_order,
        dashes=False, markers=MARKERS, linewidth=2, markersize=9, markeredgecolor="black")
    ax.set_ylabel("Timed-out Instances")
    ax.set_xlabel(get_label(xcol))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.grid(visible=True, which='major', axis='y')
    ax.set_xscale("log")
    sns.move_legend(ax, loc="best", ncols=2, title="")
    for t in ax.get_legend().texts:
        t.set_text(get_label(t.get_text()))
    for h in ax.get_legend().legend_handles:
        h.set_markeredgecolor("black")
        h.set_markersize(8)
        h.set_linewidth(2)
    ax.figure.set_size_inches(7, 4)
    ax.figure.tight_layout()
    ax.get_legend().set_visible(False)
    ax.figure.savefig(f"{OUT_DIR}/{name}-timedout-frac.png")
    ax.figure.clear()
