from common_db import coll
from common_utils import *
from numpy.polynomial import Polynomial as P
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns

df = pd.json_normalize(coll.find({"mode": "PQPlanarity-c-i"},
                                 {"m": "$mode", "x": "$stats.init_stats.pipes_degrees", "y": "$stats.time_ns"}))
df.dropna(inplace=True)

maxy = df["y"].max() * 1.1
df["y"].fillna(maxy, inplace=True)

df["yl"] = np.log10(df["y"])
df["xl"] = np.log10(df["x"])
# dfl = df[(10 <= df["x"]) & (df["x"] <= 100000)].copy()
dfl = df

poly_fit = P.fit(dfl["xl"], dfl["yl"], deg=1)
print(poly_fit.convert())  # convert() disables domain/window scaling

# stats = pd.DataFrame(dfl["x"].quantile([x / 100 for x in range(0, 105, 5)]))
# ys = dfl.groupby("x").median("yl")

poly_13 = poly_fit.convert().copy()
poly_13.coef[1] = 1.3
# poly_17 = poly_fit.convert().copy()
# poly_17.coef[1] = 1.7
poly_2 = poly_fit.convert().copy()
poly_2.coef[1] = 2

# cyc = plt.rcParams["axes.prop_cycle"]()

plt.close()
sns.set_style()
plt.scatter(dfl["x"], dfl["y"], label="SP[d] runtime", edgecolors="white", linewidths=0.5, color='#1f77b4')
for poly, color in [(poly_13, '#2ca02c'), (poly_fit, '#ff7f0e'), (poly_2, '#d62728')]: # , (poly_17, '#9467bd')
    xs, ys = poly.convert(domain=poly_fit.domain, window=poly_fit.domain).linspace(10)
    pdf = pd.DataFrame(10 ** ys, 10 ** xs)
    c = poly.convert().coef
    plt.plot(pdf, 'o-', label=f"${c[0]:.3} \cdot x^{{{c[1]:.3}}}$", color=color)
#
ax = plt.gca()
ax.axhline(maxy, color="black", alpha=0.5)
ax.xaxis.grid(True, which='major')
ax.yaxis.grid(True, which='major')
# ax.yaxis.set_major_formatter(format_ns)
plt.ylabel("Total Time [ns]")
plt.xlabel("Number of Cluster-Border Edge Crossings")
ax.dataLim.y1 = maxy
ax.figure.set_size_inches(7, 4)
plt.legend()


for xlog in ["linear", "log"]:
    for ylog in ["linear", "log"]:
        ax.set_xscale(xlog)
        ax.set_yscale(ylog)
        plt.tight_layout()
        plt.savefig(f"fit-x{xlog}-y{ylog}.pdf")
        plt.savefig(f"fit-x{xlog}-y{ylog}.png")
