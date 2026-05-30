import argparse
import sys

from .ledgerdiff import diff_ledger_text


def diff_ledger_io(left_path: str, right_path: str) -> None:
    try:
        with open(left_path, "r", encoding="utf-8") as f:
            left_content = f.read()
    except Exception as e:
        print(f"Could not read {left_path}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(right_path, "r", encoding="utf-8") as f:
            right_content = f.read()
    except Exception as e:
        print(f"Could not read {right_path}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        diff_output = diff_ledger_text(left_content, right_content)
        if diff_output:
            print(diff_output)
    except Exception as e:
        print(f"Could not diff files: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ledgerdiff",
        description="Runs a smart chronological diff on two Ledger files.",
    )
    parser.add_argument("left_file", metavar="LEFT_FILE")
    parser.add_argument("right_file", metavar="RIGHT_FILE")

    args = parser.parse_args()
    diff_ledger_io(args.left_file, args.right_file)


if __name__ == "__main__":
    main()
