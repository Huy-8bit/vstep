#!/usr/bin/env bash
set -euo pipefail
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
terraform_dir="$root_dir/devops/terraform"
command -v terraform >/dev/null || { echo 'terraform CLI is required' >&2; exit 1; }
command -v aws >/dev/null || { echo 'AWS CLI is required' >&2; exit 1; }
distribution_id="$(terraform -chdir="$terraform_dir" output -raw cloudfront_distribution_id)"
test -n "$distribution_id"
aws cloudfront create-invalidation --distribution-id "$distribution_id" --paths '/*'
