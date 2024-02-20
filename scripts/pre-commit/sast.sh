#!/bin/bash
# shellcheck disable=SC2154,SC2086,SC2046,SC2199

scan_config="--config p/default "
ext=$(git diff --cached --name-only --diff-filter=ACM | sed 's/.*\.//' | sort | uniq -c | sort -rn | awk '{print $2}')
for e in $ext; do
  if [[ $e == "py" ]]; then
    scan_config+="--config p/python  --config p/django "
  elif [[ $e == "js" ]]; then
    scan_config+="--config p/javascript  --config p/react "
  elif [[ $e == "ts" ]]; then
    scan_config+="--config p/typescript  --config p/react "
  elif [[ $e == "json" ]]; then
    scan_config+="--config p/json "
  elif [[ $e == "yaml" ]]; then
    scan_config+="--config p/yaml "
  elif [[ $e == "tf" ]]; then
    scan_config+="--config p/terraform "
  elif [[ $e == "kt" ]]; then
    scan_config+="--config p/kotlin "
  elif [[ $e == "swift" ]]; then
    scan_config+="--config p/swift "
  fi
done
conf="${scan_config% }"


if [[ $(uname) == "Darwin" ]]; then
  #v1.51.0
  docker run --platform linux/arm64 --rm -v "${PWD}:/src" returntocorp/semgrep@sha256:19b7c24f45fb77856ce8d9e7fb1d3f91886f4adcf74ac4981328e9ca6f4c22aa semgrep ci $conf --dry-run --baseline-commit HEAD
else
  #v1.51.0
  docker run --platform linux/amd64 --rm -v "${PWD}:/src" returntocorp/semgrep@sha256:921f2b6dcfbf9bb2ebfd3a4b9736a067a713dceb40710cff9b80980aa8f40fa7 semgrep ci $conf --dry-run --baseline-commit HEAD
fi
