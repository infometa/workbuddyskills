"""Offline argv and subprocess contracts; no login, resource creation or cloud calls."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'omics_cli.py'
SPEC = importlib.util.spec_from_file_location('task_omics_cli', SCRIPT)
wrapper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wrapper)


class BuilderTests(unittest.TestCase):
    def setUp(self):
        self.cli = wrapper.OmicsCLI('/test tools/omics')

    def test_existing_wdl_and_nf_paths_keep_meaning(self):
        wdl = self.cli.build_run(wdl='inputs/main.wdl', input_json='values.json', name='sample',
                                 main='main.wdl', update_app_id='app-old', release_name='v2')
        self.assertEqual(wdl, ['/test tools/omics', 'run', '-o', 'table', '--wdl', 'inputs/main.wdl',
                               '--input', 'values.json', '--name', 'sample', '--main', 'main.wdl',
                               '--update', 'app-old', '--release-name', 'v2'])
        nf = self.cli.build_run(nf_cos_path='cos://bucket/nf/', name='nf-job', nf_version='24.04.3',
                               nf_resume=True, nf_config='settings.config', nf_profile='docker,test',
                               nf_report=True, volume_id='vol-1', environment='env-1')
        self.assertIn('--nf-resume', nf)
        self.assertIn('--nf-report', nf)
        for flag, value in (('--nf', 'cos://bucket/nf/'), ('--nf-version', '24.04.3'),
                            ('--nf-profile', 'docker,test'), ('--volume-id', 'vol-1'),
                            ('--environment', 'env-1')):
            self.assertEqual(nf[nf.index(flag) + 1], value)
        self.assertNotIn('--project', nf)
        self.assertNotIn('--dry-run', nf)

    def test_direct_workflow_override_is_transported_without_shell_or_schema_rewrite(self):
        patch_text = 'steps:\n  - name: folding\n    inputs:\n      - name: sequence\n        content: "A; $(not-a-command)"\n'
        for source in ({'lambda_file': 'workflow with space.yaml'},
                       {'lambda_text': 'version: 1\nsteps: []\n'},
                       {'lambda_cos': 'cos://bucket/workflow.yaml'}):
            with self.subTest(source=source):
                command = self.cli.build_run(**source, override_text=patch_text,
                                             project='prj-1', environment='env-2', dry_run=True)
                self.assertEqual(command[command.index('--override-text') + 1], patch_text)
                self.assertEqual(command[command.index('--project') + 1], 'prj-1')
                self.assertEqual(command[command.index('--environment') + 1], 'env-2')
                self.assertIn('--dry-run', command)
                self.assertNotIn('--param', command)
                self.assertNotIn('--output-prefix', command)

    def test_public_and_private_lambda_keep_their_original_selector(self):
        for selector in ('public_app', 'app'):
            with self.subTest(selector=selector):
                command = self.cli.build_run(**{selector: 'app-source'},
                                             param=['name=sample A', 'text=a,b=c'],
                                             param_json=['settings={"a":true}'],
                                             param_output=['result=cos://bucket/results/'],
                                             omit_input=['optional'], use_example=False,
                                             agent_project=True, dry_run=True)
                self.assertIn('--' + selector.replace('_', '-'), command)
                self.assertEqual(command.count('--param'), 2)
                self.assertIn('text=a,b=c', command)
                self.assertIn('--use-example=false', command)
                self.assertIn('--agent-project', command)
                self.assertNotIn('--lambda-text', command)

    def test_direct_source_rejects_application_only_fields(self):
        fields = {'input_json': 'input.json', 'param': ['x=1'], 'param_json': ['x=1'],
                  'param_output': ['out=cos://b/o/'], 'omit_input': ['x'],
                  'use_example': False, 'target_version': 'version-1'}
        for key, value in fields.items():
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, 'schema'):
                self.cli.build_run(lambda_file='task.yaml', **{key: value})

    def test_mutual_exclusions_and_stdin_are_rejected(self):
        for kwargs in ({}, {'wdl': 'a', 'lambda_file': 'b'},
                       {'lambda_file': 'a', 'lambda_build': True},
                       {'lambda_file': 'a', 'override_file': 'b', 'override_text': 'c'},
                       {'lambda_file': '-', 'override_file': '-'},
                       {'app': 'a', 'input_json': '-', 'override_file': '-'},
                       {'app': 'a', 'input_json': 'b', 'template_id': 'c'},
                       {'nf_cos_path': 'cos://b/nf/', 'update_app_id': 'a'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.cli.build_run(**kwargs)

    def test_explicit_project_conflict_does_not_silently_choose_a_target(self):
        for method, kwargs in ((self.cli.build_run, {'app': 'app-1'}),
                               (self.cli.build_status, {}),
                               (self.cli.build_debug, {'run_uuid': 'run-1'}),
                               (self.cli.build_list_apps, {})):
            with self.subTest(method=method.__name__), self.assertRaises(ValueError):
                method(**kwargs, project='prj-1', agent_project=True)
            with self.subTest(empty=method.__name__), self.assertRaises(ValueError):
                method(**kwargs, project=' ')

    def test_no_fake_preview_or_nonexistent_wdl_output_flag(self):
        for source in ({'wdl': 'main.wdl'}, {'nf_cos_path': 'cos://b/nf/'}):
            with self.subTest(source=source), self.assertRaisesRegex(ValueError, 'dry-run'):
                self.cli.build_run(**source, dry_run=True)
        with self.assertRaisesRegex(ValueError, '没有 --output-dir'):
            self.cli.build_run(wdl='main.wdl', output_dir='cos://b/out/')
        with self.assertRaisesRegex(ValueError, '字符串列表'):
            self.cli.build_run(app='app-1', param='x=1')

    def test_lambda_build_and_explicit_values_are_preserved(self):
        with self.assertRaisesRegex(ValueError, 'image'):
            self.cli.build_run(lambda_build=True)
        command_json = '["python", "script.py", "--label", "a b"]'
        command = self.cli.build_run(lambda_build=True, image='r/app@sha256:abc',
                                     command_json=command_json, cpu=0, memory=4,
                                     lambda_input=['{"name":"input","content":"abc"}'],
                                     lambda_output=['{"name":"result","path":"out.txt"}'],
                                     env=['A=x,y=z', 'A=next'], output_prefix='cos://b/out/')
        self.assertEqual(command[command.index('--command-json') + 1], command_json)
        self.assertEqual(command[command.index('--cpu') + 1], '0')
        self.assertEqual(command.count('--env'), 2)
        self.assertIn('A=x,y=z', command)

    def test_debug_exposes_evidence_flags_and_same_project_without_config_change(self):
        command = self.cli.build_debug(run_uuid='run-1', job_id='job-2', output='json',
                                       project='prj-3', with_stdout=True, with_trace=True,
                                       with_reports=True, app_type='LAMBDA')
        self.assertEqual(command, ['/test tools/omics', 'debug', '-o', 'json', '--project', 'prj-3',
                                    '--run', 'run-1', '--job', 'job-2', '--type', 'LAMBDA',
                                    '--with-stdout', '--with-trace', '--with-reports'])
        self.assertEqual(self.cli.build_status('group-1', 'json', agent_project=True),
                         ['/test tools/omics', 'status', '-o', 'json', '--agent-project', 'group-1'])
        with self.assertRaises(ValueError):
            self.cli.build_debug(run_group_id='group-1', job_id='job-2')

    def test_application_and_storage_discovery_preserve_scope(self):
        self.assertIn('--project', self.cli.build_list_apps(project='p'))
        self.assertEqual(self.cli.build_list_cos_bucket(environment_id='e'),
                         ['/test tools/omics', 'list', 'cos-bucket', '-o', 'json', '--environment', 'e'])
        command = self.cli.build_list_public_apps(parent_app='collection', app_type='LAMBDA', keyword='fold')
        self.assertIn('--parent-app', command)
        self.assertIn('--type', command)
        self.assertIn('--keyword', command)
        with self.assertRaises(ValueError):
            self.cli.build_list_public_apps(public_app_id='cm-one', keyword='fold')


class ExecutionTests(unittest.TestCase):
    def invoke_main(self, arguments, result=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        result = result or subprocess.CompletedProcess([], 0, '{"Ready":true}\n', '')
        with patch.object(sys, 'argv', [str(SCRIPT), '--cli-path', '/fake tools/omics', *arguments]), \
                patch.object(wrapper.subprocess, 'run', return_value=result) as run, \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exit_info:
                wrapper.main()
        return exit_info.exception.code, stdout.getvalue(), stderr.getvalue(), run

    def test_run_dry_run_calls_cli_and_json_stdout_stays_parseable(self):
        patch_text = 'steps:\n  - name: score\n    inputs: []\n'
        code, stdout, stderr, run = self.invoke_main([
            'run', '--lambda-file', 'workflow file.yaml', '--override-text', patch_text,
            '--agent-project', '--environment', 'env-1', '--dry-run', '-o', 'json'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), {'Ready': True})
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], '/fake tools/omics')
        self.assertIn('--dry-run', args[0])
        self.assertEqual(args[0][args[0].index('--override-text') + 1], patch_text)
        self.assertFalse(kwargs.get('shell', False))
        self.assertNotIn('PRINT ONLY', stderr)

    def test_print_only_modes_never_execute_or_claim_platform_validation(self):
        for flag in ('--print-command', '--dry-run'):
            with self.subTest(flag=flag):
                code, stdout, stderr, run = self.invoke_main([
                    flag, 'run', '--lambda-text', 'image: x;y $(literal)', '--dry-run'])
                self.assertEqual(code, 0)
                run.assert_not_called()
                self.assertIn('未执行 CLI 或平台校验', stderr)
                self.assertEqual(shlex.split(stdout)[-1], '--dry-run')
                self.assertIn('image: x;y $(literal)', shlex.split(stdout))

    def test_nonzero_debug_retains_partial_json_and_error_details(self):
        payload = '{"Status":{"Status":"FAILED"},"JobLogs":[{"StderrError":"denied"}]}\n'
        result = subprocess.CompletedProcess([], 1, payload, 'GetRunCalls failed\n')
        code, stdout, stderr, run = self.invoke_main([
            'debug', '--run', 'run-1', '--with-stdout', '--project', 'prj-1', '-o', 'json'], result)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(stdout)['JobLogs'][0]['StderrError'], 'denied')
        self.assertIn('GetRunCalls failed', stderr)
        self.assertIn('--with-stdout', run.call_args[0][0])

    def test_parameter_error_and_project_conflict_do_not_spawn_cli(self):
        for argv in (['run', '--lambda-file', 'a', '--input', 'b'],
                     ['run', '--app', 'a', '--project', 'p', '--agent-project'],
                     ['run', '--app', 'a', '--use-example', 'nope']):
            with self.subTest(argv=argv):
                code, _, _, run = self.invoke_main(argv)
                self.assertNotEqual(code, 0)
                run.assert_not_called()

    def test_registered_schema_values_survive_argparse(self):
        code, _, _, run = self.invoke_main([
            'run', '--public-app', 'cm-1', '--param', 'label=a b',
            '--param', 'list=x,y', '--param-json', 'obj={"x": [1, 2]}',
            '--use-example=false', '--dry-run'])
        self.assertEqual(code, 0)
        command = run.call_args[0][0]
        self.assertEqual(command.count('--param'), 2)
        self.assertIn('obj={"x": [1, 2]}', command)
        self.assertIn('--use-example=false', command)

    def test_legacy_local_wdl_is_still_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            wdl = Path(directory) / 'main.wdl'
            wdl.write_text('version 1.0\nworkflow test {}\n')
            code, _, _, run = self.invoke_main(['run', '--wdl', str(wdl), '--name', 'test'])
        self.assertEqual(code, 0)
        self.assertIn('--wdl', run.call_args[0][0])
        self.assertNotIn('--dry-run', run.call_args[0][0])


if __name__ == '__main__':
    unittest.main()
