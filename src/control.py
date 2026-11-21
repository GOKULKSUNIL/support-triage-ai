"""Kill switch: stop automatic answering immediately, without a deployment.

    python -m src.control pause  --by "Marcus Adeyemi" --reason "DOC-BILL-001 found to be wrong"
    python -m src.control resume --by "Marcus Adeyemi" --reason "article corrected"
    python -m src.control status

The switch lives in the decision-log database (DATABASE_URL), the store the
pipeline already writes to. The pipeline reads it for every ticket, after
routing (so no model call is made) and again just before a reply is released,
so a ticket that was being drafted when the switch was pulled is escalated
too. While paused, every ticket goes to a person with the pause in its
reason. Every pause and resume is kept with who, when and why.
"""
import argparse

from src.logging_store import DecisionLog


def _describe(state: dict | None) -> str:
    if not state:
        return "Automatic answering: ON (the switch has never been used)"
    when = f"since {state['changed_at']} by {state['changed_by']}: {state['reason']}"
    return f"Automatic answering: {'PAUSED' if state['paused'] else 'ON'} ({when})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m src.control",
                                     description="Pause or resume automatic answering.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("pause", "resume"):
        command = commands.add_parser(name)
        command.add_argument("--by", required=True, help="who is pulling the switch")
        command.add_argument("--reason", required=True, help="why, in a sentence")
    commands.add_parser("status")
    args = parser.parse_args(argv)

    log = DecisionLog()
    if args.command != "status":
        log.set_paused(args.command == "pause", args.by, args.reason)
    print(_describe(log.control_state()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
