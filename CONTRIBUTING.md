# Contributing

Duckoder is the subject of an undergraduate thesis, and until it is defended the scope is closed:
the platform generates code for teaching boards from a hardware profile, and nothing more. Bug
reports and board profiles are welcome at any time; a pull request that widens the scope may have
to wait, so open an issue before writing one.

## Getting set up

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Answering with the Claude API needs `APP_ANTHROPIC_API_KEY`; answering with a local model needs
Ollama and `APP_LLM_PROVIDER=ollama`. The README's "Language model" section covers both. The tests
need neither: they replace the provider with a fake model, so they run without a model, a network
or a key.

## Before every commit

```bash
ruff check .
ruff format --check .
pytest
```

The CI workflow runs the same three on Python 3.11 and 3.12 for every push and every pull request.
A red check blocks the merge, so running them locally saves a round trip.

## Conventions this repository follows

- **Commits** use [Conventional Commits](https://www.conventionalcommits.org) with a scope, in
  English, in the imperative: `feat(boards): add the Arduino Nano profile`. One concern per commit.
- **Code is English** — identifiers, docstrings and comments. **What the student reads is Brazilian
  Portuguese**, and lives in `static/js/ui-text.js`, not scattered through the code.
- **One responsibility per class**, and the smallest change that solves the problem. A refactor
  that comes along for the ride makes a pull request harder to review.
- **Comments explain why**, not what the line already says.

## Where things live

| Path | What belongs there |
| --- | --- |
| `app/clients/` | One module per language model provider, plus the registry that picks one |
| `app/services/` | The use cases: prompts, conversations, pin detection, the request cap |
| `app/routers/` | HTTP routes only; they delegate to a service |
| `app/schemas/` | The shapes that cross the API, validated by Pydantic |
| `data/boards/` | One JSON profile per board |
| `tests/` | `unit/` mirrors a module, `api/` goes through the routes |

## Adding a board

Drop a `data/boards/<id>.json` file following the same fields as the profiles already there; the
README's "Adding a board" section documents each one. The profile is validated at startup, so a
malformed file stops the server with the reason. Test the board by asking for a few activities
before opening the pull request, and say in it which ones you tried.

## Adding a language model provider

Write a client beside `app/clients/ollama_client.py` that satisfies the `LlmClient` protocol, then
register it in `BUILTIN_PROVIDERS` in `app/clients/llm_provider.py` and add its settings section to
`app/config.py`. Nothing else in the application needs to know it exists.

## Changing the prompt

Bump `PROMPT_VERSION` in `app/services/prompt_builder.py` whenever `app/prompts/system_prompt.txt`
or the way a profile is serialized changes. Every saved reply records that version, which is what
makes an answer traceable to the prompt that produced it.

## Pull requests

Branch off `master`, keep the branch focused, and open the pull request once the checks are green.
Say what changed and how you tried it. Never commit `.env`, an API key, or anything under
`data/conversations/`.

By contributing you agree that your contribution is licensed under the
[GNU AGPL v3.0 or later](LICENSE), the same license as the rest of the project.
