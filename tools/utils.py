import itertools
import os
from datetime import time
from pathlib import Path

import pymongo
import sh

try:
    from itertools import pairwise
except ImportError:
    def pairwise(iterable):
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

ALL_JOB_TYPES = [
    "CConnected", "HananiTutte", "HananiTutte-f", "ILP",
    "PQPlanarity", "PQPlanarity-p", "PQPlanarity-p-b", "PQPlanarity-p-b-s",
    # batch SPQR, by degree / contract first / last
    "PQPlanarity-c", "PQPlanarity-i", "PQPlanarity-c-i",  # no contract bicon-bicon and / or intersect PQ trees
    "PQPlanarity-p-c", "PQPlanarity-p-i", "PQPlanarity-p-c-i",
    "PQPlanarity-p-b-c", "PQPlanarity-p-b-i", "PQPlanarity-p-b-c-i",
    "PQPlanarity-p-b-s-c", "PQPlanarity-p-b-s-i", "PQPlanarity-p-b-s-c-i",
    "PQPlanarity-r", "PQPlanarity-c-i-r",  # random
    "PQPlanarity-a", "PQPlanarity-c-i-a",  # ascending degree
    "PQPlanarity-b", "PQPlanarity-c-i-b",  # contract first
    "PQPlanarity-b-s", "PQPlanarity-c-i-b-s",  # contract last
]


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


def db() -> pymongo.database.Database:
    global db

    kwargs = {}
    f = Path(__file__).parent / "mongo-password.txt"
    if f.exists():
        kwargs["password"] = f.read_text().strip()
    obj = pymongo.MongoClient(
        os.getenv("SP_MONGO_URL"),
        serverSelectionTimeoutMS=2000, **kwargs
    ).get_database(os.getenv("SP_MONGO_DB"))

    def db_obj():
        return obj

    db = db_obj
    return obj


def stats_collection_name():
    return os.getenv("SP_COLLECTION", "stats")


def stats_collection():
    return db().get_collection(stats_collection_name())


def index_file():
    return os.getenv("SP_INDEX", "index.csv")


def max_file_nr():
    maxidx = int(sh.tail(index_file(), lines=1).split(",")[0])
    if "SP_MAX_IDX" in os.environ:
        maxidx = min(maxidx, int(os.getenv("SP_MAX_IDX")))
    return maxidx


def resolve_file_nr(file_nr):
    # FILE=$(grep "^$SLURM_ARRAY_TASK_ID," index.csv | cut -d "," -f 2)
    return sh.grep(f"^{file_nr},", index_file()).split(",")[1]


def hashsum(filename):
    return sh.md5sum(filename).split(" ")[0].strip()


def get_allowed_cpus():
    with open("/proc/%s/status" % os.getpid(), "rt") as f:
        for l in f:
            if l.startswith("Cpus_allowed_list"):
                return l.split(":")[1].strip()
    raise RuntimeError("/proc/$PID/status contains no Cpus_allowed_list")


def get_allowed_cpu_list():
    for r in get_allowed_cpus().split(','):
        t = list(map(int, r.split('-')))
        yield from range(t[0], t[-1] + 1)


def parse_timeout(val):
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            t = time.fromisoformat(val)
            return ((t.hour * 60) + t.minute) * 60 + t.second
    else:
        return val


def printClusters(c):
    return f"{c.nCount()}[{' '.join(map(printClusters, c.children))}]"


def clusterCrossings(CG):
    for e in CG.constGraph().edges:
        u = CG.clusterOf(e.source()).depth()
        v = CG.clusterOf(e.target()).depth()
        p = CG.commonCluster(e.source(), e.target()).depth()
        yield u + v - (2 * p)
