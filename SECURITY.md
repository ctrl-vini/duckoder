# Security policy

## Supported versions

Only the latest release receives fixes. Earlier tags stay in the repository for reference and to
reproduce the measurements reported in the thesis this platform belongs to.

| Version | Supported |
| --- | --- |
| 1.4.x | Yes |
| < 1.4 | No |

## Reporting a vulnerability

Report it privately, not in a public issue:
[open a private report](https://github.com/ctrl-vini/duckoder/security/advisories/new) in the
repository's Security tab. GitHub keeps the report visible only to you and to the maintainer until
a fix is published.

Useful in a report: which version answered, whether the provider was the Claude API or Ollama,
what the request looked like, and what the server logged. **Never paste a real API key**, in a log
or anywhere else; the key's shape is enough to describe the problem.

Expect a first answer within a few days. This is an academic project with a single maintainer, so
there is no service level agreement: a confirmed problem is fixed in the next release, and the
advisory is published once the fix is out.

## What is in scope

The web server and its routes, the handling of the Claude API key, the request cap, the deploy
scripts under `deploy/`, and the workflows under `.github/workflows/`.

The language model writing wrong, unsafe or non-compiling code is **not** a vulnerability. It is a
known limitation of the platform: the generated code is a draft for a student to read and test,
never something to flash into a board unread. The same goes for a prompt that steers the model
into writing something unhelpful.

## If you run your own instance

The platform has no authentication, so anything you publish on the internet is open to whoever
finds it:

- Keep `APP_ANTHROPIC_API_KEY` out of the repository. It belongs in `.env`, readable only by its
  owner (`chmod 600`), or in a secrets manager, as the README's AWS section describes.
- Keep `APP_MAX_REQUESTS_PER_HOUR` at a value you are willing to pay for, and set a spend limit on
  the account behind the API. The cap limits how many replies are generated, not how long each
  conversation grows.
- Conversations are stored unencrypted as JSON under `APP_CONVERSATIONS_DIR`. Treat whatever
  students typed there as data you are responsible for.
