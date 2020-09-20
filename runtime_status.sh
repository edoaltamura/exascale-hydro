#!/bin/bash -l

# Prints out the status of the SLURM jobs in a nice way.

function summary() {
    squeue "$@" | awk '
    BEGIN {
        abbrev["R"]="(Running)"
        abbrev["PD"]="(Pending)"
        abbrev["CG"]="(Completing)"
        abbrev["F"]="(Failed)"
    }
    NR>1 {a[$5]++}
    END {
        for (i in a) {
            printf "%-2s %-12s %d\n", i, abbrev[i], a[i]
        }
    }'
}

export summary