# Duckoder

![Duckoder](docs/banner.svg)

Web platform that generates code for teaching boards, such as the ESP32 and the Arduino Uno, Mega
and Nano, using a language model. The student picks a board, explains to a rubber duck what the
board should do, and gets code ready to paste into the IDE, which can be refined in the same
conversation.

The code comes either from the [Claude API](https://claude.com), which is the default and needs
no GPU, or from a model running on the machine itself through [Ollama](https://ollama.com), chosen
in one setting. With the local model it works entirely on the local network, with no internet
access and no paid service while it is in use.

Duckoder is the subject of my undergraduate thesis (TCC); the thesis itself is in
[ctrl-vini/rdc-tcc](https://github.com/ctrl-vini/rdc-tcc).

## Requirements

- Python 3.11 or newer
- A Claude API key, or Ollama to generate with a model on this machine

Or only Docker, as in [Running with Docker](#running-with-docker).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Language model

The platform generates code with one of two providers, picked by `APP_LLM_PROVIDER`:

| Provider | When it is the right one |
| --- | --- |
| `anthropic` (default) | The Claude API: fast answers from a machine with no GPU, paid per token |
| `ollama` | A model running on this machine: nothing to pay per request and no key, as long as the machine answers fast enough |

`app/clients/llm_provider.py` holds the registry that maps each name to its client, and it is the
only module that knows more than one provider exists. The rest of the platform asks the
`LlmClient` of `app/clients/llm_client.py` for a reply and never learns where it came from, which
is also how the tests answer without a model. Supporting a third provider means writing its
client beside `ollama_client.py` and adding a line to `BUILTIN_PROVIDERS`.

### Answering with the Claude API

This is what the platform does unless told otherwise. Create a key in the
[Claude Console](https://console.anthropic.com), then write it into `.env`, which is never
committed:

```bash
cp .env.example .env
chmod 600 .env
```

```
APP_LLM_PROVIDER=anthropic
APP_ANTHROPIC_API_KEY=sk-ant-...
```

Compose reads `.env` by itself. Outside Docker the server reads the environment, not that file,
so load it first: `set -a; . ./.env; set +a`.

The key is held in a `SecretStr`, so printing the settings, logging them or showing them in a
traceback writes `SecretStr('**********')`; and a provider without its key stops the server at
startup instead of answering the first student with an error. Two settings bound what the API
can cost: `APP_ANTHROPIC_MAX_TOKENS`, the longest reply it may write, and
`APP_MAX_REQUESTS_PER_HOUR`, how many replies the whole server generates in an hour, which is
what keeps a public address from spending the account's credit. That hour's requests are counted
in memory, so restarting the server starts the count again.

### Answering with a model on this machine

Set `APP_LLM_PROVIDER=ollama`, then pull a model and check that it answers:

```bash
ollama pull qwen2.5-coder:7b
ollama run qwen2.5-coder:7b --verbose "Write an Arduino sketch for the ESP32 that blinks the built-in LED on GPIO 2."
```

`--verbose` prints the load time and the generation speed after the answer.

To try a request through the platform's own prompt, board profile and provider:

```bash
python -m scripts.ask_model "Pisque o LED embutido a cada segundo" --board esp32
```

It prints the extracted code, the explanation, the board components the code uses (with any
GPIO it uses that has no component) and the timing; add `--raw` to also see the unparsed reply.
The system prompt lives in `app/prompts/system_prompt.txt`; bump `PROMPT_VERSION` in
`app/services/prompt_builder.py` whenever it changes, so each saved reply records the prompt
that produced it.

## Running

```bash
python server.py
```

The log shows the address to open from any device on the local network: that page is the
interface students use. The interactive API documentation is available at `/docs`. The
interface files are sent with `Cache-Control: no-cache`, so browsers check for a newer version on
every load and an updated interface reaches students with a plain reload.

## Running with Docker

```bash
docker compose up -d
```

`compose.yaml` starts `app`, the web server built from the `Dockerfile`, which answers with the
Claude API, so `.env` needs `APP_ANTHROPIC_API_KEY`.

Adding `APP_LLM_PROVIDER=ollama` and `COMPOSE_PROFILES=local-model` to `.env` runs the model in
Docker too, in two more services: `ollama`, the model server, and `model`, which downloads the
model into the `models` volume on the first start, about 4.7 GB, and then exits. Follow the
download with
`docker compose logs -f model`. Later starts find the model in the volume and need no internet.

The page is then on port 8000 of the machine running Docker, such as `http://192.168.0.10:8000`;
the address in the server log is the container's own. Conversations are kept in the
`conversations` volume, so they survive `docker compose down` and new images;
`docker compose down -v` deletes them, along with the model.

`APP_OLLAMA_MODEL` picks another model for both the server and the download, such as
`APP_OLLAMA_MODEL=llama3.1:8b docker compose up -d`. The settings the `app` service passes on are
read from `.env` as well; any other one in [Configuration](#configuration) goes in the
`environment` of that service.

Without a GPU the model runs on the CPU, which is much slower:

- The Claude API needs no GPU at all, and is the default.
- On Linux with an NVIDIA GPU and the NVIDIA Container Toolkit, add the GPU file:
  `COMPOSE_PROFILES=local-model docker compose -f compose.yaml -f compose.gpu.yaml up -d`.
- On a Mac, Docker Desktop does not give containers the Apple GPU, so use Ollama installed on the
  Mac and run only the web server in Docker: with `APP_LLM_PROVIDER=ollama` and
  `APP_OLLAMA_URL=http://host.docker.internal:11434` in `.env`, `docker compose up -d`. The same
  works on Linux with Ollama listening beyond loopback (`OLLAMA_HOST=0.0.0.0`).

## The interface

The page looks like a terminal, with a rubber duck in the corner, as in rubber duck debugging:

- Requests are typed at a shell prompt: Enter sends, Shift + Enter adds a line, and the up and
  down arrows bring back what was typed in this conversation, as in a shell; clearing the
  conversation empties that history. While the model works, the waiting line moves on every few
  seconds through the steps of writing a sketch.
- Each reply prints the code as "versão N" with a copy action and the model's explanation. A
  refinement that comes back with the same code as the previous version is flagged.
- `[ ver ligações ]`, on each version, opens the board with only what that code uses: its pins
  highlighted, a drawing of each of its components with the board pin every leg goes to, a notice
  in orange when it moved a component to another pin, and a warning in red for any pin it uses
  that has no component wired to it, usually a pin the model made up.
- The duck, drawn in braille characters, opens and closes its beak while its message is typed
  out and while the explanation of a new reply is typed into the conversation, blinks from time
  to time, and its eye shows whether it is listening, thinking, happy or confused. Its messages
  vary from one request to the next. Animations stop when the system asks for reduced motion.
- The board is picked in the status bar, from a list drawn like a terminal menu that shows each
  board's microcontroller: click it, or focus it and use the arrows, Enter and Esc, or type the
  start of a board's name.
- Picking a board and sending a request starts a conversation; its id goes into the page address
  (`/?conversation=<id>`), so reloading or sharing the link reopens it.

A few words typed at the prompt are commands that the page answers by itself, without the model.
`help` lists them:

| Command | Also | What it does | Shortcut |
| --- | --- | --- | --- |
| `help` | `ajuda` | Prints the commands and their shortcuts | — |
| `pinout` | — | Opens the board in a pane beside the conversation, like a split terminal. Before any code nothing is wired yet, so it marks only the pins nearly every circuit uses, such as GND, 3V3 and VIN, and says what each is for; afterwards, it shows what the latest version uses, following each new version, and `[ placa completa ]` switches back to the bare board. The duck shrinks to one line to make room; on small screens the pane takes the whole screen until `[ fechar ]` | Ctrl + P |
| `clear` | `cls`, `reset`, `clear-host`, `clc` | Asks for confirmation (Enter clears, Esc cancels) and empties the screen; the next request starts a new conversation, so the model no longer sees the earlier messages | Ctrl + L |
| `about` | `sobre` | Shows what Duckoder is, the running version and the credits | Ctrl + S |
| `quack` | — | The duck quacks, with a sound made by the Web Audio API | — |

The status bar buttons `[ ver placa ]`, `[ limpar conversa ]` and `[ sobre ]` do the same, and
hovering over one shows its shortcut; on a Mac the shortcuts use Cmd instead of Ctrl. On this
page they replace the browser's own (address bar, printing and saving), which stay available
from the browser's menu.

It is plain HTML, CSS and JavaScript modules in `static/`, with no build step and nothing loaded
from the internet. The JetBrains Mono NL font is bundled in `static/fonts/` under the SIL Open
Font License: the build without ligatures, so operators such as `<=` show the exact characters to
type, and with its box drawing characters, so the drawings line up on every system.

## Configuration

All settings are environment variables with defaults, so nothing needs to be set to get started.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_HOST` | `0.0.0.0` | Network interface the server listens on |
| `APP_PORT` | `8000` | Server port |
| `APP_LLM_PROVIDER` | `anthropic` | Which service generates the code: `anthropic`, the Claude API, or `ollama`, a model on this machine |
| `APP_MAX_REQUESTS_PER_HOUR` | `60` | Replies the server generates in an hour, counted across every visitor; `0` turns the cap off |
| `APP_ANTHROPIC_API_KEY` | — | Claude API key; without it the `anthropic` provider does not start |
| `APP_ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Model of the Claude API |
| `APP_ANTHROPIC_MAX_TOKENS` | `4096` | Longest reply the API may write, which also bounds what one reply costs |
| `APP_ANTHROPIC_TIMEOUT_S` | `120` | How long to wait for the API before giving the student an error |
| `APP_OLLAMA_URL` | `http://localhost:11434` | Address of the Ollama service |
| `APP_OLLAMA_MODEL` | `qwen2.5-coder:7b` | Model Ollama generates with |
| `APP_LLM_TEMPERATURE` | `0.7` | Sampling temperature for Ollama; higher values vary more between runs. The Claude API takes none |
| `APP_LLM_CONTEXT_SIZE` | `8192` | Context window in tokens; Ollama silently drops what exceeds it |
| `APP_LLM_KEEP_ALIVE` | `30m` | How long Ollama keeps the model loaded after the last request |
| `APP_BOARDS_DIR` | `data/boards` | Folder with the board profiles |
| `APP_DEFAULT_BOARD` | `esp32` | Board listed first, so the page opens with it selected |
| `APP_CONVERSATIONS_DIR` | `data/conversations` | Folder where each conversation is saved as JSON |

Example: `APP_OLLAMA_MODEL=llama3.1:8b python server.py`. `.env.example` lists the ones a
machine usually sets; Compose reads `.env`, and outside Docker `set -a; . ./.env; set +a` loads
it into the shell.

## API

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| GET | `/boards` | — | `200` boards with `id`, `name`, `microcontroller` |
| GET | `/boards/{id}` | — | `200` the full board profile, with components, wiring and pinout |
| POST | `/conversations` | `{"board_id"}` | `201` the new, empty conversation |
| POST | `/conversations/{id}/messages` | `{"content"}` | `201` the model's reply, with `code`, `explanation` and `metrics` |
| GET | `/conversations/{id}` | — | `200` the conversation with every message |
| GET | `/conversations/{id}/messages/{message_id}/pin-usage` | — | `200` the board `components` the message's code uses, wired as it needs them, the `moved_pins` and the `unlisted_gpios` it uses with no component |
| GET | `/version` | — | `200` the application's `name` and `version` |

Errors use `{"detail": "..."}`: `404` for an unknown board, conversation or message, `422` for an
invalid body, `502` when the provider cannot answer and `429` once the hour's cap is reached. If
the model fails, nothing is saved, so the student can simply send the message again. Try every
route from `/docs`.

The pins come from reading the generated code, in `app/services/pin_detector.py`: the pin
arguments of calls such as `pinMode`, `digitalWrite`, `analogRead`, `ledcAttach`, `tone` and
`Wire.begin`, and of library objects such as `DHT`, with named constants, `#define`s and arrays
resolved. The prompt asks the model to declare each pin as a named constant, which keeps this
reliable; the board's own pin names and the default I2C pins come from its profile. Pins
computed while the code runs are not found. The usage is computed on every request, so it always
matches the current profile.

A component can move: asked to use another pin because one is broken, the model keeps the
constant and changes its number. The earlier versions of the conversation tell which component a
constant stands for, so the board view shows that component on its new pin, with its wiring text
updated and a notice to move the wire; the profile's notes list the free pins the model should
pick.

## Adding a board

Each board is described by one JSON file in `data/boards/`. The project ships the ESP32 DevKit V1,
the Arduino UNO R3, the Arduino UNO R4 (one profile for the Minima and the WiFi), the Arduino Mega
2560 and the classic Arduino Nano, all with the same kit of components. To add a board, copy the
profile closest to it, give it a new `id` and restart the server. Invalid files stop the server at
startup with a message naming the file.

| Field | Content |
| --- | --- |
| `id` | Lowercase letters, digits and hyphens; used in the API paths |
| `name`, `microcontroller` | Shown to the student and sent to the model |
| `language`, `framework` | What the generated code must target, such as C++ on Arduino |
| `ide_board` | Optional board to pick in the Arduino IDE, shown in the board view; the wrong one can leave names such as `LED_BUILTIN` undefined |
| `components` | What is wired to the board: `name`, `type`, `pins`, an optional `wiring` text and an optional `kind` for its drawing |
| `notes` | Usage restrictions and libraries the model must respect |
| `pinout` | Optional header layout for the board view: `caption`, `left` and `right` pin lists, and a `label` of up to 8 characters drawn on the board |
| `pin_naming` | How the interface names a pin: `gpio` for "GPIO 13", the default, or `label` for the header label, such as "D13" on an Arduino |
| `supply_pins` | Optional header labels the component drawings take power from: `logic`, `five_volt` and `ground`, such as `3V3`, `VIN` and `GND` on the ESP32 |
| `pin_names` | Optional names the board's Arduino core gives to some pins, such as `LED_BUILTIN`, `SDA` and `SCL`, used to find the pins in generated code |

Each pin of a component has a `gpio` number and an optional `role`, such as `SDA`; on an Arduino,
the number is the one the code uses, so A0 is 14 on the Uno and 54 on the Mega. Each header pin has
a `label` and, when it is a GPIO, its `gpio` number; the pins nearly every circuit uses, such as GND
and 3V3, also get a short `note` drawn beside them and a `description` of what they are for, which
the board view shows before any code. A profile whose components use a GPIO missing from its pinout
is rejected, and so is one whose `supply_pins` are missing from it. The `kind` is one of `led`,
`button`, `buzzer`, `dht22`, `potentiometer`, `oled` and `relay`, each with its own drawing in
`static/js/components/componentDrawing.js`, whose power legs go to the profile's `supply_pins`; a
component without a kind, such as a built-in LED, shows only its wiring text. For example:

```json
{
  "name": "Display OLED",
  "type": "SSD1306 128x64, I2C, endereço 0x3C",
  "kind": "oled",
  "pins": [{ "gpio": 21, "role": "SDA" }, { "gpio": 22, "role": "SCL" }],
  "wiring": "VCC no 3V3, GND no GND, SDA no GPIO 21 e SCL no GPIO 22."
}
```

The profile is sent to the model as context without `pinout`, `ide_board`, `pin_names`,
`pin_naming`, `supply_pins`, the kinds and the `wiring` texts: those are for the student and for
reading the code, and leaving them out keeps the prompt shorter. The `notes` do go to the model:
they are where the profile tells it how to use the board's libraries and core, such as which calls
exist for PWM. The texts the student reads are in Brazilian Portuguese.

## Development checks

Run before every commit:

```bash
ruff check .
ruff format --check .
pytest
```

The tests replace the provider with a fake model, so they need no model, no network and no
API key.

## Continuous integration and releases

- `.github/workflows/ci.yml` runs the development checks on Python 3.11 and 3.12 for every pull
  request and every push, whatever the branch.
- `.github/workflows/release.yml` runs when a version tag is pushed. It runs the same checks,
  confirms that the tag matches `APP_VERSION` in `app/main.py`, publishes a GitHub release with
  generated notes and a `duckoder-<tag>.zip` archive of the source, and then deploys the version
  to AWS once that is set up.

To publish a version, update `APP_VERSION`, commit, then tag and push the branch and the tag
separately, so the tag push starts the release:

```bash
git tag v1.0.0
git push origin master
git push origin v1.0.0
```

## Deploying to AWS

Once set up, each release also runs `.github/workflows/deploy.yml`. It builds the image for Intel
and Arm, pushes it to Amazon ECR and has Systems Manager update an EC2 instance, which runs
`compose.yaml` with that image. GitHub signs in to AWS with OpenID Connect, so no access key is
stored, and the instance needs no SSH. The deploy is skipped until the `AWS_REGION` variable
exists; to deploy a version again, run the workflow from the Actions tab with its tag picked.

One-time setup, all in the region the instance runs in:

1. ECR: a private repository named `duckoder`.
2. IAM: an OpenID Connect identity provider for `https://token.actions.githubusercontent.com`,
   with the audience `sts.amazonaws.com`.
3. IAM: a role for EC2 with the managed policies `AmazonSSMManagedInstanceCore` and
   `AmazonEC2ContainerRegistryReadOnly`.
4. EC2: an Ubuntu Server 24.04 LTS instance with that role, a 30 GB disk, a security group
   open only on TCP port 8000, and `deploy/ec2-user-data.sh` as its user data. Answering with
   the Claude API asks nothing of the instance, so a `t4g.small` is enough; running the model
   there needs at least 16 GB of memory, such as a `t4g.xlarge`.
5. IAM: a role for GitHub Actions with the trust policy in `deploy/github-trust-policy.json` and
   the permissions in `deploy/github-permissions-policy.json`, with `ACCOUNT_ID`, `REGION` and
   `INSTANCE_ID` replaced.
6. GitHub, in Settings > Secrets and variables > Actions: the secret `AWS_ROLE_ARN`, with the ARN
   of that role, and the variables `AWS_REGION` and `EC2_INSTANCE_ID`.
7. Systems Manager Parameter Store: `/duckoder/anthropic-api-key`, a `SecureString` holding the
   key of the Claude API, as below.

The server keeps its files in `/opt/duckoder`, where the settings go in `.env`.
`deploy/update-server.sh`, which the workflow sends to it, reads `compose.yaml` from this public
repository at the version's tag and leaves the lines of `.env` it does not write itself, so what
is set by hand there survives the deploys.

### The key of the Claude API

The key is kept in Parameter Store as a `SecureString`, and the instance reads it from there at
every deploy. It is in no GitHub secret, in no workflow and in no command sent to the instance:
Systems Manager keeps the text of those commands for 30 days, where a key would stay readable.
Store it once, from your own machine:

```bash
aws ssm put-parameter --name /duckoder/anthropic-api-key --type SecureString \
  --value sk-ant-... --region <region>
```

Rotating it is the same command with `--overwrite`, and the next deploy picks the new value up;
every read is recorded in CloudTrail. This needs no extra permission: the instance role's
`AmazonSSMManagedInstanceCore` already allows `ssm:GetParameter`, and the default `alias/aws/ssm`
key lets every principal of the account decrypt — which is also its limit, as anyone in the
account who can read parameters can read this key. A customer managed key narrows that, in
exchange for granting the instance role `kms:Decrypt` on it.

With no such parameter the deploy keeps the `APP_ANTHROPIC_API_KEY` already in `.env`, so a
server that answers with a local model needs none of this: give it `APP_LLM_PROVIDER=ollama` and
`COMPOSE_PROFILES=local-model` in `/opt/duckoder/.env` instead. The first deploy after moving to
the API takes the model's containers off the instance, as they stopped being services of the
stack; `sudo docker volume rm duckoder_models` also frees the 4.7 GB the model occupied.

The AWS CLI is what reads the parameter, and Ubuntu 24.04 has no package for it, so the deploy
installs it as a snap the first time it is missing.

To serve the site at a domain over HTTPS, without the port, point the domain's A records for
`www` and for the bare domain at an Elastic IP associated with the instance, open TCP ports 80 and
443 in its security group, and add the variable `DUCKODER_DOMAIN`, such as `duckoder.com.br`. The
next deploy adds `compose.proxy.yaml`: Caddy gets the Let's Encrypt certificate, serves
`https://www.<domain>`, sends the bare domain there, and port 8000 is no longer published, so it
can be closed. Removing the variable turns this off at the next deploy.

## Manual end-to-end check

With the server running, from another device on the same network:

1. Open the address from the server log; the board list loads.
2. Run `help`, then `pinout`: the commands print, and the board opens in a pane beside the
   conversation.
3. Send "Pisque o LED embutido a cada segundo"; the code appears as "versão 1", and the open
   pane switches to it, with only the built-in LED highlighted.
4. Ask for a change, such as "Tire os comentários do código"; "versão 2" applies it.
5. Click `[ ver ligações ]` on "versão 1"; the pane shows that version again.
6. Reload the page; the conversation comes back from the address.
7. Copy the code; it pastes intact into the Arduino IDE.
8. Type `clear` and confirm; the screen empties and the next reply starts again at "versão 1".
9. Make the provider fail, by stopping Ollama or pointing the key at nothing, and send a
   request; a readable error appears and the duck looks confused.

## Contributing

[CONTRIBUTING.md](CONTRIBUTING.md) has the setup, the checks to run before a commit and the
conventions this repository follows; [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) applies to everyone
taking part. A vulnerability goes in a private report, as [SECURITY.md](SECURITY.md) describes,
never in a public issue. Duckoder is an undergraduate thesis project, so its scope is closed until
the defense: open an issue before writing a pull request that widens it.

## License

Copyright © 2026 José Vinícius Alves de Oliveira.

Duckoder is free software under the
[GNU Affero General Public License v3.0 or later](LICENSE). You may use, study, change and
redistribute it, as long as what you pass on stays under the same license and carries its notices.

Because this is a web application, the AGPL asks for one thing more than the GPL: whoever
**publishes a modified version for others to use over a network** has to offer those users its
source code. The interface's "sobre" dialog links to this repository for that reason; a modified
instance should point it at the source of that modification instead.

The JetBrains Mono font bundled in `static/fonts/` keeps its own license, the SIL Open Font
License 1.1, in `static/fonts/jetbrains-mono-OFL.txt`. The dependencies in `requirements.txt` are
MIT and BSD licensed.

If you use Duckoder in academic work, [CITATION.cff](CITATION.cff) has the metadata GitHub turns
into a citation.

### About the generated code

The platform writes a draft. A language model can produce code that does not compile, that drives
a pin the board does not have, or that works in a way the student did not ask for — read it and
test it before flashing a board. The license says this in legal terms, and it is worth saying
plainly: the code comes with no warranty, and the risk of running it on hardware is whoever runs
it.
