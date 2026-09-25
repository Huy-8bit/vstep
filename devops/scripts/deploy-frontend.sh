#!/usr/bin/env bash
set -euo pipefail
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
terraform_dir="$root_dir/devops/terraform"
output_dir="$root_dir/frontend/out"
command -v terraform >/dev/null || { echo 'terraform CLI is required' >&2; exit 1; }
command -v aws >/dev/null || { echo 'AWS CLI is required' >&2; exit 1; }
test -s "$output_dir/index.html" || { echo 'Static export missing; run build-frontend.sh first.' >&2; exit 1; }
bucket="$(terraform -chdir="$terraform_dir" output -raw frontend_bucket_name)"
test -n "$bucket"
# Upload immutable hashed bundles first, then HTML/non-fingerprinted objects with revalidation.
aws s3 sync "$output_dir/" "s3://$bucket/" --exclude '*' --include '_next/static/*' --cache-control 'public,max-age=31536000,immutable' --no-progress --delete
aws s3 sync "$output_dir/" "s3://$bucket/" --exclude '_next/static/*' --cache-control 'no-cache,max-age=0,must-revalidate' --no-progress --delete
"$root_dir/devops/scripts/invalidate-cloudfront.sh"
