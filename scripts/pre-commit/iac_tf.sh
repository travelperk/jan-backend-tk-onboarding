#!/bin/bash

if ! docker ps > /dev/null 2>&1; then echo "Docker not available. Skipping check - See results in GitHub" && exit 0; fi

# check if arg is passed
if [ -z "$1" ]; then
  crit="CRITICAL"
else
  crit="$1"
fi

fc=$(git diff --diff-filter=d --name-only --cached -- 'modules/*.tf' | xargs dirname 2>/dev/null | sort | uniq)
for module in $fc; do
  echo "Running tfsec on $module"
  if [[ $(uname) == "Darwin" ]]; then
    #v1.28.4
    docker run -v "$(pwd):/app" aquasec/tfsec@sha256:e3fb79323c567e51d032b61af6e0a9a0c79a73fe3ce02f2e1ba3427c906cc2d4 /app/"$module" --exclude-downloaded-modules --exclude-path /app/.terragrunt-cache --exclude-path /app/.tfstate --exclude-path /app/modules/it --exclude-path /app/modules/tklabs --minimum-severity "$crit"
  else
    #v1.28.4
    docker run -v "$(pwd):/app" aquasec/tfsec@sha256:f50fe4477816dd2697a10c4e12e13541fb9f58dcc010e4848a743be17f5d4abf /app/"$module" --exclude-downloaded-modules --exclude-path /app/.terragrunt-cache --exclude-path /app/.tfstate --exclude-path /app/modules/it --exclude-path /app/modules/tklabs --minimum-severity "$crit"
  fi
done
