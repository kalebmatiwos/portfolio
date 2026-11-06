#!/usr/bin/env bash
# Builds and deploys infra/template.yaml with AWS SAM.
#
# Not strictly required -- `sam build --use-container && sam deploy
# --guided` from infra/ does the same thing interactively. This just
# also handles creating the Secrets Manager secret for your GFW token,
# so the whole "first deploy" is one command. See README "Deploy to
# AWS" for the full walkthrough and prerequisites.
#
# Usage:
#   ./deploy.sh                     # prompts for your GFW token if the secret doesn't exist yet
#   GFW_API_TOKEN=xxx ./deploy.sh   # non-interactive

set -euo pipefail

STACK_NAME="take-home-assignment"
SECRET_NAME="take-home-assignment/gfw-api-token"
REGION="${AWS_REGION:-eu-west-2}"

command -v sam >/dev/null 2>&1 || {
  echo "AWS SAM CLI not found. Install it first:"
  echo "  https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
  exit 1
}

aws sts get-caller-identity >/dev/null 2>&1 || {
  echo "AWS credentials not configured or invalid. Run 'aws configure' first."
  exit 1
}

if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$REGION" >/dev/null 2>&1; then
  echo "Secret $SECRET_NAME already exists -- leaving it as is."
else
  if [ -z "${GFW_API_TOKEN:-}" ]; then
    read -rsp "Enter your GFW API token (input hidden, not echoed or logged): " GFW_API_TOKEN
    echo
  fi
  aws secretsmanager create-secret \
    --name "$SECRET_NAME" \
    --secret-string "$GFW_API_TOKEN" \
    --region "$REGION" >/dev/null
  echo "Created secret $SECRET_NAME"
fi

SECRET_ARN=$(aws secretsmanager describe-secret --secret-id "$SECRET_NAME" --region "$REGION" --query "ARN" --output text)

command -v docker >/dev/null 2>&1 || {
  echo "Docker not found. sam build --use-container needs it to build against"
  echo "the exact Lambda Python environment, regardless of your local Python"
  echo "version -- install Docker Desktop first: https://www.docker.com/products/docker-desktop/"
  exit 1
}

cd "$(dirname "$0")/infra"
sam build --use-container

if [ -f samconfig.toml ]; then
  sam deploy \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides "GfwApiTokenSecretArn=$SECRET_ARN" \
    --no-confirm-changeset
else
  sam deploy \
    --guided \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides "GfwApiTokenSecretArn=$SECRET_ARN"
fi

STATE_MACHINE_ARN=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" \
  --output text)

echo
echo "Deployed. It'll run automatically once a day, or trigger it right now with:"
echo "  aws stepfunctions start-execution --state-machine-arn $STATE_MACHINE_ARN --region $REGION"
