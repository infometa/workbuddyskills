import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "continuation", Path(__file__).parents[1] / "scripts/compose_lambda_continuation.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def fixture():
    steps = []
    for name, upstream in (("prepare", None), ("analyze", "prepare"), ("plot", "analyze")):
        step = {"name": name, "image": "example@sha256:fixed", "command": ["run", name],
                "outputs": [{"name": "data", "type": "FILE", "path": "${workdir}/result",
                             "url": f"cos://bucket/old/{name}"}], "timeoutSeconds": 0}
        if upstream:
            step["dependency"] = [upstream]
            step["inputs"] = [{"name": "data", "type": "FILE", "path": "inputs/data",
                               "from": {"step": upstream, "output": "data"}}]
        steps.append(step)
    workflow = {"apiVersion": "omics.lambda.workflow/v1", "name": "analysis", "steps": steps,
                "outputs": {"report": {"step": "plot", "output": "data"}}}
    definition = {"RunUuid": "run-a", "SnapshotJson": {
        "RunUUID": "run-a", "ProjectID": "project", "EnvironmentID": "environment",
        "Workflow": workflow}}
    debug = {"RunUuid": "run-a", "ProjectId": "project", "EnvironmentId": "environment",
             "Status": {"Status": "FAILED"},
             "Calls": [{"CallName": "prepare", "Status": "SUCCESS", "ParentId": "run-a",
                        "Runtime": {"outputResults": [{"name": "data", "type": "FILE",
                            "url": "cos://bucket/source/prepare/data", "status": "PUBLISHED"}]}},
                       {"CallName": "analyze", "Status": "FAILED"},
                       {"CallName": "plot", "Status": "CANCELED"}],
             "Artifacts": [{"Step": "prepare", "Name": "data", "Type": "FILE",
                            "State": "Ready", "EnvironmentId": "environment",
                            "URL": "cos://bucket/source/prepare/data"}]}
    return definition, debug


class ContinuationTests(unittest.TestCase):
    def test_failed_parent_reuses_published_step_without_recomputing_it(self):
        definition, debug = fixture()
        original = copy.deepcopy((definition, debug))
        result, manifest = MOD.compose(definition, debug, start="analyze")
        self.assertEqual([s["name"] for s in result["steps"]], ["analyze", "plot"])
        self.assertEqual(result["steps"][0]["inputs"][0]["url"], "cos://bucket/source/prepare/data")
        self.assertNotIn("from", result["steps"][0]["inputs"][0])
        self.assertEqual(result["steps"][1]["inputs"][0]["from"]["step"], "analyze")
        self.assertEqual(result["steps"][1]["dependency"], ["analyze"])
        self.assertEqual(manifest["source_run_status"], "FAILED")
        self.assertEqual((definition, debug), original)
        self.assertTrue(all("url" not in s["outputs"][0] for s in result["steps"]))
        self.assertTrue(all(s["timeoutSeconds"] == 0 for s in result["steps"]))

    def test_extract_one_task_preserves_command_and_image(self):
        definition, debug = fixture()
        result, manifest = MOD.compose(definition, debug, selected=["analyze"], task=True)
        self.assertEqual(result["apiVersion"], "omics.lambda/v1")
        self.assertEqual(result["command"], ["run", "analyze"])
        self.assertNotIn("dependency", result)
        self.assertEqual(manifest["omitted_exports"]["report"]["step"], "plot")

    def test_expected_or_failed_publication_cannot_be_reused(self):
        for state in ("Expected", "Unconfirmed", "Failed"):
            with self.subTest(state=state):
                definition, debug = fixture()
                debug["Artifacts"][0]["State"] = state
                with self.assertRaisesRegex(ValueError, "not Ready"):
                    MOD.compose(definition, debug, start="analyze")

    def test_parameter_change_invalidates_descendant_caches(self):
        definition, debug = fixture()
        with self.assertRaisesRegex(ValueError, "invalidated"):
            MOD.compose(definition, debug, start="analyze", invalidated=["prepare"])

    def test_ambiguous_or_wrong_type_artifact_fails(self):
        definition, debug = fixture()
        debug["Artifacts"].append(copy.deepcopy(debug["Artifacts"][0]))
        with self.assertRaisesRegex(ValueError, "one published"):
            MOD.compose(definition, debug, start="analyze")
        debug["Artifacts"].pop()
        debug["Artifacts"][0]["Type"] = "DIRECTORY"
        with self.assertRaisesRegex(ValueError, "type differs"):
            MOD.compose(definition, debug, start="analyze")

    def test_other_run_cannot_supply_artifacts(self):
        definition, debug = fixture()
        debug["RunUuid"] = "different-run"
        with self.assertRaisesRegex(ValueError, "same source"):
            MOD.compose(definition, debug, start="analyze")

    def test_control_dependency_needs_real_success(self):
        definition, debug = fixture()
        workflow = definition["SnapshotJson"]["Workflow"]
        workflow["steps"][1]["inputs"] = []
        debug["Calls"][0]["Status"] = "FAILED"
        with self.assertRaisesRegex(ValueError, "control dependency"):
            MOD.compose(definition, debug, start="analyze")

    def test_existing_object_without_this_runs_publication_cannot_be_reused(self):
        definition, debug = fixture()
        debug["Calls"][0]["Runtime"] = "{}"
        with self.assertRaisesRegex(ValueError, "no matching source PUBLISHED"):
            MOD.compose(definition, debug, start="analyze")

    def test_explicit_success_dependency_is_not_satisfied_by_partial_publication(self):
        definition, debug = fixture()
        debug["Calls"][0]["Status"] = "EXECUTOR_ERROR"
        with self.assertRaisesRegex(ValueError, "control dependency"):
            MOD.compose(definition, debug, start="analyze")

    def test_control_only_dependency_must_belong_to_the_source_run(self):
        definition, debug = fixture()
        definition["SnapshotJson"]["Workflow"]["steps"][1]["inputs"] = []
        debug["Calls"][0]["ParentId"] = "other-run"
        with self.assertRaisesRegex(ValueError, "control dependency"):
            MOD.compose(definition, debug, start="analyze")

    def test_publication_must_match_exact_url_type_and_name(self):
        for field, wrong in (("url", "cos://bucket/other"), ("name", "other"),
                             ("type", "DIRECTORY"), ("status", "FAILED")):
            with self.subTest(field=field):
                definition, debug = fixture()
                debug["Calls"][0]["Runtime"]["outputResults"][0][field] = wrong
                with self.assertRaisesRegex(ValueError, "no matching source PUBLISHED"):
                    MOD.compose(definition, debug, start="analyze")

    def test_cycle_rejected(self):
        definition, debug = fixture()
        definition["SnapshotJson"]["Workflow"]["steps"][0]["dependency"] = ["plot"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            MOD.compose(definition, debug, start="analyze")


if __name__ == "__main__":
    unittest.main()
