#!/bin/bash

if ! docker ps > /dev/null 2>&1; then echo "Docker not available. Skipping check - See results in GitHub" && exit 0; fi
codeowners=$(find "$(pwd -P)" -name 'CODEOWNERS' -depth 1)
export AWS_PROFILE=tooling
docker run --rm -v "$codeowners:/scripts/CODEOWNERS" 256045177368.dkr.ecr.eu-west-1.amazonaws.com/beautify_codeowners:latest
