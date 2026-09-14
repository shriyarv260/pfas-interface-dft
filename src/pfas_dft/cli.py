import argparse
from pathlib import Path

from .common import load_json, save_json


def main(argv=None):
    parser = argparse.ArgumentParser(description="PFAS interface workflow; no bundled DFT results")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("demo", help="Run a synthetic analytical NEB integration example")
    p.add_argument("--output", required=True)
    p = sub.add_parser("build", help="Prepare a prototype FCC(111) interface")
    p.add_argument("--molecule", required=True)
    p.add_argument("--metal", choices=["Cu", "Pd"], default="Cu")
    p.add_argument("--size", type=int, nargs=3, default=[6, 6, 4])
    p.add_argument("--vacuum", type=float, default=18.0)
    p.add_argument("--height", type=float, default=2.5)
    p.add_argument("--vacancy", type=int)
    p.add_argument("--output", required=True)
    p = sub.add_parser("endpoint", help="Translate a fragment without deleting atoms")
    p.add_argument("--initial", required=True)
    p.add_argument("--indices", type=int, nargs="+", required=True)
    p.add_argument("--shift", type=float, nargs=3, required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("prepare-neb")
    p.add_argument("--initial", required=True)
    p.add_argument("--final", required=True)
    p.add_argument("--images", type=int, default=7)
    p.add_argument("--output", required=True)
    for command in ["write-qe", "relax", "neb", "vibrations"]:
        p = sub.add_parser(command)
        p.add_argument("--input", required=True)
        p.add_argument("--config", required=True)
        p.add_argument("--output", required=True)
        if command == "vibrations":
            p.add_argument("--indices", type=int, nargs="+", required=True)
    p = sub.add_parser("analyze")
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("benchmark")
    p.add_argument("--references", required=True)
    p.add_argument("--predictions", required=True)
    p.add_argument("--policy", default="configs/benchmark_policy.json")
    p.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            from .toy import run_demo

            run_demo(args.output)
        elif args.command == "build":
            from .structures import build_interface

            build_interface(
                args.molecule,
                args.output,
                args.metal,
                args.size,
                args.vacuum,
                args.height,
                args.vacancy,
            )
        elif args.command == "endpoint":
            from .structures import displaced_endpoint

            if Path(args.output).exists():
                raise FileExistsError("Output already exists")
            displaced_endpoint(args.initial, args.output, args.indices, args.shift)
        elif args.command == "prepare-neb":
            from .structures import prepare_neb

            prepare_neb(args.initial, args.final, args.output, args.images)
        elif args.command in {"write-qe", "relax", "neb", "vibrations"}:
            from .dft import relax, run_neb, vibrate, write_qe_template

            fn = {
                "write-qe": write_qe_template,
                "relax": relax,
                "neb": run_neb,
                "vibrations": vibrate,
            }[args.command]
            extra = {"indices": args.indices} if args.command == "vibrations" else {}
            fn(args.input, load_json(args.config), args.output, **extra)
        elif args.command == "analyze":
            from .analysis import analyze_csv

            analyze_csv(args.input, args.output)
        elif args.command == "benchmark":
            from .benchmark import evaluate

            report = evaluate(
                load_json(args.references), load_json(args.predictions), load_json(args.policy)
            )
            save_json(args.output, report)
            print(report["status"])
            return 0 if report["status"] == "target_met" else 2
    except (ValueError, FileNotFoundError, FileExistsError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
