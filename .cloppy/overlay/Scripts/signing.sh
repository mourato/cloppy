#!/bin/bash
# Resolve an existing Keychain identity, following GUGU's local build convention.
resolve_signing_identity() {
    local requested="${CLOPPY_CODE_SIGN_IDENTITY:-Apple Development}"
    local fingerprint name
    if [[ "$requested" =~ ^[[:xdigit:]]{40}$ ]]; then
        requested="$(printf '%s' "$requested" | tr '[:lower:]' '[:upper:]')"
    fi
    while IFS=$'\t' read -r fingerprint name; do
        if [[ "$fingerprint" == "$requested" || "$name" == "$requested" ||
            ( "$requested" == "Apple Development" && "$name" == "Apple Development:"* ) ]]; then
            printf '%s\n' "$fingerprint"
            return 0
        fi
    done < <(security find-identity -v -p codesigning 2>/dev/null |
        sed -nE 's/^[[:space:]]*[0-9]+\) ([[:xdigit:]]{40}) "([^"]+)".*/\1\t\2/p')
    printf 'Signing certificate unavailable: %s\nSet CLOPPY_CODE_SIGN_IDENTITY to an existing certificate name or SHA-1.\n' "$requested" >&2
    return 1
}
