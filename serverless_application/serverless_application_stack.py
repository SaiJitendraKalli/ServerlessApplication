from aws_cdk import (
    Stack,
    CfnOutput,
    aws_lambda as _lambda,
    aws_iam as _iam,
    aws_logs as _logs,
    aws_apigateway as _apigw,
    aws_dynamodb as _dynamodb,
    aws_stepfunctions as _stepfunctions,
    aws_stepfunctions_tasks as _stepfunctions_tasks,
    Duration, RemovalPolicy
)
from constructs import Construct


class ServerlessApplicationStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create resources
        dynamo_db_table = self.create_dynamodb_table()
        lambda_role = self.create_lambda_role(dynamo_db_table)
        log_group = self.create_log_group(construct_id)
        lambda_function = self.create_lambda_function(construct_id, lambda_role, dynamo_db_table, log_group)
        apigw = self.create_api_gateway(construct_id, lambda_function)

        stepfunction = self.create_step_function(lambda_function)

        # Outputs
        self.create_outputs(lambda_function, lambda_role, log_group, dynamo_db_table, apigw, stepfunction)

    def create_dynamodb_table(self):
        return _dynamodb.Table(
            self, "DynamoDbTable",
            table_name="SampleTable",
            partition_key=_dynamodb.Attribute(
                name="id",
                type=_dynamodb.AttributeType.STRING
            ),
            billing_mode=_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

    def create_lambda_role(self, dynamo_db_table):
        lambda_role = _iam.Role(
            self, "LambdaRole",
            role_name="ServerlessApplication-lambda-role",
            description="Role for Lambda to access services",
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
        return lambda_role

    def create_step_function_role(self, lambda_function):
        step_function_role = _iam.Role(
            self, "StepFunctionRole",
            role_name="ServerlessApplication-stepfunction-role",
            description="Role for Step Function to invoke specific Lambda function",
            assumed_by=_iam.ServicePrincipal("states.amazonaws.com")
        )

        step_function_role.add_to_policy(
            _iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[lambda_function.function_arn]
            )
        )

        return step_function_role

    def create_log_group(self, construct_id):
        return _logs.LogGroup(
            self, "LambdaLogGroup",
            log_group_name=f"{construct_id}-log-group",
            retention=_logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY
        )

    def create_lambda_function(self, construct_id, lambda_role, dynamo_db_table, log_group):
        return _lambda.Function(
            self, "LambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="main.handler",
            function_name=f"{construct_id}-lambda",
            description=f"Lambda function for {construct_id}",
            code=_lambda.Code.from_asset("serverless_application/src"),
            timeout=Duration.seconds(900),
            memory_size=128,
            role=lambda_role,
            environment={
                "TABLE_NAME": dynamo_db_table.table_name
            },
            log_group=log_group
        )

    def create_api_gateway(self, construct_id, lambda_function):
        apigw = _apigw.RestApi(
            self, "ApiGw",
            rest_api_name=f"{construct_id}-api",
            description="API Gateway for Serverless Application",
            deploy_options=_apigw.StageOptions(
                stage_name="dev",
                tracing_enabled=False,
                logging_level=_apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
                metrics_enabled=False,
                variables={
                    'removeTestInvokeStage': 'true'
                }
            ),
            cloud_watch_role=True,
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_origins=["*"],
                allow_methods=["GET", "POST", "PUT", "DELETE"],
                allow_headers=["*"]
            )
        )
        users = apigw.root.add_resource("users")
        user = apigw.root.add_resource("user")
        user_id = user.add_resource("{user_id}")

        lambda_integration = _apigw.LambdaIntegration(
            lambda_function,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )
        users.add_method("GET", lambda_integration)
        user_id.add_method("GET", lambda_integration)
        user.add_method("POST", lambda_integration)

        apigw.node.add_dependency(lambda_function)
        return apigw

    def create_step_function(self, lambda_function):
        # Step Function definition
        sfn_role = self.create_step_function_role(lambda_function)
        tasks = _stepfunctions.Map(
            self, "ParallelProcessRequests",
            items_path="$.requests",
            result_path="$.results",
            max_concurrency=100
        ).iterator(
            _stepfunctions_tasks.LambdaInvoke(
                self, "ProcessRequest",
                lambda_function=lambda_function,
                result_path="$.result",
                output_path="$.result",
            )
        )
        step_function = _stepfunctions.StateMachine(
            self, "StepFunction",
            state_machine_name="ServerlessApplicationStepFunction",
            definition=tasks,
            role=sfn_role,
            timeout=Duration.minutes(5)
        )

        return step_function

    def create_outputs(self, lambda_function, lambda_role, log_group, dynamo_db_table, apigw, stepfunction):
        CfnOutput(self, "LambdaFunctionName", value=lambda_function.function_name)
        CfnOutput(self, "LambdaFunctionArn", value=lambda_function.function_arn)
        CfnOutput(self, "LambdaFunctionRoleArn", value=lambda_role.role_arn)
        CfnOutput(self, "LambdaFunctionRoleName", value=lambda_role.role_name)
        CfnOutput(self, "LambdaFunctionLogGroupName", value=log_group.log_group_name)
        CfnOutput(self, "LambdaFunctionLogGroupArn", value=log_group.log_group_arn)
        CfnOutput(self, "DynamoDbTableName", value=dynamo_db_table.table_name)
        CfnOutput(self, "DynamoDbTableArn", value=dynamo_db_table.table_arn)
        CfnOutput(self, "ApiGatewayUrl", value=apigw.url)
