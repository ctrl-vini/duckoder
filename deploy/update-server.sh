#!/bin/sh
# Updates the Duckoder server to one version. The deploy workflow sends it to the EC2 instance
# through Systems Manager, which runs it as root after setting TAG, IMAGE, REGISTRY, REPOSITORY
# and REGION, and DOMAIN when the site has one.
set -eu

APP_DIR=/opt/duckoder
# Parameter Store parameter, a SecureString, holding the key of the Claude API.
KEY_PARAMETER=/duckoder/anthropic-api-key
# How long the new web server may take to report healthy once its container starts.
HEALTHY_TIMEOUT_S=120

# Downloads one of the files of this version from the public repository.
fetch() {
    curl -fsSL "https://raw.githubusercontent.com/$REPOSITORY/$TAG/$1" -o "$1"
}

# Sets a line of .env, which Compose reads in this folder, or removes it when the value is empty.
# Other settings added to .env, such as APP_OLLAMA_MODEL, are kept.
set_env() {
    sed -i "/^$1=/d" .env
    if [ -n "$2" ]; then
        echo "$1=$2" >> .env
    fi
}

mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Docker gets the ECR credentials from the instance role through the credential helper, so the
# server stores no password and needs no docker login.
export DOCKER_CONFIG=/root/.docker
mkdir -p "$DOCKER_CONFIG"
printf '{ "credHelpers": { "%s": "ecr-login" } }\n' "$REGISTRY" > "$DOCKER_CONFIG/config.json"

# The services as the version describes them, and that version's image for the web server.
fetch compose.yaml
# .env holds the settings of this server, the Claude API key among them, so only its owner, root,
# may read it.
touch .env
chmod 600 .env
set_env DUCKODER_IMAGE "$IMAGE"

# The key of the Claude API is read from Parameter Store on the instance itself. It is never in
# this script, which Systems Manager keeps in its command history for 30 days, nor in the
# workflow that sends it. Ubuntu has no package for the AWS CLI, and the snap that installs it
# puts it in a folder outside the PATH this script is run with.
PATH="$PATH:/snap/bin"
if ! command -v aws > /dev/null; then
    snap install aws-cli --classic
fi

# Without the parameter, the key already in .env is kept: a server answering with a local model
# needs none of this.
if key=$(aws ssm get-parameter --region "$REGION" --name "$KEY_PARAMETER" --with-decryption \
    --query Parameter.Value --output text 2> ssm-error.txt); then
    set_env APP_ANTHROPIC_API_KEY "$key"
    echo "Read the key of the Claude API from $KEY_PARAMETER."
elif grep -q ParameterNotFound ssm-error.txt; then
    echo "No $KEY_PARAMETER parameter: keeping the key already in .env, if any."
else
    cat ssm-error.txt >&2
    echo "Could not read $KEY_PARAMETER." >&2
    exit 1
fi
rm -f ssm-error.txt

# With a domain, Caddy serves the site over HTTPS on ports 80 and 443, from compose.proxy.yaml;
# without one, the web server answers on port 8000.
# The bare domain, also when the variable was given with www.
domain=${DOMAIN:-}
domain=${domain#www.}
if [ -n "$domain" ]; then
    fetch compose.proxy.yaml
    set_env COMPOSE_FILE compose.yaml:compose.proxy.yaml
else
    rm -f compose.proxy.yaml
    set_env COMPOSE_FILE ""
fi
set_env DUCKODER_DOMAIN "$domain"

docker compose pull --quiet
# The first start waits for the model download, several minutes, before starting the server.
# Turning the domain off leaves the proxy out of the services, so it is removed as an orphan.
docker compose up -d --no-build --remove-orphans

container=$(docker compose ps -q app)
waited=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' "$container")" = healthy ]; do
    if [ "$waited" -ge "$HEALTHY_TIMEOUT_S" ]; then
        docker compose logs --tail 50 app
        echo "The web server did not become healthy in $HEALTHY_TIMEOUT_S s." >&2
        exit 1
    fi
    sleep 5
    waited=$((waited + 5))
done

# The images of earlier versions are no longer needed; the model and the conversations are in
# volumes, which stay.
docker image prune -f
docker compose ps
echo "Duckoder $TAG is running."
