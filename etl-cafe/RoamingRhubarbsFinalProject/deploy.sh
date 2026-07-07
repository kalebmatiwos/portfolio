#!/bin/sh
set -eu

###
### Script to deploy S3 bucket in cloudformation stack
###

#### CONFIGURATION SECTION ####
aws_profile="KalebDE" # e.g. sot-academy, for the aws credentials
team_name="roamingrhubarbs" # e.g. rory-gilmore (WITH DASHES), for the stack name
region="eu-west-1"
#### CONFIGURATION SECTION ####

# Deploy the stack
echo ""
echo "Doing deployment stack deployment..."
echo ""
aws cloudformation deploy --stack-name ${team_name}-deployment-stack \
    --template-file deployment-stack.yml --region ${region} \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile ${aws_profile};

DEPLOYMENT_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name ${team_name}-deployment-stack \
    --region ${region} \
    --profile ${aws_profile} \
    --query "Stacks[0].Outputs[?OutputKey=='DeploymentBucketName'].OutputValue" \
    --output text)

echo ""
echo "...all done!"
echo ""

echo "Packaging Lambda Function"
rm -rf lambda_build
mkdir lambda_build
python3 -m pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.14 \
  --only-binary=:all: \
  --target lambda_build \
  psycopg2-binary python-dotenv boto3
cp lambda/lambda_function.py lambda_build/
cp -r ETL lambda_build/
cp -r databases lambda_build/
cd lambda_build
zip -r ../lambda/lambda.zip .
cd ..
rm -rf lambda_build 

echo "Packaged Lambda Function"

echo "Uploading Lambda"
aws s3 cp \
lambda/lambda.zip \
s3://$DEPLOYMENT_BUCKET/lambda.zip \
--region ${region} \
--profile ${aws_profile};
echo "Uploaded Lambda"


echo ""
echo "Doing etl stack deployment..."
echo ""
aws cloudformation deploy --stack-name ${team_name}-ETL-stack \
    --template-file etl-stack.yml \
    --region eu-west-1 \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile ${aws_profile} \
    --parameter-overrides \
      DeploymentBucketName="${DEPLOYMENT_BUCKET}" \
      RedshiftSsmParameterName="roaming_rhubarb_redshift_settings" \
      LambdaSubnetIds="subnet-0b18baebb2612c8b0" \
      LambdaSecurityGroupIds="sg-0e23d4530f0fbf635";
    

echo ""
echo "Forcing Lambda to pick up latest code..."
echo ""

aws lambda update-function-code \
    --function-name roamingrhubarbs-etl-lambda \
    --s3-bucket "${DEPLOYMENT_BUCKET}" \
    --s3-key lambda.zip \
    --region ${region} \
    --profile ${aws_profile} \
    --publish;
echo "Lambda code updated"


echo ""
echo "...all done!"
echo ""