from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as _lambda,  # Import the Lambda module
    aws_iam as _iam,
    aws_logs as _logs,
    aws_apigateway as _apigw,
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
            role_name=f"{construct_id}-lambda-role",
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
        lambda_role.add_to_policy(
            _iam.PolicyStatement(
                actions=["dynamodb:DeleteItem", "dynamodb:PutItem", "dynamodb:Query", "dynamodb:GetItem",
                         "dynamodb:Scan", "dynamodb:UpdateItem"],
                resources=[dynamo_db_table.table_arn]
            )
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
            log_group_name=f"{construct_id}-log-group",
            retention=_logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Define the Lambda function resource
        lambda_function = _lambda.Function(
            self, "CdkLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="main.handler",
            function_name=f"{construct_id}-lambda",
            description=f"Lambda function for {ServerlessApplicationStack.stack_name}",
            code=_lambda.Code.from_asset("serverless_application/src"),
            timeout=Duration.seconds(900),  # Timeout in seconds
            memory_size=128,  # Memory in MBs
            role=lambda_role,
            environment={
                "TABLE_NAME": dynamo_db_table.table_name
            },
            log_group=log_group
        )

        apigw = _apigw.RestApi(
            self, "CdkApiGw",
            rest_api_name=f"{construct_id}-api",
            description="API Gateway for Serverless Application",
            deploy_options=_apigw.StageOptions(
                stage_name="dev",
                tracing_enabled=False,
                logging_level=_apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
                metrics_enabled=False,
            ),
            cloud_watch_role=True,
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["*"]
            )
        )
        users=apigw.root.add_resource("users")
        user=users.add_resource("{user_id}")
        apigw.node.add_dependency(dynamo_db_table, lambda_function)

        lambda_integration = _apigw.LambdaIntegration(
            lambda_function,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )
        users.add_method("GET", lambda_integration)
        user.add_method("GET", lambda_integration)

        deployment = _apigw.Deployment(
            self, "CdkApiGwDeployment",
            api=apigw,
            description="Deployment for Serverless Application",
            retain_deployments=False
        )


        CfnOutput(self, "LambdaFunctionName", value=lambda_function.function_name)
        CfnOutput(self, "LambdaFunctionArn", value=lambda_function.function_arn)
        CfnOutput(self, "LambdaFunctionRoleArn", value=lambda_role.role_arn)
        CfnOutput(self, "LambdaFunctionRoleName", value=lambda_role.role_name)
        CfnOutput(self, "LambdaFunctionLogGroupName", value=log_group.log_group_name)
        CfnOutput(self, "LambdaFunctionLogGroupArn", value=log_group.log_group_arn)
        CfnOutput(self, "DynamoDbTableName", value=dynamo_db_table.table_name)
        CfnOutput(self, "DynamoDbTableArn", value=dynamo_db_table.table_arn)
        CfnOutput(self, "ApiGatewayUrl", value=apigw.url)
