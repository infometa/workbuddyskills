import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="Validate and format tophpc --instance-specs JSON")
    parser.add_argument("spec_json", help="The raw JSON string representing the instance specs")
    args = parser.parse_args()

    try:
        specs = json.loads(args.spec_json)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format: {e}", file=sys.stderr)
        sys.exit(1)

    # Basic structural validation
    if not isinstance(specs, dict):
        print("Error: Root element must be a JSON object", file=sys.stderr)
        sys.exit(1)

    required_fields = ["Queue", "InstanceType"]
    missing = [f for f in required_fields if f not in specs]
    if missing:
        print(f"Error: Missing required fields: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    # Output minimized JSON safe for bash passing
    print(json.dumps(specs, separators=(',', ':')))

if __name__ == "__main__":
    main()
