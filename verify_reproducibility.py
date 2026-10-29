"""Run tests from a read-only temporary source copy; never chmod original inputs."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def hashes(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


def main():
    root = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)/'readonly'
        tree.mkdir()
        for name in ('memory_dsa', 'tests', 'inputs'):
            shutil.copytree(root/name, tree/name, ignore=shutil.ignore_patterns('__pycache__'))
        before = hashes(tree)
        paths = sorted(tree.rglob('*'), key=lambda p: len(p.parts), reverse=True)
        try:
            for p in paths:
                p.chmod(0o555 if p.is_dir() else 0o444)
            tree.chmod(0o555)
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(tree))
            result = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=tree, env=env, capture_output=True, text=True)
            unchanged = hashes(tree) == before
            evidence = dict(command='python3.13 -B -m unittest discover -s tests -v (read-only temporary source copy)', exit_code=result.returncode, source_unchanged=unchanged, output=result.stdout+result.stderr)
            print(json.dumps(evidence, indent=2))
            return 0 if result.returncode == 0 and unchanged else 1
        finally:
            tree.chmod(0o755)
            for p in paths:
                p.chmod(0o755 if p.is_dir() else 0o644)


if __name__ == '__main__':
    sys.exit(main())
