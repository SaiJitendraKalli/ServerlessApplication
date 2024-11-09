from aws_cdk import (
    Stack,
    aws_lambda as _lambda,  # Import the Lambda module
    aws_iam as _iam,
    aws_logs as _logs,
    aws_dynamodb as _dynamodb,
    Duration, RemovalPolicy
)
from constructs import Construct


class ServerlessApplicationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dynamo_db_table = _dynamodb.Table(
            self, "CdkDynamoDbTable",
            table_name="SampleTable",
            partition_key=_dynamodb.Attribute(
                name="id",
                type=_dynamodb.AttributeType.STRING
            ),
            billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        lambda_role = _iam.Role(
            self, "LambdaRole",
            role_name="CdkLambdaRole",
            description="Role for Lambda to access services",
            # add assume role for DynamoDb and Lambda
            assumed_by=_iam.CompositePrincipal(
                _iam.ServicePrincipal("lambda.amazonaws.com"),
                _iam.ServicePrincipal("dynamodb.amazonaws.com")
            ),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                _iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaDynamoDBExecutionRole")
            ]
        )

        # Add permissions to the role
        # lambda_role.add_to_policy(
        #     _iam.PolicyStatement(
        #         actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        #         resources=["arn:aws:logs:*:*:*"]
        #     )
        # )
        # log group for Lambda with retention of 1 day and delete log group when stack deletes
        log_group = _logs.LogGroup(
            self, "LambdaLogGroup",
            log_group_name="CdkLambdaLogGroup",
            retention=_logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Define the Lambda function resource
        my_function = _lambda.Function(
            self, "HelloWorldFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            function_name="CdkHelloWorldFunction",
            code=_lambda.Code.from_asset("serverless_application/src"),
            timeout=Duration.seconds(900),  # Timeout in seconds
            memory_size=128,  # Memory in MBs
            role=lambda_role,
            environment={
                "TABLE_NAME": dynamo_db_table.table_name
            },
            log_group=log_group
        )
