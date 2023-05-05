import common
import plot_dsold
import plot_rt
import plot_timeout
import plot_binom_test

if "opstats" in common.dfm:
    import plot_opstats

__all__ = [
    "common",
    "plot_dsold",
    "plot_rt",
    "plot_timeout",
    "plot_binom_test",
    "plot_opstats",
]

import matplotlib.pyplot as plt
plt.close("all")
