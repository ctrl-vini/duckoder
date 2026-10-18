"""Send one request through the platform's prompt and print the parsed reply, pins and timing.

Usage: python -m scripts.ask_model "Pisque o LED embutido a cada segundo" [--board esp32] [--raw]
"""

import argparse
import sys

from app.clients.llm_client import LlmResult
from app.clients.llm_provider import LlmProviderRegistry
from app.config import load_settings
from app.exceptions import BoardNotFoundError, InvalidSettingError, LlmUnavailableError
from app.schemas.pin_usage import PinUsage
from app.services.board_registry import BoardRegistry
from app.services.pin_detector import detect_pin_usage
from app.services.prompt_builder import PROMPT_VERSION, PromptBuilder
from app.services.response_parser import parse_response

DEFAULT_BOARD_ID = "esp32"
NO_CODE_PLACEHOLDER = "(no code block found)"
NONE_PLACEHOLDER = "none"


def main() -> int:
    """Run the command line tool and return its exit code."""
    arguments = _parse_arguments()
    settings = load_settings()
    try:
        profile = BoardRegistry.from_directory(settings.boards_dir).get_board(arguments.board)
        messages = PromptBuilder.from_file().build(profile, [], arguments.request)
        result = LlmProviderRegistry().create(settings).chat(messages)
    except (BoardNotFoundError, InvalidSettingError, LlmUnavailableError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if arguments.raw:
        _print_section("raw reply", result.content)
    parsed = parse_response(result.content)
    _print_section("code", parsed.code or NO_CODE_PLACEHOLDER)
    _print_section("explanation", parsed.explanation)
    _print_section("pins", _format_pin_usage(detect_pin_usage(parsed.code, profile)))
    _print_section("metrics", _format_metrics(result))
    return 0


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("request", help="what the student asks for, as typed in the interface")
    parser.add_argument("--board", default=DEFAULT_BOARD_ID, help="board profile id")
    parser.add_argument("--raw", action="store_true", help="also print the unparsed reply")
    return parser.parse_args()


def _print_section(title: str, body: str) -> None:
    print(f"--- {title}\n{body}\n")


def _format_pin_usage(usage: PinUsage) -> str:
    components = ", ".join(component.name for component in usage.components)
    unlisted = ", ".join(str(gpio) for gpio in usage.unlisted_gpios)
    return (
        f"components={components or NONE_PLACEHOLDER} unlisted_gpios={unlisted or NONE_PLACEHOLDER}"
    )


def _format_metrics(result: LlmResult) -> str:
    return (
        f"model={result.model} prompt={PROMPT_VERSION} elapsed_ms={result.elapsed_ms} "
        f"load_ms={result.load_ms} output_tokens={result.output_tokens}"
    )


if __name__ == "__main__":
    sys.exit(main())
