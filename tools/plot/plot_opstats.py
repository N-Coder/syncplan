from itertools import product

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

from common import *
from common_utils import *
from opstats_constants import *


def extract_times(dfm):
    dfm = dfm.copy()
    max_time = dfm["stats"].apply(lambda d: p(d, "time_ns", np.NAN)).max()
    dfm["timeout_ns"] = 0.0
    dfm.loc[~dfm["exit_code"].isin([0, 9, "Y", "N"]), "timeout_ns"] = max_time

    df_opstats = pd.json_normalize(dfm["opstats"]).set_index(dfm.index)
    df_stats = pd.json_normalize(dfm["stats"]).set_index(dfm.index)
    times = pd.concat([
        df_opstats.fillna(0).clip(lower=0).groupby(level=[1]).mean(),
        df_stats[df_stats.columns[df_stats.dtypes != "object"]] \
            .fillna(0).clip(lower=0).groupby(level=[1]).mean(),
        dfm["timeout_ns"].groupby(level=[1]).mean(),
    ], axis=1)

    times["all"] = sum(times[sg] for sg in [
        "time_ns", "timeout_ns",
        "time_embed_ns", "time_check_ns"
    ] if sg in times)
    # times["all"] = sum(times[sg] for sg in GROUPS["all"])

    for g, sgs in GROUPS.items():
        if g == "all": continue
        if g not in times: continue
        times[g + "-overhead"] = times[g] - sum(times[sg] for sg in sgs if sg in times)

    times_sum = lambda *p: times[times.columns.intersection(map("".join, product(*p)))].sum(axis=1)
    times["contract_time"] = times_sum(PREFIXES, CONTRACTS, [".op_time"])
    times["propagate_time"] = times_sum(PREFIXES, PROPAGATES, [".op_time"])
    times["simplify_time"] = times_sum(PREFIXES, SIMPLIFYS, [".op_time"])
    times["emb_tree_time"] = times_sum(PREFIXES, PROPAGATES + SIMPLIFYS + ["MAKE_SPQR"], [".pc_time"])
    times["contract_counts"] = times_sum(PREFIXES, CONTRACTS, [".count"])
    times["propagate_counts"] = times_sum(PREFIXES, PROPAGATES, [".count"])
    times["simplify_counts"] = times_sum(PREFIXES, SIMPLIFYS, [".count"])
    times["emb_tree_scanned"] = times_sum(PREFIXES, PROPAGATES + SIMPLIFYS + ["MAKE_SPQR"], [".pc_scan_nodes"])
    open(f"{OUT_DIR}/{name}-stats.csv", "wt").write(times.to_csv())

    times_groups = times.reset_index().assign(
        flag_s=lambda d: d["variable"].str.contains("-p"),
        flag_b=lambda d: ~d["variable"].str.contains("-c")
    ).groupby(["flag_s", "flag_b"]).mean(numeric_only=True)
    open(f"{OUT_DIR}/{name}-stats-groups.csv", "wt").write(times_groups.to_csv())

    # df_opcount = df_opstats.filter(like=".count", axis=1).fillna(0).clip(lower=0).groupby(level=[1]).mean()
    # print(df_opcount.to_string())
    # dfm["wheels"] = dfm["stats"].apply(lambda d: p(d, "reduced_stats.q_vertices"))
    # times["wheels"] = dfm["wheels"].fillna(0).clip(lower=0).groupby(level=[1]).mean()
    # print(times["wheels"].to_string())

    return times


for sname, selection in {
    "-xs": (dfm[xcol] <= 1000),
    "-s": (dfm[xcol] <= 5000),
    "-m": (dfm[xcol] > 5000) & (dfm[xcol] <= 50000),
    "-l": (dfm[xcol] > 50000),
    "": (slice(None))
}.items():

    # sname, selection = "", slice(None)
    times = extract_times(dfm[selection])
    timesm = times.filter(regex="_ns|_time", axis=1).reset_index(names="idx").melt(id_vars=["idx"])

    fig, axs = plt.subplots(5, 1)
    char = "a"
    for (group, vals), ax in zip(GROUPS.items(), axs):
        if group not in times: continue
        print(f"OPstats{sname} {group}")
        # group = "time_make_reduced_ns"; vals = GROUPS[group]
        data = timesm[~timesm["idx"].isin(["HananiTutte", "HananiTutte-f", "ILP"]) \
                      & timesm["idx"].apply(lambda idx: times[group][idx] > 0) \
                      & timesm["variable"].isin(vals + [group + "-overhead"])].copy()
        if data.empty: continue
        data["idx"] = data["idx"].apply(lambda i: MODES[i])
        data["idx"] = pd.Categorical(data["idx"], [MODES[m] for m in ORDER if m in modes])
        variables = set(data["variable"].unique())
        ax = sns.histplot(
            data, x="idx", weights="value", hue="variable", multiple="stack", shrink=0.8,
            hue_order=[n for n in NAMES.keys() if n in variables], ax=ax)
        # hue_order=[n for n in [group + "-overhead", *NAMES.keys()] if n in variables], ax=ax)
        hatch_bars(ax)
        sns.move_legend(ax, loc='upper left', bbox_to_anchor=(1, 1.1 if ax != axs[0] else 1))
        ax.yaxis.set_major_formatter(format_ns)
        for label in ax.get_xticklabels():
            label.set_rotation(-40)
            label.set_horizontalalignment('left')
        for t in ax.get_legend().texts:
            tt = t.get_text()
            t.set_text(NAMES.get(tt, tt) if not tt.endswith("-overhead") else "Overhead")
        if group == "all":
            ax.get_legend().set_title("(%s) Algorithm Step" % char)
        else:
            ax.get_legend().set_title("(%s) Step of %s" % (char, NAMES.get(group, group)))
        char = chr(ord(char) + 1)
        ax.set_xlabel("")
        ax.set_ylabel("Time")

        # ax.xaxis.grid(True, which='major')
        ax.yaxis.grid(True, which='major')
        ax.set_axisbelow(True)

        # ax.figure.set_size_inches(10, 3)
        # ax.figure.tight_layout()
        # ax.figure.savefig(f"{OUT_DIR}/{name}-groups{sname}-{group}.pdf")
        # ax.figure.clear()

    fig.set_size_inches(10, 15)
    fig.tight_layout(h_pad=1)
    fig.savefig(f"{OUT_DIR}/{name}-groups{sname}.pdf")
    fig.clear()
    plt.close(fig)

# %%

overview = [
    "contract_time",
    "propagate_time",
    "simplify_time",
    "emb_tree_time",
    "time_solve_reduced_ns",
    "time_embed_ns",
]
data = timesm[timesm["idx"].isin(["PQPlanarity-c-i"]) \
              & timesm["idx"].apply(lambda idx: times[group][idx] > 0) \
              & timesm["variable"].isin(overview)].copy()
ax = sns.histplot(
    data, y="idx", weights="value", hue="variable", multiple="stack", shrink=0.8,
    hue_order=reversed(overview))
hatch_bars(ax, ['/', 'O', 'x', '.', '\\', '*'])
sns.move_legend(ax, loc='upper center', bbox_to_anchor=(0.5, -0.5), ncol=len(overview), reverse=True)
ax.set_yticks([])
ax.xaxis.set_major_formatter(format_ns)
for t in ax.get_legend().texts:
    tt = t.get_text()
    t.set_text(NAMES.get(tt, tt) if not tt.endswith("-overhead") else "Overhead")
ax.get_legend().set_title("")
ax.set_ylabel("")
ax.set_xlabel("")
ax.figure.set_size_inches(8, 1)
ax.set_position([0.02, 0.55, 0.96, 0.4])
ax.figure.savefig(f"{OUT_DIR}/{name}-groups-overview.pdf")
ax.figure.clear()

total = data["value"].sum()
data["frac"] = data["value"] / total
print(data.to_string())

# %%

# df_opstats = pd.json_normalize(dfm["opstats"]).set_index(dfm.index)
# dfo = df_opstats.filter(regex="pc_time|pot_red|pc_scan_nodes", axis=1)
# dfo = dfo[dfo.index.get_level_values("variable").str.contains("PQPlanarity")]
# dfo = dfo.fillna(0).groupby(level=[1]).mean()
# dfo = pd.DataFrame({
#     "pc_time": dfo.filter(like="pc_time", axis=1).sum(axis=1),
#     "pc_scan_nodes": dfo.filter(like="pc_scan_nodes", axis=1).sum(axis=1),
#     "pot_red": dfo.filter(like="pot_red", axis=1).sum(axis=1),
# })
# dfo["spr"] = dfo["pc_scan_nodes"] / dfo["pot_red"]
#
# for y in ["pc_time", "pot_red"]:
#     ax = sns.scatterplot(dfo, x="pc_scan_nodes", y=y)
#     texts = [
#         ax.text(s=row.Index, x=row.pc_scan_nodes, y=getattr(row, y), ha='center', va='center')
#         for row in dfo.itertuples()
#     ]
#     ax.figure.set_size_inches(15, 10)
#     ax.figure.tight_layout()
#     adjust_text(texts, arrowprops=dict(arrowstyle='-', color='black'))
#     ax.figure.savefig(f"{OUT_DIR}/{name}-pc_scan_nodes-{y}.pdf")
#     ax.figure.clear()

# for row in dfo.itertuples():
#     ax.annotate(row.Index, (row.pc_time, row.pc_scan_nodes))
