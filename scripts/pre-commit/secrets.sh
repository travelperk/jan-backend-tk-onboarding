#!/bin/bash
# shellcheck disable=SC2154,SC2002

if ! docker ps > /dev/null 2>&1; then echo "Docker not available. Skipping check - See results in GitHub" && exit 0; fi
if [[ $(uname) == "Darwin" ]]; then
  #v8.18.1
  docker run --rm -v "$PWD:/path" zricethezav/gitleaks@sha256:10f607e8e77f4afbccd98afe04a67eb853e27f76b80b6a9ebb159e43345c615d protect --source="/path" --staged --verbose --redact --no-banner
else
  #v8.18.1
  docker run --rm -v "$PWD:/path" zricethezav/gitleaks@sha256:65494a0d1ad9f408693a76b3a6d2be8719b82fd74933d5b563f3c7a85a90c534 protect --source="/path" --staged --verbose --redact --no-banner
fi
