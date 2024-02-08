#!/bin/bash
set -e # causes the shell to exit if any subcommand or pipeline returns a non-zero status.

repo=$(basename "$(pwd)")

CODEOWNERS_VALIDATOR_VERSION="v0.7.4"
export AWS_PROFILE=tooling

run_validator() {
  # Run Codeowners Validator on local
  set +e  # Do not exit with codeowners-validator failure as we want to parse the output
  docker run --rm \
    -v "$(pwd)":/repo \
    -w /repo \
    -e REPOSITORY_PATH="." \
    -e CHECKS="files" \
    -e EXPERIMENTAL_CHECKS="notowned" \
    -e OWNER_CHECKER_REPOSITORY="travelperk/$repo" \
    -e OWNER_CHECKER_OWNERS_MUST_BE_TEAMS="true" \
    -e NOT_OWNED_CHECKER_TRUST_WORKSPACE="true" \
    256045177368.dkr.ecr.eu-west-1.amazonaws.com/codeowners-validator:$CODEOWNERS_VALIDATOR_VERSION
  set -e
}

invalid_rules_exceptions=(
  "\*\*/migrations/\*"
  "\*\.min\.js"
  "\*\.min\.css"
  "\*\.bundle\.js"
  "\*bootstrap\*\.js"
  "\*jquery\*\.js"
  "\*\.woff"
  "\*\.png"
  "\*\.jpg"
  "\*\.svg"
  "\*\.gif"
  "\*\.gitkeep"
  "travelperk/\*/last_migration\.txt"
  "__init__.py"
)
invalid_rule_exceptions_regex=$(printf '%s\n' "$(IFS=\|; printf '%s' "${invalid_rules_exceptions[*]}")")
invalid_rules=$(grep -Env '^(#.*|.* @.*)$|^$' CODEOWNERS | grep -Ev "$invalid_rule_exceptions_regex" || echo '')
if [ -n "$invalid_rules" ];
then
  echo "❌ All rules must follow the syntax 'file_path owner', e.g. /travelperk/test.py @travelperk/squad-coreservices."
  echo "These rules are not following the syntax:"
  echo "$invalid_rules"
  exit 1
fi


# Run validator
result=$(run_validator)

if echo "$result" | grep -q "no failure(s)"; then # Check that there are some errors
      echo "✅ There are no new files without owner 🙌"
      exit 0
    else
      echo "$result"
      echo "❌ Error: Detected some issues in the CODEOWNERS file, please, correct them."
      exit 1
fi
