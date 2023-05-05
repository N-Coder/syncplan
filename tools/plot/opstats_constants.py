GROUPS = {
    "all": [
        # "time_ns",
        "timeout_ns",
        "time_embed_ns", "time_check_ns",
        # ],
        # "time_ns": [
        "time_init_ns", "time_make_reduced_ns", "time_solve_reduced_ns",
        # "time_embed_ns", "time_check_ns"
    ],
    "time_make_reduced_ns": [
        "BATCH_SPQR.op_time",
        "CONTRACT_BICON.op_time",
        "ENCAPSULATE_CONTRACT.op_time",
        "PROPAGATE_BICON.op_time",
        "PROPAGATE_CUT.op_time",
        "SIMPLIFY_TERMINAL.op_time",
        "SIMPLIFY_TRANSITIVE.op_time",

        "PROPAGATE_BICON.pc_time",
        "PROPAGATE_CUT.pc_time",
        "SIMPLIFY_TERMINAL.pc_time",
        "SIMPLIFY_TRANSITIVE.pc_time",
    ],
    "BATCH_SPQR.op_time": [
        "BATCH_SPQR:PROPAGATE_BICON.op_time",
        "BATCH_SPQR:PROPAGATE_CUT.op_time",
        "BATCH_SPQR:SIMPLIFY_TERMINAL.op_time",
        "BATCH_SPQR:SIMPLIFY_TRANSITIVE.op_time",

        "BATCH_SPQR:MAKE_SPQR.pc_time",
        "BATCH_SPQR:PROPAGATE_BICON.pc_time",
        "BATCH_SPQR:PROPAGATE_CUT.pc_time",
        "BATCH_SPQR:SIMPLIFY_TERMINAL.pc_time",
        "BATCH_SPQR:SIMPLIFY_TRANSITIVE.pc_time",
    ],
    "time_solve_reduced_ns": [
        "solvedReduced-applyEmbedding.op_time",
        "solvedReduced-deriveSAT.op_time",
        "solvedReduced-deriveSPQR.op_time",
        "solvedReduced-embedSPQR.op_time",
        "solvedReduced-makeWheels.op_time",
        "solvedReduced-solveSAT.op_time",
    ],
    "time_embed_ns": [
        # "embed-PQPlanarity::ResetIndices.op_time",
        "embed-UndoContractBiconnected.op_time",
        "embed-UndoContractBipartite.op_time",
        "embed-UndoContractSmall.op_time",
        "embed-UndoConvertSmall.op_time",
        "embed-UndoEncapsulate.op_time",
        "embed-UndoInitCluster.op_time",
        "embed-UndoMakeWheel.op_time",
        "embed-UndoPropagate.op_time",
        "embed-UndoSimplify.op_time",
    ],
}

NAMES = {
    "all": "Total",

    "BATCH_SPQR:MAKE_SPQR.pc_time": "Compute SPQR",
    "BATCH_SPQR:PROPAGATE_BICON.op_time": "Propagate(block)",
    "BATCH_SPQR:PROPAGATE_CUT.op_time": "Propagate(cut)",
    "BATCH_SPQR:SIMPLIFY_TERMINAL.op_time": "Simplify(terminal)",
    "BATCH_SPQR:SIMPLIFY_TRANSITIVE.op_time": "Simplify(transitive)",
    "BATCH_SPQR:PROPAGATE_BICON.pc_time": "ET: Propagate(block)",
    "BATCH_SPQR:PROPAGATE_CUT.pc_time": "ET: Propagate(cut)",
    "BATCH_SPQR:SIMPLIFY_TERMINAL.pc_time": "ET: Simplify(terminal)",
    "BATCH_SPQR:SIMPLIFY_TRANSITIVE.pc_time": "ET: Simplify(transitive)",

    "embed-PQPlanarity::ResetIndices.op_time": "ResetIndices",
    "embed-UndoInitCluster.op_time": "Undo Reduce from Cluster",
    "embed-UndoConvertSmall.op_time": "Undo ConvertSmall",
    "embed-UndoMakeWheel.op_time": "Undo MakeWheel",
    "embed-UndoEncapsulate.op_time": "Undo Encapsulate",
    "embed-UndoContractBiconnected.op_time": "Undo Join(blocks)",
    "embed-UndoContractBipartite.op_time": "Undo Join(cuts)",
    "embed-UndoContractSmall.op_time": "Undo Join(small)",
    "embed-UndoPropagate.op_time": "Undo Propagate",
    "embed-UndoSimplify.op_time": "Undo Simplify",

    "ENCAPSULATE_CONTRACT.op_time": "EncapsulateAndJoin",
    "CONTRACT_BICON.op_time": "JoinBlocks",
    "PROPAGATE_BICON.op_time": "Propagate(block)",
    "PROPAGATE_CUT.op_time": "Propagate(cut)",
    "SIMPLIFY_TERMINAL.op_time": "Simplify(terminal)",
    "SIMPLIFY_TRANSITIVE.op_time": "Simplify(transitive)",
    "PROPAGATE_BICON.pc_time": "ET: Propagate(block)",
    "PROPAGATE_CUT.pc_time": "ET: Propagate(cut)",
    "SIMPLIFY_TERMINAL.pc_time": "ET: Simplify(terminal)",
    "SIMPLIFY_TRANSITIVE.pc_time": "ET: Simplify(transitive)",
    "BATCH_SPQR.op_time": "Batch SPQR",

    "solvedReduced-makeWheels.op_time": "MakeWheels",
    "solvedReduced-deriveSPQR.op_time": "Compute SPQR",
    "solvedReduced-deriveSAT.op_time": "Derive SAT",
    "solvedReduced-solveSAT.op_time": "Solve SAT",
    "solvedReduced-embedSPQR.op_time": "Embed SPQR",
    "solvedReduced-applyEmbedding.op_time": "Apply Embedding",

    "timeout_ns": "Timeouts",
    "time_ns": "Test",
    "time_test_ns": "Test",
    "time_verify_ns": "Verify",

    "time_init_ns": "Reduce from Cluster",
    "time_make_reduced_ns": "Make Reduced",
    "time_solve_reduced_ns": "Solve Red.",
    "time_embed_ns": "Embed",
    "time_check_ns": "Verify",

    "contract_time": "Enc.AndJoin",
    "propagate_time": "Propagate",
    "simplify_time": "Simplify",
    "emb_tree_time": "Emb. Trees",
}

CONTRACTS = ["CONTRACT_BICON", "ENCAPSULATE_CONTRACT"]
PROPAGATES = ["PROPAGATE_BICON", "PROPAGATE_CUT"]
SIMPLIFYS = ["SIMPLIFY_TERMINAL", "SIMPLIFY_TRANSITIVE", "SIMPLIFY_TOROIDAL"]
PREFIXES = ["", "BATCH_SPQR:"]

OPSTATS_SUMS = {
    "contract_time": (PREFIXES, CONTRACTS, [".op_time"]),
    "propagate_time": (PREFIXES, PROPAGATES, [".op_time"]),
    "simplify_time": (PREFIXES, SIMPLIFYS, [".op_time"]),
    "emb_tree_time": (PREFIXES, PROPAGATES + SIMPLIFYS + ["MAKE_SPQR"], [".pc_time"]),
    "contract_counts": (PREFIXES, CONTRACTS, [".count"]),
    "propagate_counts": (PREFIXES, PROPAGATES, [".count"]),
    "simplify_counts": (PREFIXES, SIMPLIFYS, [".count"]),
    "emb_tree_scanned": (PREFIXES, PROPAGATES + SIMPLIFYS + ["MAKE_SPQR"], [".pc_scan_nodes"]),
}

# more plots?
# solvedReduced-makeWheels.wheels
#
# embed UndoMakeWheel count
# embed UndoMakeWheel op time
#
# embed UndoSimplify count
# embed UndoSimplify op time
#
# undo ops
#
# reduced stats bicon max size
# reduced stats bicon sum size
# reduced stats nodes
# reduced stats q vertices
# reduced stats bicon
# reduced stats connected