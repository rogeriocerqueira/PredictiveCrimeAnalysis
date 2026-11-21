"""CLI: `python -m crime_analysis [process|models]`."""

import argparse
import sys

from . import config
from .data import load_processed, run_pipeline
from .model import compare_models


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="crime_analysis", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("process", help="Valida o CSV bruto e gera o CSV processado.")
    sub.add_parser("models", help="Compara modelos por validação cruzada leave-one-out.")
    args = parser.parse_args(argv)

    if args.cmd == "process":
        try:
            df, rep = run_pipeline()
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        print(f"OK: {len(df)} linhas -> {config.PROCESSED_FILE.relative_to(config.PROJECT_ROOT)}")
        print(f"{len(rep.avisos)} aviso(s); veja {config.VALIDATION_REPORT.relative_to(config.PROJECT_ROOT)}")
    elif args.cmd == "models":
        print(compare_models(load_processed()).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
