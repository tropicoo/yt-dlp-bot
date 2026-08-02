#!/usr/bin/env bash
#
# Rebuild and restart the stack, then reclaim the disk space the rebuild orphaned.
#
# Rebuilding retags an image and leaves the previous one untagged. Those
# leftovers, together with the build cache, fill the disk quietly until
# something fails in a way that looks unrelated, so cleaning up is part of
# deploying rather than a separate chore.
#
# Usage:
#   ./redeploy.sh                    rebuild and restart every application service
#   ./redeploy.sh yt_bot yt_worker   rebuild and restart only these
#   ./redeploy.sh --pull             update the current branch first
#   ./redeploy.sh --base             rebuild the base image too (base.Dockerfile changed)
#   ./redeploy.sh --no-cache         build without the layer cache
#   ./redeploy.sh --recreate         recreate containers even if unchanged
#   ./redeploy.sh --clean-only       reclaim space without building anything
#
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

readonly APP_SERVICES=(yt_bot yt_worker yt_api)
readonly BASE_SERVICE='base-image'
# Kept so an ordinary rebuild stays fast; only the excess is dropped.
readonly KEEP_BUILD_CACHE='5GB'
readonly ENV_NAMES=(common api bot worker)

DO_PULL=false
DO_BASE=false
DO_CLEAN_ONLY=false
NO_CACHE=false
RECREATE=false
SERVICES=()

info() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m!! %s\033[0m\n' "$*" >&2; }
die() { printf '\033[1;31mxx %s\033[0m\n' "$*" >&2; exit 1; }

# Prints the header comment, so the help can never drift from it.
usage() { awk 'NR>2 && /^#/ {sub(/^# ?/, ""); print; next} NR>2 {exit}' "$0"; exit 0; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pull) DO_PULL=true ;;
        --base) DO_BASE=true ;;
        --no-cache) NO_CACHE=true ;;
        --recreate) RECREATE=true ;;
        --clean-only) DO_CLEAN_ONLY=true ;;
        -h|--help) usage ;;
        -*) die "Unknown option: $1 (try --help)" ;;
        *) SERVICES+=("$1") ;;
    esac
    shift
done

[[ ${#SERVICES[@]} -eq 0 ]] && SERVICES=("${APP_SERVICES[@]}")

command -v docker >/dev/null || die 'docker is not installed'
docker compose version >/dev/null 2>&1 || die 'docker compose v2 is required'

disk_free() {
    local root
    root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo /var/lib/docker)"
    df -Ph "${root}" | awk 'NR==2 {print $4 " free of " $2}'
}

# Compose before 2.24 has no "required: false", so a missing env_file is a hard
# error there. Creating the overrides empty costs nothing and keeps both old and
# new Compose working from a bare clone.
ensure_local_envs() {
    local name path created=()
    for name in "${ENV_NAMES[@]}"; do
        path="envs/${name}.local.env"
        [[ -e "${path}" ]] && continue
        cat > "${path}" <<EOF
# Your settings for ${name}.env. Gitignored and loaded last, so anything set
# here wins over the shipped default. See envs/README.md.
EOF
        created+=("${path}")
    done
    [[ ${#created[@]} -gt 0 ]] && info "Created empty overrides: ${created[*]}"
    return 0
}

# The tracked files are shipped defaults; editing them in place is what makes a
# pull stop dead, and the message git gives says nothing about the fix.
warn_if_tracked_config_edited() {
    local dirty
    dirty="$(git diff --name-only -- envs/ docker-compose.yml 2>/dev/null || true)"
    [[ -z "${dirty}" ]] && return 0
    warn "These shipped defaults have been edited in place:
$(printf '    %s\n' ${dirty})
  A pull will refuse to overwrite them. Move your changes into the file beside
  each one that is meant for them — envs/*.local.env, or
  docker-compose.override.yml — then run 'git checkout -- <file>'.
  See envs/README.md and docker-compose.override.example.yml."
}

reclaim_space() {
    info "Reclaiming space (was: $(disk_free))"
    # Untagged leftovers only: images still carrying a tag are never touched,
    # so other projects on this host are unaffected.
    docker image prune --force
    if ! docker builder prune --force --keep-storage "${KEEP_BUILD_CACHE}" 2>/dev/null; then
        warn "--keep-storage unsupported by this Docker, dropping the whole build cache"
        docker builder prune --force
    fi
    info "Now: $(disk_free)"
}

if [[ "${DO_CLEAN_ONLY}" == true ]]; then
    reclaim_space
    exit 0
fi

if [[ "${DO_PULL}" == true ]]; then
    branch="$(git rev-parse --abbrev-ref HEAD)"
    # Follow whatever this branch tracks: the remote is not necessarily called
    # "origin", and the local and remote branch names need not match.
    if ! upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)"; then
        die "Branch '${branch}' tracks nothing. Point it at a remote branch once with:
    git branch --set-upstream-to=<remote>/<branch>
  then rerun, or build without --pull."
    fi
    warn_if_tracked_config_edited
    info "Updating ${branch} from ${upstream}"
    git pull --ff-only \
        || die "Pull failed. Resolve it by hand, then rerun without --pull."
fi

ensure_local_envs

build_args=()
[[ "${NO_CACHE}" == true ]] && build_args+=(--no-cache)

if [[ "${DO_BASE}" == true ]]; then
    info "Building ${BASE_SERVICE}"
    docker compose build "${build_args[@]+"${build_args[@]}"}" "${BASE_SERVICE}"
fi

info "Building: ${SERVICES[*]}"
docker compose build "${build_args[@]+"${build_args[@]}"}" "${SERVICES[@]}"

up_args=(--detach)
[[ "${RECREATE}" == true ]] && up_args+=(--force-recreate)

info "Starting: ${SERVICES[*]}"
docker compose up "${up_args[@]}" "${SERVICES[@]}"

# Dependencies such as the database or broker may be stopped after a failure,
# so bring up whatever else the stack needs.
docker compose up --detach

reclaim_space

info 'Current state'
docker compose ps

cat <<EOF

Follow the logs with:
  docker compose logs -f ${SERVICES[*]}
EOF
