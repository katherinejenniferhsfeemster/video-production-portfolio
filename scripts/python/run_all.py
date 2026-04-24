"""
End-to-end build: synth clips -> curate -> NLE projects -> caption -> demo
-> posters. Idempotent; safe to re-run.

    python3 scripts/python/run_all.py
"""
import importlib.util
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))


def run(name: str) -> None:
    print(f"\n=== {name} ===")
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod                       # required for @dataclass
    spec.loader.exec_module(mod)
    if hasattr(mod, "main"):
        try:
            mod.main()
        except TypeError:
            mod.main([])


def main() -> None:
    os.chdir(ROOT)
    run("make_synthetic_clips")
    run("curate_dataset")
    run("build_shotcut_mlt")
    run("build_openshot_osp")
    run("export_lightworks_edl")
    run("auto_caption")
    run("render_demo")
    run("render_posters")


if __name__ == "__main__":
    main()
