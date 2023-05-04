#!/usr/bin/env python3

import csv
import json
import random
import shlex
import sys
import tempfile
import uuid
from collections import Counter
from datetime import datetime, timedelta
from json import JSONDecodeError
from os.path import join, relpath, normpath

import click
import pymongo.database
from click import UsageError
from tqdm import tqdm

from utils import *

TIME_WALL_CLOCK_KEY = "Elapsed (wall clock) time (h:mm:ss or m:ss)"

option_build_dir = click.option("--build-dir", default="../build-debug", envvar="SP_BUILD_DIR",
                                type=click.Path(exists=True, file_okay=False, resolve_path=True))


@click.group()
def cli():
    pass


@cli.command
def stash_db():
    if stats_collection().estimated_document_count() > 0:
        new_name = f"{stats_collection_name()}-{datetime.now().isoformat().replace(' ', '_')}"
        stats_collection().rename(new_name)


@cli.command(name="max-file-nr")
def cli_max_file_nr():
    print(max_file_nr())


@cli.command(name="resolve-file-nr")
@click.option("-n", "--file-nr", envvar="SLURM_ARRAY_TASK_ID", type=int)
def cli_resolve_file_nr(file_nr):
    print(resolve_file_nr(file_nr))


def profile(file, method, build_dir, timeout, timeout_ilp, likwid, **extras):
    mode = method
    method, *flags = method.split("-")
    flags = ["-" + f for f in flags]
    with tempfile.TemporaryDirectory(dir="/tmp", prefix="synplan-profile-") as tmpdir:
        err_lines = []
        stats = {}

        def handle_line(line):
            nonlocal stats
            try:
                stats = json.loads(line)
                if stats["method"] != method:
                    raise ValueError()
            except (JSONDecodeError, ValueError, AttributeError, TypeError, KeyError):
                err_lines.append(line)

        comm = sh
        time_out = tmpdir + "/time.txt"
        comm = comm.time.bake(verbose=True, output=time_out, _cwd=tmpdir).bake("--")
        if likwid:
            comm = comm.bake(shlex.split(likwid.format(
                cpus=get_allowed_cpus(), cpu=next(get_allowed_cpu_list()))))
        if timeout:
            comm = comm.timeout.bake(kill_after=10).bake(timeout)
        tool = os.getenv("SP_PROFILE_MODE", "c")
        comm = comm.bake(
            os.path.join(build_dir, f"profile-{tool}plan-likwid" if likwid else f"profile-{tool}plan"),
            os.path.abspath(file),
            "-l", 4, *flags
        )
        if tool == "c":
            comm = comm.bake("-m", method, "-t", timeout_ilp)
        comm = comm.bake(_err=handle_line, _out="/dev/null")

        data = {
            "file": file,
            "method": method,
            "mode": mode,
            "flags": flags,
            "start_time": datetime.now(),

            "file_dir": os.path.dirname(file),
            "file_name": os.path.basename(file),
            "timeout": str(timedelta(seconds=timeout)) if isinstance(timeout, int) else timeout,
            "timeout_ilp": timeout_ilp,

            **extras
        }

        try:
            comm()
            data["exit_code"] = 0
        except sh.ErrorReturnCode as err:
            data["exit_code"] = err.exit_code

        data["end_time"] = datetime.now()
        data["stats"] = stats
        data["errors"] = "\n".join(err_lines)

        time_output = []
        time_data = {}
        for line in open(time_out, "rt"):
            if ":" in line:
                line = line.strip()
                if line.startswith(TIME_WALL_CLOCK_KEY):
                    time_data[TIME_WALL_CLOCK_KEY] = line.removeprefix(TIME_WALL_CLOCK_KEY + ":").strip()
                    continue
                k, _, v = (s.strip() for s in line.partition(":"))
                try:
                    time_data[k] = int(v.removesuffix("%"))
                except ValueError:
                    try:
                        time_data[k] = float(v)
                    except ValueError:
                        time_data[k] = v
            else:
                time_output.append(line)

        data["time"] = time_data
        data["time_output"] = "".join(time_output)

        with open(tmpdir + "/pqplan_stats.json", "at") as f:
            f.write("\n")
            json.dump(data, f, separators=(',', ':'), default=str)
            f.write("\n")
            json.dump(dict(os.environ), f, separators=(',', ':'))
            f.write("\n")
            f.writelines(open(time_out, "rt"))
        extra_id = uuid.uuid4()
        extra_file = os.path.abspath(f"./{extra_id}.json.gz")
        data["extra_id"] = str(extra_id)
        data["extra_file"] = extra_file
        sh.gzip(tmpdir + "/pqplan_stats.json", "-c", _out=open(extra_file, "xb"))

        return data


@cli.command(name="profile")
@click.option("-m", "--method", default=ALL_JOB_TYPES[0], envvar="SP_METHOD",
              type=click.Choice(ALL_JOB_TYPES, case_sensitive=False))
@click.option("-n", "--file-nr", envvar="SLURM_ARRAY_TASK_ID", type=int, multiple=True)
@click.option("-f", "--file", type=click.Path(exists=True, dir_okay=False), multiple=True)
@click.option("-b", "--batch-size", type=int, envvar="SLURM_ARRAY_TASK_STEP")
@click.option("-s", "--no-mongo", is_flag=True)
@click.option("-v", "--verbose", is_flag=True)
@click.option("--likwid", default=None, envvar="SP_LIKWID")
@click.option("--timeout", default=None, type=parse_timeout, envvar="SP_TIMEOUT")
@click.option("--timeout-ilp", default="00:01:00", envvar="SP_TIMEOUT_ILP")
@option_build_dir
def cli_profile(no_mongo, verbose, **kwargs):
    file_nrs = kwargs.pop("file_nr", [])
    batch_size = kwargs.pop("batch_size", None)
    files = kwargs.pop("file", [])

    if file_nrs:
        if files:
            raise click.BadParameter(message="Specify either file or file-nr")
        elif batch_size:
            if len(file_nrs) > 1:
                raise click.BadParameter(message="Can only use one file-nr with batch-size")
            file_nr = file_nrs[0]
            calls = [{"file": resolve_file_nr(file_nr + offset), "file_nr": file_nr + offset,
                      "batch_start": file_nr, "batch_offset": offset, "batch_size": batch_size, **kwargs}
                     for offset in range(batch_size)
                     if file_nr + offset <= max_file_nr()]
        else:
            calls = [{"file": resolve_file_nr(nr), "file_nr": nr, "batch_size": len(file_nrs), **kwargs} for nr in
                     file_nrs]
    elif files:
        if batch_size and batch_size > 0:
            raise click.BadParameter(message="Can only use batch-size together with file-nr")
        calls = [{"file": file, "batch_size": len(files), **kwargs} for file in files]
    else:
        raise click.BadParameter(message="Specify either file or file-nr")

    for call in calls:
        data = profile(**call)
        if no_mongo:
            print(data)
        else:
            ins = stats_collection().insert_one(data)
            if verbose:
                print(ins.inserted_id)


@cli.command()
@click.option("-n", "--file-nr", "file_nrs", envvar="SLURM_ARRAY_TASK_ID", type=int, multiple=True)
@click.option("-f", "--file", "files", type=click.Path(exists=True, dir_okay=False), multiple=True)
@click.option("-b", "--batch-size", type=int, envvar="SLURM_ARRAY_TASK_STEP")
@click.option("-d", "--dir", type=click.Path(exists=True, dir_okay=True, file_okay=False), default=".")
@click.option("-t", "--thread_batch", type=int, default=1)
def read_opstats(file_nrs, files, batch_size, dir, thread_batch):
    if files:
        if batch_size and batch_size > 0:
            raise click.BadParameter(message="Can only use batch-size together with file-nr")
        if file_nrs:
            raise click.BadParameter(message="Specify either file or file-nr")
    else:
        files = sorted(os.path.join(dir, f) for f in os.listdir(dir) if f.endswith("json.gz"))
        if file_nrs:
            if batch_size:
                if len(file_nrs) > 1:
                    raise click.BadParameter(message="Can only use one file-nr with batch-size")
                file_nr = file_nrs[0]
                files = [files[file_nr + offset]
                         for offset in range(batch_size)
                         if file_nr + offset < len(files)]
            else:
                files = [files[nr] for nr in file_nrs]

    stats_collection().create_index([
        ("file", pymongo.ASCENDING),
        ("method", pymongo.ASCENDING),
        ("mode", pymongo.ASCENDING),
    ])

    from opstats import process_files
    if thread_batch > 1:
        from tqdm.contrib.concurrent import thread_map
        thread_map(process_files, list(batched(files, thread_batch)), smoothing=0, mininterval=1, maxinterval=10,
                   desc="Total", file=sys.stdout)
    else:
        process_files(files)


@cli.command()
def find_missing():
    stats_collection().create_index([
        ("mode", pymongo.ASCENDING),
        ("file_nr", pymongo.ASCENDING),
    ], background=True)
    for method in ALL_JOB_TYPES:
        occurences = Counter(doc["file_nr"] for doc in stats_collection().find({"mode": method}, {"file_nr": 1}))
        multiple = {nr: cnt for nr, cnt in occurences.items() if cnt >= 2}
        if multiple:
            print("Multiple entries:", multiple)
        found = set(occurences.keys())
        found.symmetric_difference_update(range(max_file_nr() + 1))
        ranges = []
        for idx in sorted(found):
            if ranges and idx == ranges[-1][1] + 1:
                ranges[-1][1] += 1
            else:
                ranges.append([idx, idx])
        ranges = [str(f) if f == t else f"{f}-{t}" for f, t in ranges]
        print(method, ", ".join(ranges))


@cli.command()
@click.option("-m", "--method", default=ALL_JOB_TYPES[0], envvar="SP_METHOD",
              type=click.Choice(ALL_JOB_TYPES, case_sensitive=False))
@click.option("-b", "--batch-size", type=int, envvar="SLURM_ARRAY_TASK_STEP", default=0)
def find_missing_prog(method, batch_size):
    stats_collection().create_index([
        ("mode", pymongo.ASCENDING),
        ("file_nr", pymongo.ASCENDING),
    ], background=True)
    found = set(doc["file_nr"] for doc in stats_collection().find({"mode": method}, {"file_nr": 1}))
    found.symmetric_difference_update(range(max_file_nr() + 1))
    # found.intersection_update(range(1001, max_file_nr() + 1))
    ranges = []
    for idx in sorted(found):
        if ranges and idx == ranges[-1][1] + 1:
            ranges[-1][1] += 1
        else:
            ranges.append([idx, idx])

    def str_range(r):
        f, t = r
        if f == t:
            return str(f)
        elif batch_size and t - f <= batch_size:
            return f"{f}-{t}"
        else:
            return f"{f}-{t}:{batch_size}"

    print(",".join(map(str_range, ranges)))


@cli.command()
def remove_duplicates():
    to_delete = []
    for method in ALL_JOB_TYPES:
        for k, g in itertools.groupby(stats_collection().find(
                {"mode": method}, {"_id": 1, "file_nr": 1, "start_time": 1}, sort=[("file_nr", 1), ("start_time", -1)]
        ), lambda d: d["file_nr"]):
            keep = next(g)
            to_delete.extend(g)
    print(stats_collection().bulk_write([pymongo.DeleteOne(d) for d in to_delete]).bulk_api_result)


@cli.command()
@click.option("--nodes", "-n", type=int, required=True, multiple=True)
@click.option("--edges", "-e", type=int, default=[None], multiple=True)
@click.option("--density", "-d", type=float, default=[None], multiple=True)
@click.option("--ccs", "-c", type=int, default=[1], multiple=True)
@click.option("--bcs", "-b", type=int, default=[None], multiple=True)
@click.option("--seed", "-s", type=int, default=[None], multiple=True)
@click.option("--format", "-f", default="gml")
@click.option("--out", "-o")
def random_graph(nodes, edges, density, ccs, bcs, seed, format, out):
    from ogdf_python import ogdf, cppinclude
    cppinclude("ogdf/basic/simple_graph_alg.h")
    cppinclude("ogdf/basic/extended_graph_alg.h")
    cppinclude("ogdf/basic/graph_generators/randomized.h")
    cppinclude("limits")
    ogdf.Logger.globalLogLevel(ogdf.Logger.Level.Alarm)

    for args in itertools.product(nodes, edges, density, ccs, bcs, seed):
        make_graph(*args, format=format, out=out)


def make_graph(nodes, edges, density, ccs, bcs, seed, format, out):
    from ogdf_python import ogdf, cppyy
    if seed is None:
        nl = cppyy.gbl.std.numeric_limits["int"]
        seed = random.randint(nl.lowest(), nl.max())
    print("Seed", seed)
    ogdf.setSeed(seed)
    random.seed(seed)

    if (edges is None) == (density is None):
        raise UsageError("specify either edges or density")
    elif edges is None:
        edges = round(nodes * density)

    if out is None:
        out = [("n", nodes), ("e", edges), ("c", ccs), ("b", bcs), ("s", seed)]
        out = "random-" + "-".join(f"{a}{b}" for a, b in out if b is not None)
    out = Path(out)
    if not out.suffix:
        out = out.with_suffix("." + format)
    if out.is_file():
        print("Skipping", out)
        return

    cc = {0, nodes}
    while len(cc) < ccs + 1:
        cc.add(random.randint(1, nodes - 1))
    cc = sorted(cc)
    print("Connected components", cc)

    if bcs:
        bc = {0, bcs}
        while len(bc) < ccs + 1:
            bc.add(random.randint(1, bcs - 1))
        bc = sorted(bc)
        print("Biconnected components", bc)
    else:
        bc = cc  # just ensure the right length, values won't be used

    G = ogdf.Graph()
    for (f_n, l_n), (f_b, l_b) in zip(pairwise(cc), pairwise(bc)):
        g = ogdf.Graph()
        n = l_n - f_n
        b = l_b - f_b
        e = round(edges * (n / nodes))
        if bcs:
            if b > 1:
                ogdf.randomPlanarCNBGraph(g, n, e, b)
            else:
                ogdf.randomPlanarBiconnectedGraph(g, n, e)
        else:
            ogdf.randomPlanarConnectedGraph(g, n, e)
        G.insert(g)

    bcc = ogdf.biconnectedComponents(G, ogdf.EdgeArray["int"](G, -1))
    ccc = ogdf.connectedComponents(G)
    print(f"Graph with {G.numberOfNodes()} nodes, {G.numberOfEdges()} edges, "
          f"{ccc} connected components, and {bcc} biconnected components.")

    print(out, ogdf.GraphIO.write(G, str(out)))


@cli.command()
@click.argument('filesdir')
@click.option('--rem-ccon/--keep-ccon', default=True)
def preprocess_files(filesdir, rem_ccon):
    from ogdf_python import ogdf, cppinclude, cppyy
    cppinclude("ogdf/basic/simple_graph_alg.h")
    cppinclude("ogdf/basic/extended_graph_alg.h")
    cppyy.add_include_path(normpath(join(__file__, "../../include/")))
    cppyy.add_include_path(normpath(join(__file__, "../../src/")))
    cppinclude("utils/Preprocess.cpp")
    ogdf.Logger.globalLogLevel(ogdf.Logger.Level.Alarm)

    count = 0
    for dirpath, dnames, fnames in os.walk(filesdir):
        for f in fnames:
            if f.endswith(".gml") or f.endswith(".graphml"):
                CG = G = None
                file = Path(dirpath) / f
                G = ogdf.Graph()
                CG = ogdf.ClusterGraph(G)
                ogdf.GraphIO.read(CG, G, str(file))
                if not ogdf.isPlanar(G):
                    print("Non-Planar", file)
                    file.rename(str(file) + ".nonplanar")
                elif CG.numberOfClusters() < 2:
                    print("Trivial", file)
                    file.rename(str(file) + ".trivial")
                elif rem_ccon and ogdf.isCConnected(CG):
                    print("CCon", file)
                    file.rename(str(file) + ".ccon")
                elif cppyy.gbl.preprocessClusterGraph(CG, G):
                    newname = str(file.with_stem(file.stem + "-preproc"))
                    if not ogdf.isPlanar(G):
                        print("Preprocessed", file, "(now non-planar)")
                        suffix = ".nonplanar"
                    elif CG.numberOfClusters() < 2:
                        print("Preprocessed", file, "(now trivial)")
                        suffix = ".trivial"
                    elif rem_ccon and ogdf.isCConnected(CG):
                        print("Preprocessed", file, "(now ccon)")
                        suffix = ".ccon"
                    else:
                        print("Preprocessed", file)
                        suffix = ""
                    if not ogdf.GraphIO.write(CG, newname):
                        print("Could not write", newname)
                    os.rename(newname, newname + suffix)
                    file.rename(str(file) + ".unpreproc")
                count += 1
                if count % 100 == 0:
                    print(count)


@cli.command()
@click.argument('filesdir')
@click.argument('indexfile', envvar="SP_INDEX")
@click.option('--ogdf/--no-ogdf', default=True)
@click.option('--mode', type=click.Choice(["pq", "cluster"], case_sensitive=False), default="cluster")
@click.option('--batch-size', '-b', default=100, type=int)
@option_build_dir
def make_index(filesdir, indexfile, ogdf, batch_size, build_dir, mode):
    indexdir = os.path.dirname(indexfile)
    files = [
        join(dirpath, f)
        for dirpath, dnames, fnames in os.walk(filesdir)
        for f in fnames
        if f.endswith(".gml") or f.endswith(".graphml")
    ]
    random.seed(123456789)
    random.shuffle(files)

    with open(indexfile, 'w', newline='') as csvfile:
        csvwriter = None

        it = iter(enumerate(tqdm(files)))
        while batch := tuple(itertools.islice(it, batch_size)):

            if ogdf:
                mk = sh.Command(f"make-{mode}-index", search_paths=[build_dir])
                lines = mk([t[1] for t in batch]).splitlines()
                meta = {j["file"]: j for j in (json.loads(l) for l in lines)}
            else:
                meta = {}

            for nr, file in batch:
                data = {
                    "nr": nr,
                    "file": relpath(file, indexdir),
                    "md5": hashsum(file),
                    "size": os.stat(file).st_size,
                }
                if mode == "pq":
                    pqfile = file + ".json"
                    data["pq-file"] = relpath(pqfile, indexdir)
                    data["pq-md5"] = hashsum(pqfile)
                    data["pq-size"] = os.stat(pqfile).st_size

                if ogdf:
                    if file not in meta:
                        tqdm.write(f"Got no OGDF data for {file}")
                    else:
                        data.update(meta[file])
                    if data["edges"] < 1:
                        continue

                if not csvwriter:
                    csvwriter = csv.DictWriter(csvfile, data.keys(), quoting=csv.QUOTE_MINIMAL)
                    csvwriter.writeheader()
                csvwriter.writerow(data)


if __name__ == "__main__":
    cli()
