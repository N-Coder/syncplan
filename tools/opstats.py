import gzip
import json
import os
import sys
import traceback
from collections import defaultdict
from dataclasses import dataclass, fields, field
from datetime import datetime

import pymongo
from pymongo import UpdateMany
from tqdm import tqdm
from tqdm.contrib import tmap

from utils import batched, stats_collection


@dataclass
class OpStats:
    count: int = 0
    op_time: int = 0
    pc_time: int = 0
    pc_new_nodes: int = 0
    pc_scan_nodes: int = 0
    pot_red: int = 0
    intrs_pot_red: int = 0
    meta: dict = field(default_factory=dict)

    def incr(self, op):
        self.count += 1
        if op["op"] == "MAKE_SPQR":
            self.pc_time += op["op_time_ns"]
            self.pc_scan_nodes += op["bicon_size"]
            return
        for k, v in op.items():
            if isinstance(v, (float, int)):
                if v > 1_000_000_000_000:
                    tqdm.write(f"Document for {op['op']} contains a too high value {k}={v}!")
                    return  # ignore
                if v < 0:
                    tqdm.write(f"Document for {op['op']} contains a negative value {k}={v}!")
                    return  # ignore

        cycle_len = op.get("cycle_len", 0)
        if op["op"] == "SIMPLIFY_TOROIDAL" and cycle_len != 1:
            tqdm.write(f"SIMPLIFY_TOROIDAL cycle_len {op.get('cycle_len', 0)} != 1: {op}")
            self.meta.setdefault("cycle_lengths", []).append(cycle_len)

        if op["op"].startswith("solvedReduced-"):
            for k, v in op.items():
                if k in ["op", "op_time_ns"]: continue
                self.meta[k] = v

        old_pot = op.get("deg", 3) - 3
        self.op_time += op["op_time_ns"]
        if "pc_time_ns" in op:
            self.pc_time += op["pc_time_ns"]
            if op["u_cv"]:
                self.pc_scan_nodes += op["v_bicon_size"]
            else:
                self.pc_scan_nodes += op["u_bicon_size"]

            if "v_pc_time_ns" in op:
                self.pc_time += op["v_pc_time_ns"]
                self.pc_scan_nodes += op["v_bicon_size"]
                self.pc_new_nodes += op["i_p_nodes"] + op["i_c_nodes"]
                new_pot = op["i_p_node_degs"] - 3 * op["i_p_nodes"]
                int_pot = op["p_node_degs"] - 3 * op["p_nodes"]
                self.intrs_pot_red += max(int_pot - new_pot, 0)
            else:
                self.pc_new_nodes += op["p_nodes"] + op["c_nodes"]
                new_pot = op["p_node_degs"] - 3 * op["p_nodes"]

            if op["op"].startswith("SIMPLIFY"):
                self.pot_red += old_pot
            else:  # PROPAGATE
                self.pot_red += max(old_pot - new_pot, 0)
        else:
            if op["op"] == "CONTRACT_BICON":
                self.pot_red += old_pot
            elif op["op"] == "ENCAPSULATE_CONTRACT":
                self.pot_red += (op["u_blocks"] + op["v_blocks"] - 2) * 1.5

    def as_dict(self):
        result = {**self.meta}
        for f in fields(OpStats):
            if f.name == "meta": continue
            val = getattr(self, f.name)
            if val:
                result[f.name] = val
        return result


def update_key(data):
    return {
        k: (datetime.fromisoformat(v) if k.endswith("_time") else v)
        for k, v in data.items()
        if k in ["file", "method", "mode", "flags", "start_time", "end_time", "exit_code"]
    }


def process_file(file):
    if not file.endswith("json.gz"):
        return None

    failure = None
    with gzip.open(file, "rt") as f:
        try:
            l = next(f)
            opstats = json.loads(l)
        except (json.JSONDecodeError, StopIteration) as e:
            failure = e

        try:
            l = next(f)
            if not l.strip():
                l = next(f)
            data = json.loads(l)
            l = next(f)
            env = json.loads(l)
        except (json.JSONDecodeError, StopIteration) as e:
            tqdm.write(f'Failed to extract doc ID for {file}! {e}')
            return None

    if data.get("method") != "PQPlanarity":
        return None
    if env.get("SP_COLLECTION", "stats") != os.getenv("SP_COLLECTION", "stats"):
        return None
    if failure:
        ec = data.get("exit_code", -1)
        if ec not in [124, 137]:
            tqdm.write(f'Error  {ec :4d} {file} {failure}')
        return UpdateMany(update_key(data), {"$set": {
            "opstats_error": str(failure)}}), file

    try:
        # tqdm.write(f'{doc["file"]} {doc["mode"]} {doc["start_time"]}')
        ops = defaultdict(OpStats)
        for op in opstats:
            ops[op["op"]].incr(op)
            if op["op"] == "BATCH_SPQR":
                for op in op["ops"]:
                    ops["BATCH_SPQR:" + op["op"]].incr(op)
        # tqdm.write(str({k: v for k, v in ops.items()}))
    except Exception as e:
        tqdm.write(f'Fail   {data.get("exit_code", -1):4d} {file} {e}')
        return None

    return UpdateMany(update_key(data), {"$set": {
        "opstats": {k: v.as_dict() for k, v in ops.items()}}}), file
    # tqdm.write(repr(updates[-1]))


def send_updates(updates, uuids):
    try:
        res = stats_collection().bulk_write(updates, ordered=False)
        tqdm.write(f"Update {len(updates):4d} {res.bulk_api_result}")
        if res.matched_count != len(updates):
            tqdm.write(f"Matched count does not equal number of updates!")
            if len(uuids) != len(updates):
                tqdm.write(f"Got {len(uuids)} UUIDs but {len(updates)} updates!")
            for id, upd in zip(uuids, updates):
                cnt = stats_collection().count_documents(filter=upd._filter)
                if cnt != 1:
                    tqdm.write(f"Could not identify document {upd._filter} for {id} (found {cnt})!")
    except Exception:
        with tqdm.external_write_mode(file=sys.stdout):
            print("Could not update documents!")
            traceback.print_exc(file=sys.stdout)
            print()
            print(uuids)
            print()
            print(updates)
            print()


def process_files(files):
    results = filter(bool, tmap(process_file, files, smoothing=0, mininterval=1, maxinterval=10, file=sys.stdout))
    zipped = list(zip(*results))
    if not zipped:
        tqdm.write("Got no updates to send!")
        return
    updates, uuids = zipped
    send_updates(list(updates), uuids)


if __name__ == "__main__":
    stats_collection().create_index([
        ("file", pymongo.ASCENDING),
        ("method", pymongo.ASCENDING),
        ("mode", pymongo.ASCENDING),
    ])

    from tqdm.contrib.concurrent import thread_map

    dir = "./"
    batches = list(batched((f for f in os.listdir(dir) if f.endswith("json.gz")), 1000))
    thread_map(process_files, batches, smoothing=0, mininterval=1, maxinterval=10, desc="Total", file=sys.stdout)
