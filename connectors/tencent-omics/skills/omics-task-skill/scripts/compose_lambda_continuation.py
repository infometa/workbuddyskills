#!/usr/bin/env python3
"""Compose a continuation from a frozen workflow and actual published artifacts.

No submission, network access, scientific computation or new step templates.
JSON output is accepted by ``omics run --lambda-file``.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False).encode()).hexdigest()


def named(items, label):
    result = {}
    for item in items:
        name = item.get("name")
        if not isinstance(name, str) or not name or name in result:
            raise ValueError(f"{label}: missing or duplicate name {name!r}")
        result[name] = item
    return result


def graph(workflow):
    if workflow.get("apiVersion") != "omics.lambda.workflow/v1":
        raise ValueError("Expected a frozen omics.lambda.workflow/v1 definition")
    steps = named(workflow.get("steps", []), "steps")
    if not steps:
        raise ValueError("Workflow has no steps")
    parents = {}
    for name, step in steps.items():
        dependencies = step.get("dependency", [])
        if not isinstance(dependencies, list) or len(set(dependencies)) != len(dependencies):
            raise ValueError(f"{name}: invalid dependencies")
        parents[name] = set(dependencies)
        for inp in named(step.get("inputs", []), f"{name}.inputs").values():
            ref = inp.get("from")
            if ref is None:
                continue
            if not isinstance(ref, dict) or set(ref) != {"step", "output"}:
                raise ValueError(f"{name}.{inp['name']}: unsupported from reference")
            producer = steps.get(ref["step"])
            if producer is None:
                raise ValueError(f"{name}: unknown producer {ref['step']}")
            outputs = named(producer.get("outputs", []), f"{ref['step']}.outputs")
            if ref["output"] not in outputs:
                raise ValueError(f"{name}: unknown output {ref}")
            if inp.get("type", "FILE") != outputs[ref["output"]].get("type", "FILE"):
                raise ValueError(f"{name}: input/output type mismatch for {ref}")
            parents[name].add(ref["step"])
        if not parents[name] <= steps.keys() or name in parents[name]:
            raise ValueError(f"{name}: invalid dependency")
    pending = set(steps)
    ordered = []
    while pending:
        ready = [name for name in steps if name in pending and not (parents[name] & pending)]
        if not ready:
            raise ValueError("Workflow contains a dependency cycle")
        ordered.extend(ready)
        pending.difference_update(ready)
    return steps, parents, ordered


def descendants(seeds, parents):
    result = set(seeds)
    while True:
        following = result | {name for name, deps in parents.items() if deps & result}
        if following == result:
            return result
        result = following


def compose(definition, debug, selected=None, start=None, invalidated=(), task=False):
    run = definition.get("RunUuid")
    if not run or debug.get("RunUuid") != run:
        raise ValueError("Frozen definition and debug must identify the same source RunUuid")
    snapshot = definition.get("SnapshotJson")
    if isinstance(snapshot, str):
        snapshot = json.loads(snapshot)
    if not isinstance(snapshot, dict) or snapshot.get("RunUUID") != run:
        raise ValueError("Missing or mismatched frozen SnapshotJson.RunUUID")
    for frozen_key, debug_key in (("ProjectID", "ProjectId"), ("EnvironmentID", "EnvironmentId")):
        if not snapshot.get(frozen_key) or snapshot[frozen_key] != debug.get(debug_key):
            raise ValueError(f"Frozen definition and debug disagree on {debug_key}")
    workflow = deepcopy(snapshot.get("Workflow", {}))
    steps, parents, order = graph(workflow)
    if bool(selected) == bool(start):
        raise ValueError("Choose explicit steps or a starting step")
    seeds = set(selected or [start])
    if not seeds <= steps.keys():
        raise ValueError(f"Unknown selected steps: {sorted(seeds - steps.keys())}")
    chosen = seeds if selected else descendants(seeds, parents)
    if not set(invalidated) <= steps.keys():
        raise ValueError("Unknown invalidated step")
    stale = descendants(invalidated, parents)
    if task and len(chosen) != 1:
        raise ValueError("Task output requires exactly one selected step")
    artifacts = {}
    for artifact in debug.get("Artifacts", []):
        key = (artifact.get("Step"), artifact.get("Name"))
        artifacts.setdefault(key, []).append(artifact)
    calls = {}
    for call in debug.get("Calls", []):
        calls.setdefault(call.get("CallName"), []).append(call)
    reused, removed_urls, output_steps, control_edges = [], [], [], []
    for name in order:
        if name not in chosen:
            continue
        step = deepcopy(steps[name])
        external_data_parents = set()
        for inp in step.get("inputs", []):
            ref = inp.get("from")
            if ref is None or ref["step"] in chosen:
                continue
            producer = ref["step"]
            if producer in stale:
                raise ValueError(f"{name}.{inp['name']}: {producer} is invalidated; rerun it")
            candidates = artifacts.get((producer, ref["output"]), [])
            if len(candidates) != 1:
                raise ValueError(f"{name}.{inp['name']}: need one published artifact for {ref}")
            artifact = candidates[0]
            if artifact.get("State") != "Ready":
                raise ValueError(f"{name}.{inp['name']}: artifact is not Ready")
            if artifact.get("Type") != inp.get("type", "FILE"):
                raise ValueError(f"{name}.{inp['name']}: published artifact type differs")
            if artifact.get("EnvironmentId") != debug["EnvironmentId"]:
                raise ValueError(f"{name}.{inp['name']}: artifact environment differs")
            url = artifact.get("URL", "")
            parts = urlsplit(url)
            if (parts.scheme != "cos" or not parts.netloc or not parts.path.strip("/")
                    or parts.query or parts.fragment or any(c.isspace() for c in url)):
                raise ValueError(f"{name}.{inp['name']}: expected an actual unsigned COS artifact URL")
            publication = []
            for call in calls.get(producer, []):
                if call.get("ParentId", run) != run:
                    raise ValueError(f"{producer}: call belongs to a different Run")
                runtime = call.get("Runtime", {})
                if isinstance(runtime, str):
                    runtime = json.loads(runtime)
                for receipt in runtime.get("outputResults", []):
                    if (receipt.get("name") == ref["output"] and receipt.get("url") == url
                            and receipt.get("type") == artifact["Type"]
                            and receipt.get("status") == "PUBLISHED"):
                        publication.append({"call_run_id": call.get("RunId"),
                                            "job_id": call.get("JobId"), "receipt": receipt})
            if not publication:
                raise ValueError(f"{name}.{inp['name']}: no matching source PUBLISHED receipt; "
                                 "an existing object alone does not prove this Run published it")
            inp.pop("from")
            inp.pop("content", None)
            inp["url"] = url
            external_data_parents.add(producer)
            reused.append({
                "consumer_step": name, "input": inp["name"], "source_run_uuid": run,
                "source_step": producer, "source_output": ref["output"],
                "url": url, "type": artifact["Type"], "publication_state": artifact["State"],
                "source_step_definition_sha256": digest(steps[producer]),
                "source_call_statuses": [c.get("Status") for c in calls.get(producer, [])],
                "publication_receipts": publication,
            })
        # An explicit success dependency is not satisfied merely by publishing
        # one file before the producer failed elsewhere.
        removed_control = (set(steps[name].get("dependency", [])) |
                           (parents[name] - external_data_parents)) - chosen
        for dependency in sorted(removed_control):
            matching = calls.get(dependency, [])
            if (dependency in stale or len(matching) != 1
                    or matching[0].get("Status") != "SUCCESS"
                    or matching[0].get("ParentId", run) != run):
                raise ValueError(f"{name}: removed control dependency {dependency} has not succeeded")
            control_edges.append({"step": name, "satisfied_dependency": dependency,
                                  "source_run_uuid": run})
        dependencies = [dep for dep in order if dep in parents[name] & chosen]
        if dependencies:
            step["dependency"] = dependencies
        else:
            step.pop("dependency", None)
        # Never overwrite the frozen run's explicitly fixed output destinations.
        for output in step.get("outputs", []):
            if "url" in output:
                removed_urls.append({"step": name, "output": output["name"],
                                     "previous_url": output.pop("url")})
        output_steps.append(step)
    output = deepcopy(workflow)
    output["steps"] = output_steps
    dropped_exports = {}
    if "outputs" in output:
        exports = output["outputs"]
        if not isinstance(exports, dict):
            raise ValueError("Unsupported workflow exports")
        for alias, ref in list(exports.items()):
            if ref.get("step") not in chosen:
                dropped_exports[alias] = exports.pop(alias)
        if not exports:
            output.pop("outputs")
    graph(output)
    if task:
        output = output_steps[0]
        output.pop("dependency", None)
        output["apiVersion"] = "omics.lambda/v1"
    source_status = debug.get("Status", {})
    manifest = {
        "schema": "omics.lambda.continuation.v1", "source_run_uuid": run,
        "source_run_status": source_status.get("Status") if isinstance(source_status, dict) else source_status,
        "project_id": debug["ProjectId"], "environment_id": debug["EnvironmentId"],
        "source_effective_spec_hash": definition.get("EffectiveSpecHash"),
        "source_workflow_sha256": digest(workflow), "continuation_sha256": digest(output),
        "selected_steps": [name for name in order if name in chosen],
        "invalidated_steps": sorted(stale), "reused_artifacts": reused,
        "satisfied_control_dependencies": control_edges, "removed_fixed_output_urls": removed_urls,
        "omitted_exports": dropped_exports,
        "scope": "New execution of selected steps; the source Run keeps its original status.",
        "validation": {
            "graph_and_publication_binding": "checked",
            "scientific_input_compatibility": "verify input identity, method, parameters, labels and seeds",
            "submission": "not submitted; dry-run and inspect the effective definition before running",
        },
    }
    return output, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--definition", required=True, help="omics run-definition --format json output")
    parser.add_argument("--debug", required=True, help="omics debug -o json output for the same Run")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--steps", nargs="+", help="Exact subgraph to execute")
    choice.add_argument("--from-step", help="This step and all its descendants")
    parser.add_argument("--invalidated-step", action="append", default=[],
                        help="Changed step whose previous output and descendants cannot be reused")
    parser.add_argument("--as-task", action="store_true", help="Extract one step as a standalone Task")
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        output, manifest = compose(read_json(args.definition), read_json(args.debug),
                                   args.steps, args.from_step, args.invalidated_step, args.as_task)
        destinations = [Path(args.output), Path(args.manifest)]
        if destinations[0].resolve() == destinations[1].resolve() or any(p.exists() for p in destinations):
            raise ValueError("Use distinct new output and manifest paths")
        manifest["evidence_files"] = {
            key: {"path": str(Path(path).resolve()), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}
            for key, path in (("definition", args.definition), ("debug", args.debug))
        }
        for path, value in zip(destinations, (output, manifest)):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
        print(json.dumps({"output": str(destinations[0]), "manifest": str(destinations[1]),
                          "steps": manifest["selected_steps"], "submitted": False}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, f"Cannot compose continuation: {exc}\n")


if __name__ == "__main__":
    main()
