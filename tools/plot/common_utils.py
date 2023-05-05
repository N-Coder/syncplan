import os
import re
from itertools import cycle

OUT_DIR = os.getenv("SP_PLOT_DIR")
os.makedirs(OUT_DIR, exist_ok=True)


def format_ns(ns, ign=None):
    if ns == 0:
        return "0"
    elif abs(ns) < 1000:
        return f"{ns:.0f}ns"
    elif abs(ns) < 1000_000:
        return f"{ns / 1000:.2f}".rstrip("0").rstrip(".") + "µs"
    else:
        return format_ms(ns / 1000_000)


def format_ms(ms, ign=None):
    if ms == 0:
        return "0"
    elif abs(ms) < 1000:
        return f"{ms:.2f}".rstrip("0").rstrip(".") + "ms"
    elif abs(ms) < 60_000:
        return f"{ms / 1000:.2f}".rstrip("0").rstrip(".") + "s"
    elif abs(ms) < 60 * 60_000:
        return f"{ms / 60_000:.2f}".rstrip("0").rstrip(".") + "min"
    else:
        return f"{ms / 60 / 60_000:.2f}".rstrip("0").rstrip(".") + "h"


def format_s(s, ign=None):
    return format_ms(s * 1000)


# %%

EXIT_CODES = {
    0: "Y",
    9: "N",
    33: "ERR",
    39: "TO",
    124: "TO",
    137: "TO",  # Out of Memory
}

EXIT_CODE_ORDER = ["Y", "N", "ERR", "TO"]


def parse_exit_code(ec):
    return EXIT_CODES.get(ec, str(ec))


# %%

ORDER = [
    'ILP',
    'HananiTutte',
    'HananiTutte-f',

    "PQPlanarity-r",
    "PQPlanarity-a",
    "PQPlanarity-b",
    "PQPlanarity",
    "PQPlanarity-i",
    "PQPlanarity-b-s",

    "PQPlanarity-c",
    "PQPlanarity-c-i-r",
    "PQPlanarity-c-i-a",
    "PQPlanarity-c-i",
    "PQPlanarity-c-i-b",
    "PQPlanarity-c-i-b-s",

    "PQPlanarity-p-b-s-i",
    "PQPlanarity-p-i",
    "PQPlanarity-p-b-i",
    "PQPlanarity-p-b-s",
    "PQPlanarity-p",
    "PQPlanarity-p-b",
    "PQPlanarity-p-b-s-c",
    "PQPlanarity-p-b-c",
    "PQPlanarity-p-b-s-c-i",
    "PQPlanarity-p-b-c-i",
    "PQPlanarity-p-c",
    "PQPlanarity-p-c-i",
]


def col_idx(col):
    m = None
    if isinstance(col, str):
        m = re.fullmatch(r"(.+\.)?(?P<name>(PQPlanarity|HananiTutte|ILP|CConnected)[^\.]*)(\..+)?", col)
    if m:
        try:
            return ORDER.index(m.group("name"))
        except ValueError:
            pass
    return len(ORDER)


# %%

RT_CLUSTERS = [
    ["PQPlanarity-b-s", "PQPlanarity-c-i-b-s", "PQPlanarity-p"],
    [
        "PQPlanarity-r",
        "PQPlanarity-a",
        "PQPlanarity-b",
        "PQPlanarity",
        "PQPlanarity-i",
        "PQPlanarity-b-s",  # last is ref
    ], [
        "PQPlanarity-c",
        "PQPlanarity-c-i-r",
        "PQPlanarity-c-i-a",
        "PQPlanarity-c-i",
        "PQPlanarity-c-i-b",
        "PQPlanarity-c-i-b-s",  # last is ref
    ], [
        "PQPlanarity-p-b-s",
        "PQPlanarity-p-b-s-c",
        "PQPlanarity-p-b-s-i",
        "PQPlanarity-p-b-s-c-i",
        "PQPlanarity-p-i",
        "PQPlanarity-p-b-i",
        "PQPlanarity-p-c",
        "PQPlanarity-p-b-c-i",
        "PQPlanarity-p-b-c",
        "PQPlanarity-p-c-i",
        "PQPlanarity-p-b",
        "PQPlanarity-p",  # last is ref
    ]
]

# %%

MODES = {
    "CConnected": "CCon", "HananiTutte": "HT", "HananiTutte-f": "HT-f", "ILP": "ILP",

    # batch SPQR, by degree / contract first
    "PQPlanarity": "SP[d bi]", "PQPlanarity-p": "SP[d bis]", "PQPlanarity-p-b": "SP[d+c bis]",
    "PQPlanarity-p-b-s": "SP[d-c bis]",

    # no contract bicon-bicon and / or intersect PQ trees
    "PQPlanarity-c": "SP[d i]", "PQPlanarity-i": "SP[d b]", "PQPlanarity-c-i": "SP[d]",
    "PQPlanarity-p-c": "SP[d is]", "PQPlanarity-p-i": "SP[d bs]", "PQPlanarity-p-c-i": "SP[d s]",
    "PQPlanarity-p-b-c": "SP[d+c is]", "PQPlanarity-p-b-i": "SP[d+c bs]", "PQPlanarity-p-b-c-i": "SP[d+c s]",
    "PQPlanarity-p-b-s-c": "SP[d-c is]", "PQPlanarity-p-b-s-i": "SP[d-c bs]", "PQPlanarity-p-b-s-c-i": "SP[d-c s]",

    # random
    "PQPlanarity-r": "SP[r bi]", "PQPlanarity-c-i-r": "SP[r]",

    # ascending degree
    "PQPlanarity-a": "SP[a bi]", "PQPlanarity-c-i-a": "SP[a]",

    # descending, contract first
    "PQPlanarity-b": "SP[d+c bi]", "PQPlanarity-c-i-b": "SP[d+c]",

    # descending, contract last
    "PQPlanarity-b-s": "SP[d-c bi]", "PQPlanarity-c-i-b-s": "SP[d-c]",
}

LABELS = {
    **MODES,
    "init_stats.nodes": "Number of Nodes",
    "init_stats.edges": "Number of Edges",
    "init_stats.pipes": "Number of Pipes",
    "init_stats.pipes_degrees": "Sum of Pipe Degrees",
    "cluster-crossing": "Number of Cluster-Border Edge Crossings",
    "time_ns": "Total Time",
    "time_make_reduced_ns": "Make Reduced Time",
    "time_solve_reduced_ns": "Solve Reduced Time",
    "time_embed_ns": "Embed Time",
    "undo_ops": "Number of Operations",
    "init_stats.bicon_max_size": "Max. Size of a Bicon. Comp.",
    "init_stats.bicon_sum_size": "Overall Size of all Biconnected Components",
    "init_stats.top_pipe": "Max. Pipe Degree",
    "reduced_stats.bicon_max_size": "Max. Size of a Bicon. Comp.",
    "pipe-total-deg": "Total Pipe Degree",
    "exit_code": "Result",
    "mode": "Mode",
}

PTYPES = {
    "bicon_bicon_diff_cc": "Block-Block Pipes, diff comps",
    "bicon_bicon_same_cc": "Block-Block Pipes, same comps",
    "bicon_cut": "Block-Cut Pipes",
    "cut_cut": "Cut-Cut Pipes",
    "small": "Tiny Pipes"
}
for ptype, ptype_name in PTYPES.items():
    LABELS[f"init_stats.pipe_types.{ptype}"] = f"Number of {ptype_name}"
    LABELS[f"init_stats.pipe_types_degrees.{ptype}"] = f"Total Degree of {ptype_name}"


def get_label(l: str):
    if l.endswith("-frac"):
        return "Overhead over Baseline"
    if l in LABELS:
        return LABELS[l]
    l = l.removeprefix("stats.")
    if l in LABELS:
        return LABELS[l]
    l, _, _ = l.partition(".")
    if l in LABELS:
        return LABELS[l]
    else:
        return l


# %%

def p(obj, path, default=None):
    for seg in path.split("."):
        try:
            obj = obj.get(seg)
        except (IndexError, AttributeError):
            return default
    return obj


# %%

MARKERS = [
              (4, 0, 0),
              '^',
              (5, 1, 0),
              'o',
              (4, 1, 0),
              'v',
              (6, 1, 0),
              'X',
              (4, 0, 45),
              '<',
              (5, 0, 0),
              'P',
              (4, 1, 45),
              '>',
              (6, 0, 0)
          ] * 2

HATCHES = [
    '/', 'o', '\\', 'x', '|', 'O', '*', '.',
]


def hatch_bars(ax, hatches=HATCHES):
    lhs = ax.get_legend().legend_handles
    cols = (len(ax.patches) // len(lhs))
    for nr, (var, h) in enumerate(zip(reversed(lhs), cycle(hatches))):
        var.set_hatch(h + h)
        for bar in ax.patches[nr * cols: (nr + 1) * cols]:
            bar.set_hatch(h)
