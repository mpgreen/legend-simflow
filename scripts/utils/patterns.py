# Copyright (C) 2023 Luigi Pertoldi <gipert@pm.me>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https:#www.gnu.org/licenses/>.

"""Prepare pattern strings to be used in Snakemake rules.

Extra keyword arguments are typically interpreted as variables to be
substituted in the returned (structure of) strings. They are passed to
:func:`snakemake.io.expand`.

Definitions:
- ``simid``: string identifier for the simulation run
- ``simjob``: one job of a simulation run (corresponds to one macro file and one
  output file)
- ``jobid``: zero-padded integer (i.e., a string) used to label a simulation job
"""
from __future__ import annotations

import json
from pathlib import Path

from snakemake.io import expand


def simjob_rel_basename(**kwargs):
    """Formats a partial output path for a `simid` and `jobid`."""
    return expand("{simid}/{simid}_{jobid}", **kwargs, allow_missing=True)[0]


def run_command(config, tier):
    """Returns command to build files in tier `tier` prefixed by environment."""
    return "{swenv} " + config["runcmd"][tier]


def log_file_path(config, **kwargs):
    """Formats a log file path for a `simid` and `jobid`."""
    pat = str(
        Path(config["paths"]["log"]) / "{tier}" / (simjob_rel_basename() + ".log")
    )
    return expand(pat, **kwargs, allow_missing=True)[0]


def benchmark_file_path(config, **kwargs):
    """Formats a benchmark file path for a `simid` and `jobid`."""
    pat = str(
        Path(config["paths"]["benchmarks"])
        / "{tier}"
        / (simjob_rel_basename() + ".tsv")
    )
    return expand(pat, **kwargs, allow_missing=True)[0]


def plots_file_path(config, **kwargs):
    """Formats a benchmark file path for a `simid` and `jobid`."""
    pat = str(Path(config["paths"]["plots"]) / "{tier}" / "{simid}")
    return expand(pat, **kwargs, allow_missing=True)[0]


def genmacro_log_file_path(config, **kwargs):
    """Formats a log file path for a `simid` and `jobid`."""
    return expand(
        str(
            Path(config["paths"]["log"])
            / "macros"
            / "{tier}"
            / (simjob_rel_basename() + ".log")
        ),
        **kwargs,
        allow_missing=True,
    )[0]


def template_macro_dir(config, **kwargs):
    """Returns the directory path to the macro templates for the current `tier`."""
    tier = expand("{tier}", **kwargs, allow_missing=True)[0]
    return Path(config["paths"]["config"]) / "tier" / tier / config["experiment"]


# ver, raw tiers


def macro_gen_inputs(config, tier, simid, **kwargs):
    """Return inputs for the Snakemake rules that generate macros."""
    tdir = template_macro_dir(config, tier=tier)

    with (tdir / "simconfig.json").open() as f:
        sconfig = json.load(f)[simid]

    if "template" not in sconfig:
        msg = "simconfig.json blocks must define a 'template' field."
        raise RuntimeError(msg)

    expr = {
        "template": str(tdir / sconfig["template"]),
        "cfgfile": str(tdir / "simconfig.json"),
    }
    for k, v in expr.items():
        expr[k] = expand(v, **kwargs, allow_missing=True)[0]
    return expr


def input_simjob_filename(config, **kwargs):
    """Returns the full path to the input file for a `simid`, `tier` and job index."""
    tier = kwargs.get("tier", None)

    if tier is None:
        msg = "the 'tier' argument is mandatory"
        raise RuntimeError(msg)

    expr = str(
        Path(config["paths"]["macros"])
        / f"{tier}"
        / (simjob_rel_basename() + config["filetypes"]["input"][tier])
    )
    return expand(expr, **kwargs, allow_missing=True)[0]


def output_simjob_filename(config, **kwargs):
    """Returns the full path to the output file for a `simid`, `tier` and job index."""
    tier = kwargs.get("tier", None)

    if tier is None:
        msg = "the 'tier' argument is mandatory"
        raise RuntimeError(msg)

    expr = str(
        Path(config["paths"][f"tier_{tier}"])
        / (simjob_rel_basename() + config["filetypes"]["output"][tier])
    )
    return expand(expr, **kwargs, allow_missing=True)[0]


def input_simid_filenames(config, n_macros, **kwargs):
    """Returns the full path to `n_macros` input files for a `simid`. Needed by
    script that generates all macros for a `simid`.
    """
    pat = input_simjob_filename(config, **kwargs)
    jobids = expand("{id:>04d}", id=list(range(n_macros)))
    return expand(pat, jobid=jobids, **kwargs, allow_missing=True)


def output_simid_filenames(config, n_macros, **kwargs):
    """Returns the full path to `n_macros` output files for a `simid`."""
    pat = output_simjob_filename(config, **kwargs)
    jobids = expand("{id:>04d}", id=list(range(n_macros)))
    return expand(pat, jobid=jobids, **kwargs, allow_missing=True)


def smk_ver_filename_for_raw(config, wildcards):
    """Returns the vertices file needed for the 'raw' tier job, if needed. Used
    as lambda function in the `build_tier_raw` Snakemake rule."""
    tdir = template_macro_dir(config, tier="raw")

    with (tdir / "simconfig.json").open() as f:
        sconfig = json.load(f)[wildcards.simid]

    if "vertices" in sconfig:
        return output_simjob_filename(config, tier="ver", simid=sconfig["vertices"])
    else:
        return []
