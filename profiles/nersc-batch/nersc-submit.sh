#!/bin/bash

# module load python
# mamba activate snakemake

cd "$1" || exit 1
version=$(basename "$1")

rm -rf .snakemake

logdir=".slurm/$(date +'%Y%m%dT%H%M%SZ')"
mkdir -p "$logdir"

simids=$(python -c '
import json

with open("inputs/simprod/config/tier/raw/l200a/simconfig.json") as f:
    simids = json.load(f).keys()

for s in simids:
    print(f"pdf.{s}", end=" ")
')

for s in $simids; do
    job="${version}_$s"
    echo ">>> $job"

    if squeue --me --format '%200j' | grep "$job"; then
        echo "job already queued"
        continue
    fi

    snakemake --config simlist="$s" --dry-run | grep 'Nothing to be done' && continue

    echo "Submitting..."
    # https://docs.nersc.gov/development/shifter/faq-troubleshooting/#failed-to-lookup-image
    sbatch \
        --nodes 1 \
        --ntasks-per-node=1 \
        --account m2676 \
        --constraint cpu \
        --time 12:00:00 \
        --qos regular \
        --licenses scratch,cfs \
        --job-name "$job" \
        --output "$logdir/$s.log" \
        --error "$logdir/$s.log" \
        --image "legendexp/legend-base:latest" \
        --wrap "
            srun snakemake \
                --profile workflow/profiles/nersc-interactive \
                --shadow-prefix $PSCRATCH \
                --config simlist=$s
        "
done
