#!/bin/bash
# shellcheck disable=SC2154,SC2016

if ! docker ps > /dev/null 2>&1; then echo "Docker not available. Skipping check - See results in GitHub" && rm -rf ./output && exit 0; fi

diff=$(git diff --cached --name-only | grep -v -E 'test|node_modules')

req_py=$(grep "requirements.txt" <<< "$diff")
req_pnpm=$(grep "pnpm-lock.yaml" <<< "$diff")
req_npm=$(grep "package-lock.json" <<< "$diff")

if [[ -n "$req_py" || -n "$req_pnpm" || -n "$req_npm" ]]; then exit 0; fi

if [[ -n "$req_py" ]]; then
  for file in $req_py; do
    echo "$file updated, scanning content"
    if [[ $(uname) == "Darwin" ]]; then
      #v0.47.0
      docker run --rm -v "$PWD":/myapp aquasec/trivy@sha256:d5a39d66fd0fd3f842fd3e94ab4a39e401a7c7df9cdf74a9b6c911c0f2dd29f1 fs myapp/"$file" --ignore-unfixed --scanners vuln --quiet --exit-code 0
    else
      #v0.47.0
      docker run --rm -v "$PWD":/myapp aquasec/trivy@sha256:163b935486680eefe46e38534eaeabd95e36e0e6b7b3fa5d08fb1e05c6ad9f20 fs myapp/"$file" --ignore-unfixed --scanners vuln --quiet --exit-code 0
    fi
  done
fi

if [[ -n "$req_pnpm" ]]; then
  for file in $req_pnpm; do
    echo "$file updated, scanning content"
    if [[ $(uname) == "Darwin" ]]; then
      #v0.47.0
      docker run --rm -v "$PWD":/myapp aquasec/trivy@sha256:d5a39d66fd0fd3f842fd3e94ab4a39e401a7c7df9cdf74a9b6c911c0f2dd29f1 fs myapp/"$file" --ignore-unfixed --scanners vuln --quiet --exit-code 0
    else
      #v0.47.0
      docker run --rm -v "$PWD":/myapp aquasec/trivy@sha256:163b935486680eefe46e38534eaeabd95e36e0e6b7b3fa5d08fb1e05c6ad9f20 fs myapp/"$file" --ignore-unfixed --scanners vuln --quiet --exit-code 0
    fi
  done
fi

if [[ -n "$req_npm" ]]; then
  for file in $req_npm; do
    echo "$file updated, scanning content"
    if [[ $(uname) == "Darwin" ]]; then
      #v0.47.0
      docker run --rm -v "$PWD":/myapp aquasec/trivy@sha256:d5a39d66fd0fd3f842fd3e94ab4a39e401a7c7df9cdf74a9b6c911c0f2dd29f1 fs myapp/"$file" --ignore-unfixed --scanners vuln --quiet --exit-code 0
    else
      #v0.47.0
      docker run --rm -v "$PWD":/myapp aquasec/trivy@sha256:163b935486680eefe46e38534eaeabd95e36e0e6b7b3fa5d08fb1e05c6ad9f20 fs myapp/"$file" --ignore-unfixed --scanners vuln --quiet --exit-code 0
    fi
  done
fi
