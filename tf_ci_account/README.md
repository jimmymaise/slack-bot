## How to create CI user

1. Cd to folder tf_ci_account
2. Add below environment variable to the deployment machine
    1. export REGION=`<the aws region>`
    2. export S3_BACKEND_BUCKET=`<The s3 bucket name to store the bucket>`
3. terraform init -backend-config="bucket="${S3_BACKEND_BUCKET}"" -backend-config="region="${REGION}""
4. terraform apply
5. Run below command to get the secret key
   1. terraform state pull | jq '.resources[] | select(.type == "aws_iam_access_key") | .instances[0].attributes.secret'
6. copy aws access key, aws secret key and use them for Github actions