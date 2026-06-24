# portfolio-project-1

A basic REST API built with AWS serverless services, designed to store and retrieve items from a DynamoDB table. The stack includes Amazon API Gateway, AWS Lambda, and DynamoDB for the core functionality, plus a CloudWatch Alarm and SNS Topic for error monitoring and e-mail alerting.


## Architecture

![Architecture](docs/architecture.png)


## Technologies

**AWS Services**
- AWS Lambda (environment provided by AWS for Python 3.14)
- Amazon API Gateway
- Amazon DynamoDB
- Amazon CloudWatch
- Amazon SNS

**Infrastructure & Tooling**
- AWS SAM (Server Application Model)
- LocalStack (local AWS emulation)
- Docker


## Prerequisites

- [Docker Desktop + WSL] (https://www.docker.com/products/docker-desktop/)
- [Python 3.14+] (https://www.python.org/downloads/)
- [LocalStack CLI] (https://docs.localstack.cloud/aws/getting-started/installation/): create a free account to generate an auth token (https://docs.localstack.cloud/aws/getting-started/auth-token/). LocalStack can be installed with the command `pip install localstack`
- [AWS CLI V2] (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) configured with a `localstack` profile
- [AWS SAM CLI] (https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [samlocal] (https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/aws-sam/#samlocal-wrapper-script)


## Local setup with LocalStack

Follow these steps to deploy the application locally using LocalStack:

1. Clone this repository on your local machine.

2. Make sure Docker Desktop is running. Open a terminal and start LocalStack:

   ```powershell
   localstack start
   ```

   Wait until `Ready` appears in the output.

3. Create the S3 bucket that SAM uses to upload the deployment package:

   ```powershell
   aws s3 mb s3://awssamcli-managed-default --profile localstack
   ```

4. Open `samconfig.toml`, uncomment the `parameter_overrides` line and replace `#INSERT NOTIFICATION E-MAIL ADDRESS#` with your email address.

5. Build the project:

   ```powershell
   samlocal build
   ```

6. Deploy the stack:
   
   ```powershell
   samlocal deploy --config-env localstack
   ```

   When the deploy completes, the API endpoint URL is shown in the `Outputs` section under `ItemsApi`.


## Run the tests

### Prerequisites to run unit and integration tests
To execute all tests, it's necessary to install the Python libraries `pytest` and `boto3` with this command:

```powershell
pip install pytest boto3
```

### Run unit tests
Launch this command from the root folder of this project:

```powershell
python -m pytest tests/unit/ -v
```

### Run integration tests
To run the integration tests:

1. the application must be deployed and running on LocalStack

2. these environment variables must be defined:

   ```powershell
   $env:AWS_SAM_STACK_NAME = "portfolio-project-1"
   $env:CLOUDFORMATION_ENDPOINT = "http://localhost.localstack.cloud:4566"
   $env:AWS_PROFILE = "localstack"
   ```

3. run integration tests with this command from the root folder of this project:
   
   ```powershell
   python -m pytest tests/integration/ -v
   ```


## Deploy on AWS

Steps to run the project into the cloud:

- create a new user or use an existing one different from the root user and assign it an access key to communicate with your AWS account through the AWS CLI. Then you can associate to this user the AWS managed policy called `AdministratorAccess` for simplicity, but this policy is too permissive and so this solution is not recommended. For a more restrictive behaviour that respects the least privilege principle, you can associate to your user the following AWS managed policies:
   
   - `AWSCloudFormationFullAccess`
   - `AWSLambda_FullAccess`
   - `AmazonAPIGatewayAdministrator`
   - `AmazonDynamoDBFullAccess`
   - `CloudWatchFullAccess`
   - `AmazonSNSFullAccess`
   - `AmazonS3FullAccess`

and a custom IAM policy defined like this:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:GetRole",
                "iam:PassRole",
                "iam:DetachRolePolicy",
                "iam:DeleteRolePolicy",
                "iam:ListAttachedRolePolicies",
                "iam:TagRole",
                "iam:CreateRole",
                "iam:DeleteRole",
                "iam:AttachRolePolicy",
                "iam:PutRolePolicy",
                "iam:ListRolePolicies",
                "iam:GetRolePolicy"
            ],
            "Resource": "arn:aws:iam::*:role/portfolio-project-1-*"
        }
    ]
}
```

Then you have to create a new AWS profile through the command:

```powershell
   aws configure --profile <PROFILE_NAME_FOR_PROJECT_DEPLOYMENT_ON_AWS>
```

- give a value to the parameters `region`, `profile` and to the "AlertEmail=" string inside the parameter `parameter_overrides` under the `[aws.deploy.parameters]` group of parameters, inside the `samconfig.toml` file.

- give a value to the `IpRangeWhitelist` property inside the `template.yaml` file. This property is used to associate a resource policy to the REST api endpoint. This introduces a basic level of security because it allows only a defined IP to invoke the endpoints. The IP of the machine, from which you make the requests, can be retrieved through the command:

```powershell
   curl https://checkip.amazonaws.com
```

The value of the IP address must be in CIDR notation.

- use the following command to prepare the artifacts that will be used during the deployment on AWS:

```powershell
   sam build
```

- use the following command to deploy the artifacts on AWS:

```powershell
   sam deploy --config-env aws
```

The last command will print the url on the `Output` section in the same way as the `samlocal` command.
If all's gone well, you received a subscription e-mail from AWS SNS service. The acceptance is necessary to receive the alerting e-mail.

**IMPORTANT NOTE**: delete the trailing "/" inside the URI printed in the `Output` section by the command deploy. If you don't do this, the invocation will be denied because the resource policy, that SAM generates from the property `IpRangeWhiteList`, references the path without the trailing "/". For this reason all the requests with the trailing "/" fail the authorization.

- make some tests with Invoke-WebRequest command:

```powershell
   Invoke-WebRequest -Uri "<URI_WITHOUT_TRAILING_/>" -Method GET
```
```powershell
   Invoke-WebRequest -Uri "<URI_WITHOUT_TRAILING_/>" -Method POST -ContentType "application/json" -Body '{"name": "first AWS item", "description": "real deploy test"}'
```


## Testing the monitoring

To test the monitoring and alerting chain defined in the architecture, the Lambda function's
code includes an intentional trigger that raises an unhandled exception. Submit the following
POST request to activate it:

```powershell
   Invoke-WebRequest -Uri "<URI_WITHOUT_TRAILING_/>" -Method POST -ContentType "application/json" -Body '{"name": "TRIGGER_ERROR"}'
```

When the Lambda function raises this unhandled exception, the invocation is counted as an error in the `Errors` metric. Since the alarm threshold is set to 1 error within a 60-second period, even a single failed invocation is enough to trigger it. Once triggered, the alarm transitions to the `ALARM` state and publishes a message to the SNS topic, which sends a notification e-mail to the address confirmed during the subscription step.


## Cleanup

To remove all the resources created by the CloudFormation stack defined with SAM for this project, you can remove manually the stack "portfolio-project-1" from the CloudFormation web console or alternatively use the following command:

```powershell
   aws cloudformation delete-stack --stack-name portfolio-project-1 --profile <PROFILE_NAME_FOR_PROJECT_DEPLOYMENT_ON_AWS> --region <YOUR_AWS_REGION>
```

and monitor the execution of the deletion of the stack through the command:

```powershell
   aws cloudformation describe-stacks --stack-name portfolio-project-1 --profile <PROFILE_NAME_FOR_PROJECT_DEPLOYMENT_ON_AWS> --region <YOUR_AWS_REGION>
```

until it will return an output saying that stack does not exist anymore.

During the deployment phase, SAM creates also the stack "aws-sam-cli-managed-default" to create an S3 bucket inside which it stores the artifacts it uses. After the "portfolio-project-1" stack deletion, the S3 bucket "aws-sam-cli-managed-default-samclisourcebucket-*" managed by that stack is empty and can be left there because next time SAM will reuse it and an empty bucket will not generate significant costs.
If you want to delete this stack too, first you have to execute these instructions to delete all the versions of the artifacts inside the S3 bucket:

```powershell
   $awsProfile = "<PROFILE_NAME_FOR_PROJECT_DEPLOYMENT_ON_AWS>"

   $bucket = "<BUCKET_NAME_TO_EMPTY>" 

   $versions = aws s3api list-object-versions --bucket $bucket --profile $awsProfile --output json | ConvertFrom-Json

   foreach ($obj in $versions.Versions) {
       aws s3api delete-object --bucket $bucket --key $obj.Key --version-id $obj.VersionId --profile $awsProfile
   }

   foreach ($marker in $versions.DeleteMarkers) {
       aws s3api delete-object --bucket $bucket --key $marker.Key --version-id $marker.VersionId --profile $awsProfile
   }
```

Subsequently we can delete the stack "aws-sam-cli-managed-default" too with the command:

```powershell
   aws cloudformation delete-stack --stack-name aws-sam-cli-managed-default --profile <PROFILE_NAME_FOR_PROJECT_DEPLOYMENT_ON_AWS> --region <YOUR_AWS_REGION>
```


## Project structure

Here's a description of the folders and files present in the repository:

- **/docs**: contains the files used to build this README.

- **/events**: contains `event.json`, a sample API Gateway event used during local development with `sam local invoke`.

- **/items**: contains all the files needed by the Lambda function.
    - **app.py**: the Lambda function handler with the GET and POST logic.
    - **requirements.txt**: the Lambda function dependencies.

- **/tests**: contains unit and integration tests.
    - **/integration**: integration tests against LocalStack.
      - **test_api_gateway.py**: integration test suite for the API endpoints.
    - **/unit**: unit tests with mocked DynamoDB.
      - **test_handler.py**: unit test suite for the Lambda handler.
    - **requirements.txt**: test dependencies.

- **samconfig.toml**: SAM CLI configuration organized by command and environment.

- **template.yaml**: CloudFormation/SAM template that defines the entire infrastructure stack.