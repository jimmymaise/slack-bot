## How to create CI user

1. Cd to folder tf_ci_account
2. Add below environment variable to the deployment machine. Replace us-west-2 and leave-management-bimodal depend 
on environment you are working for.
    1. export REGION=us-west-2
    2. export S3_BACKEND_BUCKET=leave-management-bimodal
4. terraform init -backend-config="bucket="${S3_BACKEND_BUCKET}"" -backend-config="region="${REGION}""
5. terraform apply
6. Run below command to get the secret key (You must have jq)
   1. terraform state pull | jq '.resources[] | select(.type == "aws_iam_access_key") | .instances[0].attributes.secret'
7. copy aws access key, aws secret key and use them for Github actions