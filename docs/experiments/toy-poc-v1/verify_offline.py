"""Produce safe offline evidence. All runtime dispatch is synthetic or blocked.
Run with -B -X utf8; optional -O verifies gates under Python optimization.
"""
import argparse
import ast
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import cli_runner as r
import test_cli_runner as tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--demo-export', action='store_true')
    args = parser.parse_args()
    source_names = ['cli_runner.py', 'harness.py', 'test_cli_runner.py', 'verify_offline.py']
    for name in source_names:
        ast.parse((r.ROOT / name).read_text(encoding='utf-8'))
    for name in ('tasks.json', 'small-test-plan.json', 'failed-launches-user-ledger.json'):
        r.strict_json((r.ROOT / name).read_text(encoding='utf-8-sig'))
    original = subprocess.Popen
    children = []
    def synthetic_children_only(argv, *call_args, **kwargs):
        # Actual subprocesses in this suite are Python fixtures or a PowerShell
        # junction fixture. A leaked native Codex call fails before spawn.
        executable = os.path.normcase(str(argv[0]))
        if executable == os.path.normcase(sys.executable):
            kind = 'python_fixture_child'
        elif Path(executable).name.lower() in ('powershell', 'powershell.exe'):
            kind = 'powershell_fixture_child'
        else:
            raise AssertionError('Unexpected subprocess in offline suite')
        children.append(kind)
        return original(argv, *call_args, **kwargs)
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    started = time.monotonic()
    with patch.object(subprocess, 'Popen', side_effect=synthetic_children_only), redirect_stdout(io.StringIO()):
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=2).run(suite)
        if args.demo_export and result.wasSuccessful():
            with tests.state() as (ledger, unused_project):
                fixture = lambda task, expert: tests.harness.reference(task) if expert else {'SYNTHETIC_bad': True}
                r.sequential(ledger, tests.dispatch(ledger, fixture))
                r.safe_export(ledger, r.PROJECT)
    wrapper = str(r.ROOT / 'run-poc.ps1').replace("'", "''")
    command = ("$t=$null; $e=$null; [System.Management.Automation.Language.Parser]::ParseFile('" +
               wrapper + "',[ref]$t,[ref]$e) | Out-Null; Write-Output $e.Count")
    parsed = subprocess.run(['powershell', '-NoProfile', '-Command', command],
                            capture_output=True, timeout=15)
    ps_errors = int(parsed.stdout.strip()) if parsed.returncode == 0 else None
    diff = subprocess.run(['git', 'diff', '--check'], cwd=r.PROJECT, capture_output=True, timeout=15)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=r.PROJECT, capture_output=True, timeout=15)
    hashes = {}
    for name in source_names + ['run-poc.ps1', 'tasks.json', 'small-test-plan.json']:
        raw = (r.ROOT / name).read_bytes()
        relative = 'docs/experiments/toy-poc-v1/' + name
        blob = subprocess.run(['git', 'show', 'HEAD:' + relative], cwd=r.PROJECT,
                              capture_output=True, timeout=15)
        hashes[name] = dict(working_tree_sha256=r.sha(raw), lf_sha256=r.sha(raw.replace(b'\r\n', b'\n')),
                           head_git_blob_sha256=r.sha(blob.stdout) if blob.returncode == 0 else None)
    reports = [(r.PROJECT / 'docs' / language / 'controller-audit-fixes-2026-10-01.md').read_text(encoding='utf-8')
               for language in ('en', 'ru')]
    def structure(text):
        return dict(sections=len(re.findall(r'^## ', text, re.M)),
                    table_rows=len(re.findall(r'^\|', text, re.M)),
                    links=re.findall(r'\]\(([^)]+)\)', text),
                    literals=re.findall(r'`([^`\n]+)`', text))
    parity = structure(reports[0]) == structure(reports[1])
    success = result.wasSuccessful() and not result.skipped and ps_errors == 0 and diff.returncode == 0 and parity
    evidence = dict(schema_version=1, kind='OFFLINE_REGRESSION_ONLY', generated_at=r.now(),
        status='passed' if success else 'failed', tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
        failed_tests=[test.id() for test, _ in result.failures + result.errors],
        elapsed_seconds=time.monotonic()-started, python_version=sys.version.split()[0],
        optimization=sys.flags.optimize, platform='Windows' if os.name == 'nt' else os.name,
        ast_files=source_names, strict_json_files=3, powershell_parser_errors=ps_errors,
        git_diff_check_exit=diff.returncode, bilingual_structure_and_literal_parity=parity,
        real_codex_launches=0, actual_model_success_demonstrated=False,
        fixture_children=children, historical_launches=2, remaining_real_launches=6,
        source_head=head.stdout.decode().strip(), source_hashes=hashes,
        demo_export='poc-exports/cap8-serial-public-toy-v2/latest.json' if args.demo_export else None)
    r.durable_bytes(args.out, r.json_bytes(evidence), replace=True)
    print(r.json_bytes({k: evidence[k] for k in ('status', 'tests_run', 'errors', 'failures',
                      'skipped', 'optimization', 'powershell_parser_errors', 'real_codex_launches')}).decode())
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
