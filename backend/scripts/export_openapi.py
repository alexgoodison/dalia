import argparse
import json
from pathlib import Path

from backend.app.main import app


def dump_openapi_schema(output_path: Path) -> None:
    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export the FastAPI OpenAPI schema to a JSON file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve(
        ).parents[2] / "frontend" / "openapi.json",
        help="Path to write the OpenAPI schema JSON file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dump_openapi_schema(args.output)


if __name__ == "__main__":
    main()
