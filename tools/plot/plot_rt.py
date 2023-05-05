import matplotlib.pyplot as plt
import seaborn as sns

from common import *
from common_utils import *


def rt_calc_frac(dfm, ycol, ref_val):
    dfm = dfm.drop(columns=["ref", "key_0", ycol + "-frac"], errors="ignore")
    if ref_val == "min":
        ref = dfm.groupby("file_nr")[ycol].min()  # compare with fastest
    elif ref_val in dfm.index.get_level_values(1):
        ref = dfm.loc[(slice(None), ref_val), "value"] \
            .apply(lambda d: p(d, ycol)) \
            .reset_index(level=1, drop=True)  # compare with PQPlanarity-c-i
    else:
        return dfm
    if ref.empty:
        return dfm
    ref.name = "ref"
    dfm = dfm.merge(ref, left_on=dfm.index.get_level_values(0).values, right_index=True)
    if dfm.empty:
        raise RuntimeError("something is wrong")
    if not ref.isnull().all():
        dfm[ycol + "-frac"] = dfm[ycol].div(dfm["ref"])
    return dfm


def rt_plot(dfm, xcol, ycol, catcol, dfm_line=None, hue_order=None):
    avail_cats = sorted(dfm[catcol].unique(), key=col_idx)
    if hue_order is None:
        hue_order = avail_cats
    ax = sns.scatterplot(
        dfm.sample(frac=1, random_state=42),
        x=xcol, y=ycol,
        hue=catcol, style=catcol, hue_order=hue_order, style_order=hue_order,
        legend=False, markers=MARKERS)
    ax = sns.lineplot(
        dfm_line if dfm_line is not None else dfm, ax=ax,
        x="bin", y=ycol,
        hue=catcol, style=catcol, hue_order=hue_order, style_order=hue_order,
        dashes=False, markers=MARKERS, linewidth=2, markersize=9, markeredgecolor="black",
        errorbar=None, estimator="median", legend=True)

    ax.set_ylabel(get_label(ycol))
    ax.set_xlabel(get_label(xcol))
    ax.set_xscale("log")
    handles, labels = [], []
    for handle, label in zip(*ax.get_legend_handles_labels()):
        if label not in avail_cats:
            continue
        handle.set_markeredgecolor("black")
        handle.set_markersize(8)
        handle.set_linewidth(2)
        handles.append(handle)
        labels.append(get_label(label))
    if handles:
        ax.legend(handles, labels, loc="best", ncols=2, title="")
        ax.get_legend().set_visible(False)

    ax.figure.set_size_inches(7, 4)
    return ax


stats = [
    "stats.time_ns", #"stats.time_make_reduced_ns", "stats.time_solve_reduced_ns", "stats.time_embed_ns",
    #"stats.undo_ops", "stats.reduced_stats.edges", "stats.reduced_stats.partitions", "stats.reduced_stats.bicon",
    #"stats.reduced_stats.bicon_sum_size",
    "stats.reduced_stats.bicon_max_size",
    #"reduced_bicon_avg_size",
    #"time.User time (seconds)", "time.System time (seconds)",
    "time.Maximum resident set size (kbytes)"
]
dfm["reduced_bicon_avg_size"] = dfm["value"].apply(lambda d: p(d, "stats.reduced_stats.bicon_sum_size")).div(
    dfm["value"].apply(lambda d: p(d, "stats.reduced_stats.bicon")))
# dfm[xcol] = ilp["value"].apply(lambda d: p(d, xcol))
dfm["bin"] = pd.qcut(dfm[xcol], 10).apply(lambda b: b.mid)
catcol = "mode"
for ycol in stats:
    # ycol = stats[0]
    print(f"Time Plot {xcol} x {ycol}")

    if ycol not in ["reduced_bicon_avg_size"]:
        dfm[ycol] = dfm["value"].apply(lambda d: p(d, ycol))
    if dfm[ycol].isna().all():
        continue
    if ycol.endswith("_ns") or ycol.endswith("(seconds)"):
        maxy = dfm[ycol].max() * 1.1
        dfm[ycol].fillna(maxy, inplace=True)
    else:
        maxy = None
    hue_order = sorted(dfm[catcol].unique(), key=col_idx)

    ax = rt_plot(dfm, xcol, ycol, catcol, hue_order=hue_order)
    if ycol.endswith("_ns") or ycol.endswith("(seconds)"):
        ax.axhline(maxy, color="black", alpha=0.5)
    ax.set_yscale("log")
    if ycol.endswith("_ns") or ycol.endswith("op_time"):
        ax.yaxis.set_major_formatter(format_ns)
    elif "(seconds)" in ycol:
        ax.yaxis.set_major_formatter(format_s)

    if ycol == "stats.time_ns":
        fig = plt.figure()
        handles, labels = [], []
        for handle, label in zip(*ax.get_legend_handles_labels()):
            if label not in hue_order:
                continue
            handles.append(handle)
            labels.append(get_label(label))
        if handles:
            legend = fig.legend(handles, labels, ncol=len(labels) // 3, loc="center")
            bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
            fig.set_size_inches(bbox.width + 0.1, bbox.height + 0.1)
            fig.savefig(f"{OUT_DIR}/{name}-legend.pdf")  # , bbox_inches=bbox)
            fig.clear()

    fname = re.sub("[^a-zA-Z0-9.-]+", "_", f"{name}-{xcol}-{ycol}").strip("_").lower()
    ax.figure.tight_layout()
    ax.figure.savefig(f"{OUT_DIR}/{fname}.png")
    ax.figure.clear()

    ####

    # ycol = stats[0]
    dfm = rt_calc_frac(dfm, ycol, "PQPlanarity-c-i")
    if "ref" not in dfm.columns or dfm["ref"].isnull().all() or dfm["ref"].max() == 0.0:
        continue
    last_bin = dfm["bin"].max()  # drop the last bucket due to too many timeouts (see tofrac)
    ax = rt_plot(dfm, xcol, ycol + "-frac", catcol, dfm_line=dfm[dfm["bin"] != last_bin], hue_order=hue_order)
    ax.set_ylim(bottom=0, top=5)
    ax.figure.tight_layout()
    ax.figure.savefig(f"{OUT_DIR}/{fname}-frac.png")
    ax.figure.clear()

    dfm = rt_calc_frac(dfm, ycol, "min")
    ax = rt_plot(dfm, xcol, ycol + "-frac", catcol, dfm_line=dfm[dfm["bin"] != last_bin], hue_order=hue_order)
    ax.set_ylim(bottom=1, top=10)
    ax.figure.tight_layout()
    ax.figure.savefig(f"{OUT_DIR}/{fname}-frac-min.png")
    ax.figure.clear()

    for nr, clusters in enumerate(RT_CLUSTERS):
        # clusters = RT_CLUSTERS[3]
        dfm = rt_calc_frac(dfm, ycol, clusters[-1])
        if "ref" not in dfm.columns or dfm["ref"].isnull().all() or dfm["ref"].max() == 0.0:
            continue
        ax = rt_plot(dfm[dfm["mode"].isin(clusters)], xcol, ycol + "-frac", catcol,
                     dfm_line=dfm[dfm["mode"].isin(clusters) & (dfm["bin"] != last_bin)], hue_order=hue_order)
        ax.set_ylim(bottom=0, top=5 if nr == 0 else 2)
        ax.figure.tight_layout()
        ax.figure.savefig(f"{OUT_DIR}/{fname}-frac-cluster{nr}.png")
        ax.figure.clear()
