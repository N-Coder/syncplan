import sys
import warnings

import matplotlib
import pandas as pd
from tqdm import tqdm

from common_db import *
from common_utils import *

warnings.filterwarnings("ignore", category=UserWarning, message="The markers list has more values")
matplotlib.rcParams['savefig.dpi'] = 300

# %%

# Load CSV
filter = {}
file = os.getenv("SP_INDEX", "index.csv")
df = pd.read_csv(file)
max_idx = None
if "SP_MAX_IDX" in os.environ:
    max_idx = int(os.environ["SP_MAX_IDX"])
    df = df[df["nr"] <= max_idx]
    filter = {"file_nr": {"$lte": max_idx}}
if "-med" in name or "dsold" in name:
    print("Ignoring PQPlanarity and only using PQPlanarity-c-i")
    filter["mode"] = {"$ne": "PQPlanarity"}
df["density"] = df["edges"] / df["nodes"]

# %%

# Load DB data
modes = set()
for doc in tqdm(coll.find(filter=filter), file=sys.stdout):
    if doc["mode"] not in modes:
        modes.add(doc["mode"])
        df[doc["mode"]] = [{}] * len(df)
    file_nr = int(doc["file_nr"])
    if df.at[file_nr, "file"] == doc["file"]:
        df.at[file_nr, doc["mode"]] = doc
    else:
        file_nrs = df.loc[df["file"] == doc["file"].lstrip("./"), "nr"]
        print(f"{doc['mode']} document claims file_nr {file_nr} for file {doc['file']}, but index says {file_nrs}")
        if len(file_nrs) == 1:
            df.at[file_nrs.iat[0], doc["mode"]] = doc

# %%

id_vars = ['md5', 'size', 'nodes', 'edges', 'density', 'planar', 'components', 'bin']
if 'cluster-crossing' in df:
    id_vars += ['clusters', 'cluster-tree', 'cluster-depth', 'cluster-crossing', 'can-preprocess']
    xcol = 'cluster-crossing'
else:
    id_vars += ["pipe-max-deg", "pipe-total-deg", "pipes", ]
    xcol = "pipe-total-deg"
df["bin"] = pd.qcut(df[xcol], 10).apply(lambda b: b.mid)
dfm = df.melt(value_vars=[m for m in ORDER if m in modes], ignore_index=False, id_vars=id_vars) \
    .set_index("variable", append=True)
dfm = pd.concat([dfm, pd.json_normalize(dfm["value"], max_level=0).set_index(dfm.index)], axis=1)
dfm.index.name = ("file_nr", "mode")
dfm["exit_code"] = dfm["exit_code"].apply(parse_exit_code)

# %%

print(dfm["exit_code"].value_counts().to_string())
print()
print(
    dfm["exit_code"].reset_index(level=1).value_counts().reset_index(level=1).pivot(columns=["exit_code"], values=["count"]))
print()
exit_code_combinations = dfm["exit_code"].reset_index() \
    .assign(variable=lambda df: df["variable"].apply(MODES.get)) \
    .pivot(index="level_0", columns="variable", values="exit_code") \
    .value_counts().reset_index().rename({0: "Count"}, axis=1)
if len(exit_code_combinations) < 10:
    print(exit_code_combinations.to_string())
    print()
    print(exit_code_combinations.style.to_latex())
    print()
elif "HT" in exit_code_combinations:
    print(exit_code_combinations[(exit_code_combinations["HT"] == "N") & (exit_code_combinations["SP[d]"] == "Y")])
