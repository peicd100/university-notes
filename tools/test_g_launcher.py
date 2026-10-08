"""Regression: python -m unittest tools.test_g_launcher (no real Git/deployment)."""
from pathlib import Path
import os
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest

from tools.publish_built_site import publish

ROOT = Path(__file__).resolve().parents[1]


class BuiltSiteTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("git"), "Git required")
    def test_real_git_excludes_ignored_memory_without_error(self):
        # Literal ignored directory excludes can make git add exit1 even though
        # they are negative pathspecs. Exercise the actual Git parser here.
        line = next(line for line in (ROOT / "g.bat").read_text().splitlines() if line.startswith("call git add "))
        args = shlex.split(line)[3:]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)
            private_dirs = [".peicd100/codex", ".peicd100/codex_compressed", ".codex", "codex"]
            (root / ".gitignore").write_text("".join(f"/{name}/\\n" for name in private_dirs), encoding="utf8")
            for name in private_dirs:
                folder = root / name
                folder.mkdir(parents=True)
                private = folder / "private.txt"
                private.write_text("old", encoding="utf8")
                subprocess.run(["git", "add", "-f", str(private.relative_to(root))], cwd=root, check=True, capture_output=True)
                private.write_text("modified", encoding="utf8")
            (root / "public.txt").write_text("public", encoding="utf8")
            result = subprocess.run(["git", "add", "--dry-run", *args], cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("public.txt", result.stdout)
            self.assertNotIn("private.txt", result.stdout)

    def test_module_entry_preflight_loads_project_hooks_without_publishing(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "index.html").write_text("preflight", encoding="utf8")
            result = subprocess.run([sys.executable, "-m", "tools.publish_built_site", "--site-dir", directory, "--check"],
                                    cwd=ROOT, capture_output=True, text=True, encoding="utf8", errors="replace", timeout=20)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("no Git changes or push", result.stderr)

    def test_missing_build_cannot_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                publish(Path(directory), config_loader=lambda **kw: self.fail("No config loading"),
                        deploy=lambda cfg: self.fail("No deployment"))

    def test_validated_artifact_is_reused_without_build_or_force(self):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            (site / "index.html").write_text("test", encoding="utf8")
            calls = []
            def loader(**kwargs):
                calls.append(kwargs)
                return {"validated": True}
            publish(site, root=site, config_loader=loader, deploy=lambda cfg: calls.append(cfg))
            self.assertEqual(calls, [{"config_file": str(site / "mkdocs.yml"), "site_dir": str(site.resolve())}, {"validated": True}])


@unittest.skipUnless(os.name == "nt", "Native Windows CMD required")
class LauncherTests(unittest.TestCase):
    def run_launcher(self, option="", **overrides):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "入口 測試 with spaces"
            bin_dir = root / "bin"
            bin_dir.mkdir(parents=True)
            shutil.copyfile(ROOT / "g.bat", root / "g.bat")
            scripts = {
                "activate.cmd": '@echo off\necho activate %*>>"%CALL_LOG%"\nif "%FAIL_STEP%"=="activate" exit /b %FAIL_CODE%\nexit /b 0\n',
                "python.cmd": '@echo off\necho python %*>>"%CALL_LOG%"\nif "%~2"=="mkdocs" (\n if "%FAIL_STEP%"=="build" exit /b %FAIL_CODE%\n) else (\n if "%FAIL_STEP%"=="deploy" exit /b %FAIL_CODE%\n)\nexit /b 0\n',
                "git.cmd": '@echo off\necho git %*>>"%CALL_LOG%"\nif "%~1"=="branch" (\n echo %MOCK_BRANCH%\n exit /b 0\n)\nif "%~1"=="diff" (\n if "%~4"=="--" exit /b %PRIVATE_STAGED%\n exit /b %DIFF_EXIT%\n)\nif "%FAIL_STEP%"=="%~1" exit /b %FAIL_CODE%\nexit /b 0\n',
            }
            for name, text in scripts.items():
                (bin_dir / name).write_text(text, encoding="ascii", newline="\r\n")
            log = root / "calls.log"
            env = {**os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                   "CALL_LOG": str(log), "FAIL_STEP": "", "FAIL_CODE": "7", "MOCK_BRANCH": "main",
                   "PRIVATE_STAGED": "0", "DIFF_EXIT": "1", **overrides}
            result = subprocess.run(f'cmd.exe /d /c call "{root / "g.bat"}" {option}',
                                    cwd=root, env=env, capture_output=True, text=True,
                                    encoding="utf8", errors="replace", timeout=20)
            calls = log.read_bytes().decode("utf8", errors="replace") if log.exists() else ""
            return result, calls

    def test_check_only_cannot_publish_or_use_git(self):
        result, calls = self.run_launcher("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("-m mkdocs build", calls)
        self.assertNotIn("git ", calls)
        self.assertNotIn("publish_built_site", calls)
        self.assertIn("g-deploy", calls)

    def test_failure_stops_later_steps_and_preserves_exit_code(self):
        for stage, forbidden in [("activate", "python "), ("build", "git add"), ("add", "git commit"),
                                 ("commit", "publish_built_site"), ("deploy", "git push"), ("push", "completed")]:
            with self.subTest(stage=stage):
                result, calls = self.run_launcher(FAIL_STEP=stage, FAIL_CODE="7")
                self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
                if stage == "push":
                    self.assertNotIn(forbidden, result.stdout)
                else:
                    self.assertNotIn(forbidden, calls)

    def test_success_builds_once_commits_before_deploy_and_pushes_last(self):
        result, calls = self.run_launcher()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls.count("-m mkdocs build"), 1)
        self.assertLess(calls.index("git commit"), calls.index("publish_built_site"))
        self.assertLess(calls.index("publish_built_site"), calls.index("git push"))
        self.assertNotIn("branch -M", calls)
        self.assertIn("(top,glob,exclude)[.]peicd100/codex/**", calls)

    def test_clean_sources_skip_commit_not_deployment(self):
        result, calls = self.run_launcher(DIFF_EXIT="0")
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("git commit", calls)
        self.assertIn("publish_built_site", calls)

    def test_unexpected_diff_error_is_not_treated_as_changes(self):
        result, calls = self.run_launcher(DIFF_EXIT="2")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("git commit", calls)
        self.assertNotIn("publish_built_site", calls)

    def test_staged_private_memory_aborts_before_staging_or_publishing(self):
        result, calls = self.run_launcher(PRIVATE_STAGED="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("git add", calls)
        self.assertNotIn("publish_built_site", calls)

    def test_other_branch_is_never_renamed_or_published(self):
        result, calls = self.run_launcher(MOCK_BRANCH="feature")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("-m mkdocs build", calls)
        self.assertNotIn("git add", calls)
        self.assertNotIn("branch -M", calls)

    def test_unknown_options_do_not_start_work(self):
        result, calls = self.run_launcher("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(calls, "")


if __name__ == "__main__":
    unittest.main()
