"""Offline contract tests: fake CLI only, no login/network/platform resources."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "query_run_log.py"
spec = importlib.util.spec_from_file_location("query_run_log", SCRIPT)
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


class IsolatedCliEnvironment(unittest.TestCase):
    def setUp(self):
        environment = {key: value for key, value in os.environ.items() if key != "OMICS_CLI_PATH"}
        clean = patch.dict(os.environ, environment, clear=True)
        clean.start()
        self.addCleanup(clean.stop)


class ArgumentTests(IsolatedCliEnvironment):
    def command(self, *argv):
        return query.build_command(query.parse_args(argv))

    def test_scope_and_lambda_job(self):
        self.assertEqual(self.command("--run-uuid", "run-a", "-p", "p-a", "--job", "tes-a", "--with-stdout"),
                         ["omics", "debug", "--run", "run-a", "--project", "p-a", "--job", "tes-a", "--with-stdout", "-o", "json"])
        self.assertEqual(self.command("--run-uuid", "run-a", "--agent-project", "--type", "LAMBDA")[-5:],
                         ["--agent-project", "--type", "LAMBDA", "-o", "json"])

    def test_scope_is_left_to_cli_when_omitted(self):
        self.assertEqual(self.command("--run-group-id", "group-a"), ["omics", "debug", "group-a", "-o", "json"])

    def test_status_shapes(self):
        self.assertEqual(self.command("--status", "--agent-project"), ["omics", "status", "--agent-project", "-o", "json"])
        self.assertEqual(self.command("--status", "--run-group-id", "group-a", "--project", "p-a"),
                         ["omics", "status", "group-a", "--project", "p-a", "-o", "json"])

    def test_invalid_args_fail_before_starting_cli(self):
        invalid = [[], ["--run-uuid", "u", "--run-group-id", "g"],
                   ["--run-uuid", "u", "-p", "p", "--agent-project"],
                   ["--run-uuid", "u", "--status"], ["--status", "--with-stdout"],
                   ["--run-group-id", "g", "--job", "j"], ["--run-uuid", "u", "--env", "prod"],
                   ["--run-uuid", "u", "--run-uin", "123"], ["--run-uuid", "  "],
                   ["--run-uuid", "u", "-p", ""], ["--run-group-id=--help"],
                   ["--run-uuid", "u\x00"], ["--run-uuid", "u", "--omics-cli", "omics\x00"],
                   ["--run-uuid", "u", "--timeout", "nan"], ["--run-uuid", "u", "--timeout", "-1"]]
        with patch.object(query.subprocess, "run") as run:
            for argv in invalid:
                with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                    query.main(argv)
                self.assertEqual(exc.exception.code, 2)
            run.assert_not_called()

    def test_command_plan_does_not_require_cli(self):
        stream = io.StringIO()
        with patch.object(query.subprocess, "run") as run, contextlib.redirect_stdout(stream):
            self.assertEqual(query.main(["--run-uuid", "u", "--print-command", "--omics-cli", "/not/installed"]), 0)
        run.assert_not_called()
        self.assertEqual(json.loads(stream.getvalue())["mode"], "command_plan")

    def test_cli_selection_prefers_explicit_then_environment(self):
        with patch.dict(os.environ, {"OMICS_CLI_PATH": "/private/connector/omics"}):
            self.assertEqual(self.command("--run-uuid", "u")[0], "/private/connector/omics")
            self.assertEqual(self.command("--run-uuid", "u", "--omics-cli", "/explicit/omics")[0], "/explicit/omics")

    def test_empty_environment_binding_is_an_error_not_a_path_fallback(self):
        with patch.dict(os.environ, {"OMICS_CLI_PATH": ""}), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            query.parse_args(["--run-uuid", "u"])
        self.assertEqual(error.exception.code, 2)


class EvidenceTests(IsolatedCliEnvironment):
    def collect(self, response, exit_code=0, stderr="", argv=None):
        result = subprocess.CompletedProcess([], exit_code, json.dumps(response), stderr)
        with patch.object(query.subprocess, "run", return_value=result):
            return query.collect(query.parse_args(argv or ["--run-uuid", "u"]))

    def test_task_failure_is_not_query_failure(self):
        data, code = self.collect({"AppType": "LAMBDA", "Status": {"Status": "Failed", "ErrorMessage": "file missing"}})
        self.assertEqual(code, 0)
        self.assertFalse(data["collection"]["incomplete"])
        self.assertEqual(data["response"]["Status"]["ErrorMessage"], "file missing")

    def test_partial_json_survives_nonzero_cli(self):
        data, code = self.collect({"RunUuid": "u", "Calls": [{"JobId": "tes-a"}]}, 2, "GetRunStatus failed")
        self.assertEqual(code, 2)
        self.assertEqual(data["response"]["Calls"][0]["JobId"], "tes-a")
        self.assertTrue(data["collection"]["incomplete"])

    def test_best_effort_errors_and_truncation_on_exit_zero(self):
        data, code = self.collect({"JobLogs": [{"Stderr": "partial", "StderrTruncated": True,
                                               "StdoutError": "403", "PodEventsError": "unavailable"}]})
        self.assertEqual(code, 0)
        self.assertTrue(data["collection"]["incomplete"])
        self.assertEqual(data["collection"]["retrieval_error_fields"],
                         ["response.JobLogs[0].StdoutError", "response.JobLogs[0].PodEventsError"])
        self.assertEqual(data["collection"]["truncated_fields"], ["response.JobLogs[0].StderrTruncated"])

    def test_status_empty_list_is_valid_but_wrong_shape_is_not(self):
        data, code = self.collect([], argv=["--status"])
        self.assertEqual((code, data["response"]), (0, []))
        data, code = self.collect([])
        self.assertEqual(code, 1)
        self.assertIn("JSON", data["wrapper_error"])

    def test_status_nil_slice_is_a_valid_empty_result(self):
        data, code = self.collect(None, argv=["--status"])
        self.assertEqual(code, 0)
        self.assertIsNone(data["response"])
        self.assertFalse(data["collection"]["incomplete"])
        self.assertNotIn("cli_stdout", data)
        _, code = self.collect(None)
        self.assertEqual(code, 1)

    def test_non_json_failure_is_visible_and_redacted(self):
        result = subprocess.CompletedProcess([], 1, "old CLI", "GET https://example.invalid/log?q-signature=FIXTURE_SECRET failed")
        with patch.object(query.subprocess, "run", return_value=result):
            data, code = query.collect(query.parse_args(["--run-uuid", "u"]))
        self.assertEqual(code, 1)
        self.assertEqual(data["cli_stdout"], "old CLI")
        self.assertNotIn("FIXTURE_SECRET", json.dumps(data))

    def test_timeout_preserves_complete_partial_json(self):
        exc = subprocess.TimeoutExpired(["omics"], 1, output=b'{"RunUuid":"u"}', stderr=b"timeout")
        with patch.object(query.subprocess, "run", side_effect=exc):
            data, code = query.collect(query.parse_args(["--run-uuid", "u"]))
        self.assertEqual(code, 124)
        self.assertEqual(data["response"], {"RunUuid": "u"})
        self.assertTrue(data["collection"]["incomplete"])

    def test_missing_cli_is_explicit(self):
        with patch.object(query.subprocess, "run", side_effect=FileNotFoundError("missing")):
            data, code = query.collect(query.parse_args(["--run-uuid", "u"]))
        self.assertEqual(code, 127)
        self.assertIn("无法启动", data["wrapper_error"])

    def test_redacts_nested_credentials_and_signed_urls(self):
        original = {"SessionId": "FIXTURE_A", "Meta": '{"SecretKey":"FIXTURE_B"}',
                    "Stderr": "X-Session-Id: FIXTURE_C\nAuthorization: Bearer FIXTURE_D\nsecret_key=FIXTURE_E\n"
                              "GET https://user:FIXTURE_F@example.invalid/object?sig=FIXTURE_G#FIXTURE_H\nNoSuchKey result.tsv"}
        text = json.dumps(query.redact(original))
        for letter in "ABCDEFGH":
            self.assertNotIn("FIXTURE_" + letter, text)
        self.assertIn("NoSuchKey result.tsv", text)
        self.assertIn("example.invalid/object?REDACTED", text)

    def test_fake_executable_runs_without_auth_file_and_without_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            fake_cli = path / "fake omics"
            fake_cli.write_text("#!" + sys.executable + "\nimport json,sys\n"
                                "print(json.dumps({'RunUuid':'u','received_args':sys.argv[1:]}))\n"
                                "sys.exit(3)\n")
            fake_cli.chmod(0o755)
            marker = path / "unwanted"
            run_id = "u;touch${IFS}" + str(marker)
            env = dict(os.environ, HOME=directory)
            result = subprocess.run([sys.executable, str(SCRIPT), "--omics-cli", str(fake_cli),
                                     "--run-uuid", run_id, "--agent-project"],
                                    capture_output=True, text=True, env=env, check=False)
            self.assertEqual(result.returncode, 3, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["response"]["received_args"], ["debug", "--run", run_id, "--agent-project", "-o", "json"])
            self.assertFalse(marker.exists())
            self.assertFalse((path / ".omics-platform-cli").exists())

    def test_bound_cli_executes_instead_of_path_cli_and_never_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            path_bin = path / "path-bin"
            path_bin.mkdir()
            marker = path / "path-cli-was-used"
            for executable, label in ((path_bin / "omics", "path"),
                                      (path / "bound omics", "bound"),
                                      (path / "explicit omics", "explicit")):
                source = "#!" + sys.executable + "\nimport json\n"
                if label == "path":
                    source += "from pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('used')\n"
                source += "print(json.dumps({'selected':" + repr(label) + "}))\n"
                executable.write_text(source)
                executable.chmod(0o755)
            environment = dict(os.environ, HOME=directory, PATH=str(path_bin) + os.pathsep + os.environ.get("PATH", ""),
                               OMICS_CLI_PATH=str(path / "bound omics"))
            argv = [sys.executable, str(SCRIPT), "--run-uuid", "u"]
            result = subprocess.run(argv, capture_output=True, text=True, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["response"]["selected"], "bound")
            result = subprocess.run(argv + ["--omics-cli", str(path / "explicit omics")],
                                    capture_output=True, text=True, env=environment)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["response"]["selected"], "explicit")
            environment["OMICS_CLI_PATH"] = str(path / "missing cli")
            result = subprocess.run(argv, capture_output=True, text=True, env=environment)
            self.assertEqual(result.returncode, 127, result.stderr)
            self.assertIn("无法启动", json.loads(result.stdout)["wrapper_error"])
            self.assertFalse(marker.exists())
            self.assertFalse((path / ".omics-platform-cli").exists())


if __name__ == "__main__":
    unittest.main()
