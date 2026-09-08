#!/bin/sh

set -u

mode="${1:-}"
evidence="${2:-/evidence}"
actionlint_version="1.7.12"
actionlint_sha256="8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"

mkdir -p "$evidence"

run_audit() {
  mkdir -p "$evidence/audit"
  python -I automation/repository_audit.py \
    --root . \
    --policy .bima/audit.json \
    --output "$evidence/audit"
  code=$?
  printf '%s\n' "$code" > "$evidence/audit.exit-code"
}

run_tests() {
  python -I -m unittest discover -s tests -v > "$evidence/tests.log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$evidence/tests.exit-code"
}

run_workflow_lint() {
  archive="/tmp/actionlint.tar.gz"
  binary="/tmp/actionlint"
  log="$evidence/actionlint.log"

  if ! curl --fail --location --silent --show-error \
    --output "$archive" \
    "https://github.com/rhysd/actionlint/releases/download/v${actionlint_version}/actionlint_${actionlint_version}_linux_amd64.tar.gz" > "$log" 2>&1; then
    printf '2\n' > "$evidence/actionlint.exit-code"
    return
  fi

  if ! printf '%s  %s\n' "$actionlint_sha256" "$archive" | sha256sum --check >> "$log" 2>&1; then
    printf '2\n' > "$evidence/actionlint.exit-code"
    return
  fi

  if ! tar -xzf "$archive" -C /tmp actionlint >> "$log" 2>&1; then
    printf '2\n' > "$evidence/actionlint.exit-code"
    return
  fi

  "$binary" -version >> "$log" 2>&1
  "$binary" -shellcheck= -pyflakes= >> "$log" 2>&1
  code=$?
  printf '%s\n' "$code" > "$evidence/actionlint.exit-code"
}

write_summary() {
  python -I automation/write_ci_summary.py --evidence "$evidence"
}

case "$mode" in
  audit)
    run_audit
    ;;
  tests)
    run_tests
    ;;
  workflow-lint)
    run_workflow_lint
    ;;
  ci)
    run_tests
    run_audit
    run_workflow_lint
    write_summary
    ;;
  *)
    printf 'usage: %s audit|tests|workflow-lint|ci [evidence-dir]\n' "$0" >&2
    exit 2
    ;;
esac

exit 0
