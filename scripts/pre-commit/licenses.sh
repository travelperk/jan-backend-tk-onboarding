#!/bin/bash
# shellcheck disable=SC2154

mkdir -p ./output/prod/ ./output/dev/

prod_req="./output/prod/requirements.txt"
dev_req="./output/dev/requirements.txt"
licenses="./output/licenses.txt"

if ! pip-licenses --version &>/dev/null; then printf "pip-licenses package not found please run: pip install pip-licenses" && rm -rf ./output/ && exit 1; fi

pip-licenses | grep 'GPL\|GPLv2\|GPLv3\|Artistic\|MPL\|ASL\|GNU\|Eclipse\|CNRI' | grep -v 'Lesser' | awk '{print tolower($0)}' > "$licenses"
git diff --cached -- requirements.txt | grep '^\+' | sed 's/^+//' | grep '^[a-zA-Z].*=[^=]*$' | cut -d= -f1 > "$prod_req"
result=$(awk 'NR==FNR{words[$0]=1;next} $1 in words' "$prod_req" "$licenses")
[[ -n "$result" ]] && printf "requirements.txt updated. The following packages are not allowed due to their licenses:\n %s" "$result"
git diff --cached -- requirements-dev.txt | grep '^\+' | sed 's/^+//' | grep '^[a-zA-Z].*=[^=]*$' | cut -d= -f1 > "$dev_req"
result=$(awk 'NR==FNR{words[$0]=1;next} $1 in words' "$dev_req" "$licenses")
[[ -n "$result" ]] && printf "requirements-dev.txt updated. The following packages are not allowed due to their licenses:\n %s" "$result"
rm -rf ./output/
