import common

if "-dsold" in common.name or "-med" in common.name:
    import plot_dsold
else:  # if "-large" in common.name or "-instances" in common.name:
    import plot_rt
    import plot_timeout
    import plot_binom_test

if "-dsold" in common.name:
    import plot_meds

if "opstats" in common.dfm:
    import plot_opstats

__all__ = [
    "common",
    "plot_dsold",
    "plot_meds",
    "plot_rt",
    "plot_timeout",
    "plot_binom_test",
    "plot_opstats",
]

import matplotlib.pyplot as plt

plt.close("all")
