#!/bin/bash

if ! docker ps > /dev/null 2>&1; then echo "Docker not available. Skipping check - See results in GitHub" && exit 0; fi

Dockerfile=$(find . -regex ".*Dockerfile.*" -not -path "./**/*test*/**")
for file in $Dockerfile; do
  echo "file $file was modified"
    if [[ $(uname) == "Darwin" ]]; then
      #v0.47.0
      docker run -v "$PWD:/app" --rm aquasec/trivy@sha256:d5a39d66fd0fd3f842fd3e94ab4a39e401a7c7df9cdf74a9b6c911c0f2dd29f1 config "/app/$file" --quiet --exit-code 0
    else
      #v0.47.0
      docker run -v "$PWD:/app" --rm aquasec/trivy@sha256:163b935486680eefe46e38534eaeabd95e36e0e6b7b3fa5d08fb1e05c6ad9f20 config "/app/$file" --quiet --exit-code 0
    fi
done
