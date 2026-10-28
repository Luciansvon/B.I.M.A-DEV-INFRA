#!/usr/bin/env bash
# Install the digest-pinned workflow security tools used by CI and the reusable template.
set -euo pipefail

destination="${1:?usage: install_security_tools.sh DESTINATION}"
mkdir -p "$destination"
trap 'rm -f "$destination"/*.download' EXIT

fetch_verified() {
  local name="$1" url="$2" digest="$3"
  local archive="$destination/$name.download"
  curl --fail --location --silent --show-error --output "$archive" "$url"
  printf '%s  %s\n' "$digest" "$archive" | sha256sum --check --status
  printf '%s\n' "$archive"
}

action_validator="$(fetch_verified action-validator \
  https://github.com/mpalmer/action-validator/releases/download/v0.9.0/action-validator_linux_amd64 \
  9f42f94fca5b8d04c13bccfbb331104b37a9250650d89ae58dc888d46206f9b9)"
install -m 0755 "$action_validator" "$destination/action-validator"
rm -f "$action_validator"

pinact_archive="$(fetch_verified pinact \
  https://github.com/suzuki-shunsuke/pinact/releases/download/v4.1.1/pinact_linux_amd64.tar.gz \
  d1cffebe5704b74e2e5f8a864efb9f7e54768972dc686188c008033fb1797841)"
tar -xzf "$pinact_archive" -C "$destination" pinact
rm -f "$pinact_archive"

zizmor_archive="$(fetch_verified zizmor \
  https://github.com/zizmorcore/zizmor/releases/download/v1.31.1/zizmor-x86_64-unknown-linux-gnu.tar.gz \
  d185f726bdaf92df78273217dfdd24ebcd6b0ef48cf3ce776ff5762b6e138c99)"
tar -xzf "$zizmor_archive" -C "$destination" zizmor
rm -f "$zizmor_archive"

for tool in action-validator pinact zizmor; do
  [[ -x "$destination/$tool" ]] || { echo "missing verified $tool" >&2; exit 1; }
done
