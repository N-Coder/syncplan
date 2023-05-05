import pandas as pd

from common_db import db
from common_utils import *

data = []

DATASETS = {
    "index-dsold.csv": "\dsold",
    "index-clusters-medncp.csv": "\dsmedncp",
    "index-clusters-med.csv": "\dsmed",
    "index-clusters-large.csv": "\dslarge",
    "index-instances-sefe.csv": "\dssefe",
    "index-instances-pq.csv": "\dspq",
}

for file, ds_name in DATASETS.items():
    df = pd.read_csv(file)
    df["density"] = df["edges"] / df["nodes"]
    df = df[df["edges"] != 0]
    if "clusters" in df.columns:
        df = df[df["cluster-crossing"] != 0]
        df["Delta"] = df["cluster-crossing"] / df["clusters"]
    else:
        df = df[df["pipe-total-deg"] != 0]
        df["Delta"] = df["pipe-total-deg"] / df["pipes"]
    if file == "index-instances-sefe.csv":
        df["nodes"] = df["file"].str.replace(".*-n([0-9]+)-.*", "\\1", regex=True).apply(int)
        df["edges"] = df["file"].str.replace(".*-e([0-9]+)-.*", "\\1", regex=True).apply(int)
        df["components"] = 1
    desc = df.describe()

    data.append({
        "Dataset": ds_name,
        "Instances": f"{desc.loc['count']['nr']:.0f}",
        "Nodes": f"{desc.loc['min']['nodes']:.0f}--{desc.loc['max']['nodes']:.0f} ({desc.loc['mean']['nodes']:.1f})",
        "Density": f"{desc.loc['min']['density']:.1f}--{desc.loc['max']['density']:.1f} ({desc.loc['mean']['density']:.1f})",
        "Components": f"{desc.loc['min']['components']:.0f}--{desc.loc['max']['components']:.0f} ({desc.loc['mean']['components']:.1f})",
    })
    if "clusters" in df.columns:
        data[-1].update({
            "Clusters/Pipes": f"{desc.loc['min']['clusters']:.0f}--{desc.loc['max']['clusters']:.0f} ({desc.loc['mean']['clusters']:.1f})",
            # "cluster-depth": f"{desc.loc['min']['cluster-depth']:.0f}--{desc.loc['max']['cluster-depth']:.0f} ({desc.loc['mean']['cluster-depth']:.1f})",
            "$d$": f"{desc.loc['min']['cluster-crossing']:.0f}--{desc.loc['max']['cluster-crossing']:.0f} ({desc.loc['mean']['cluster-crossing']:.1f})",
            # "$\Delta$": f"{desc.loc['min']['Delta']:.0f}--{desc.loc['max']['Delta']:.0f} ({desc.loc['mean']['Delta']:.1f})",
        })
    else:
        data[-1].update({
            "Clusters/Pipes": f"{desc.loc['min']['pipes']:.0f}--{desc.loc['max']['pipes']:.0f} ({desc.loc['mean']['pipes']:.1f})",
            # "cluster-depth": f"{desc.loc['min']['cluster-depth']:.0f}--{desc.loc['max']['cluster-depth']:.0f} ({desc.loc['mean']['cluster-depth']:.1f})",
            "$d$": f"{desc.loc['min']['pipe-total-deg']:.0f}--{desc.loc['max']['pipe-total-deg']:.0f} ({desc.loc['mean']['pipe-total-deg']:.1f})",
            # "$\Delta$": f"{desc.loc['min']['Delta']:.0f}--{desc.loc['max']['Delta']:.0f} ({desc.loc['mean']['Delta']:.1f})",
        })

df = pd.DataFrame(data)
df.set_index("Dataset", drop=True, inplace=True)
print(df.style.to_latex())
print()
for row in df.itertuples():
    print(r"\newcommand{%ssize}{%s}" % (row.Index, row.Instances))
print(r"\newcommand{\dstotalsize}{%s}" % (df.Instances.apply(int).sum()))

# %%


DS_ORDER = ["\\dsold", "\\dsmedncp", "\\dsmed"]
MODE_ORDER = ["ILP", "HT", "HT-f", "SP[d]"]


def coll_exit_stats(cname):
    return pd.DataFrame(
        {"ds": DATASETS[cname.replace("stats-", "index-") + ".csv"],
         "count": d["count"],
         "exit_code": parse_exit_code(d["_id"]["exit_code"]),
         "mode": MODES.get(d["_id"]["mode"])}
        for d in
        db[cname].aggregate([{'$group': {
            '_id': {'exit_code': '$exit_code', 'mode': '$mode'},
            'count': {'$sum': 1}
        }}]))


edf = pd.concat(
    [coll_exit_stats("stats-dsold"), coll_exit_stats("stats-clusters-med"), coll_exit_stats("stats-clusters-medncp")])
edf = edf[edf["mode"].isin(MODE_ORDER)]
piv = edf.groupby(["ds", "mode", "exit_code"]).sum().reset_index() \
    .pivot(columns=["ds", "mode"], values="count", index="exit_code").fillna(0).astype("int")
piv.sort_index(axis=1, level=1, key=lambda s: s.map(MODE_ORDER.index), kind="stable", sort_remaining=False,
               inplace=True)
piv.sort_index(axis=1, level=0, key=lambda s: s.map(DS_ORDER.index), kind="stable", sort_remaining=False, inplace=True)
piv.sort_index(axis=0, level=0, key=lambda s: s.map(EXIT_CODE_ORDER.index), kind="stable", sort_remaining=False,
               inplace=True)

print(piv.to_string())
print()
print(piv.style.to_latex())
