from aws_cdk import aws_lambda as _lambda, Stack
from constructs import Construct
from aws_cdk import Duration

class LambdaConstruct(Construct):
    def __init__(self, scope: Construct, id: str, dynamodb_tables: dict, iam_roles: dict):
        super().__init__(scope, id)
        account = Stack.of(self).account
        region = Stack.of(self).region

        # Lambda Layer for authentication dependencies with automatic bundling
        self.auth_layer = _lambda.LayerVersion(
            self, "AuthDependenciesLayer",
            code=_lambda.Code.from_asset(
                "lambda_layer",
                bundling={
                    "image": _lambda.Runtime.PYTHON_3_12.bundling_image,
                    "command": [
                        "bash", "-c",
                        "pip install -r requirements.txt -t /asset-output/python --platform manylinux2014_aarch64 --only-binary=:all: --python-version 3.12 --implementation cp && cp requirements.txt /asset-output/"
                    ],
                },
            ),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            compatible_architectures=[_lambda.Architecture.ARM_64],
            description="Authentication dependencies: bcrypt, PyJWT"
        )

        # CreateChallengeLambdaFunction
        self.create_challenge_lambda = _lambda.Function(
            self, "CreateChallengeLambdaFunction",
            function_name="CreateChallengeLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create_challenge.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["create_challenge_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # StartChallengeLambdaFunction
        self.start_challenge_lambda = _lambda.Function(
            self, "StartChallengeLambdaFunction",
            function_name="StartChallengeLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="start_challenge.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGE_SESSIONS_TABLE": dynamodb_tables["challenge_sessions_table"].table_name,
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["start_challenge_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # DeleteChallengeLambdaFunction
        self.delete_challenge_lambda = _lambda.Function(
            self, "DeleteChallengeLambdaFunction",
            function_name="DeleteChallengeLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="delete_challenge.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["delete_challenge_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # GetOwnerChallengeLambdaFunction
        self.get_owner_challenge_lambda = _lambda.Function(
            self, "GetOwnerChallengeLambdaFunction",
            function_name="GetOwnerChallengeLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_owner_challenge.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["get_owner_challenge_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # GetChallengeLambdaFunction
        self.get_challenge_lambda = _lambda.Function(
            self, "GetChallengeLambdaFunction",
            function_name="GetChallengeLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="get_challenge.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["get_challenge_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # ListOwnerChallengesLambdaFunction
        self.list_owner_challenges_lambda = _lambda.Function(
            self, "ListOwnerChallengesLambdaFunction",
            function_name="ListOwnerChallengesLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="list_owner_challenges.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["list_owner_challenges_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # ListUserSuccessfulChallengesLambdaFunction
        self.list_user_successful_challenges_lambda = _lambda.Function(
            self, "ListUserSuccessfulChallengesLambdaFunction",
            function_name="ListUserSuccessfulChallengesLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="list_user_successful_challenges.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGE_SESSIONS_TABLE": dynamodb_tables["challenge_sessions_table"].table_name
            },
            role=iam_roles["list_user_successful_challenges_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # ListChallengesLambdaFunction
        self.list_challenges_lambda = _lambda.Function(
            self, "ListChallengesLambdaFunction",
            function_name="ListChallengesLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="list_challenges.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["list_challenges_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # PollForResponsesLambdaFunction
        self.poll_for_responses_lambda = _lambda.Function(
            self, "PollForResponsesLambdaFunction",
            function_name="PollForResponsesLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="poll_for_responses.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "PROMPTS_TABLE": dynamodb_tables["prompts_table"].table_name
            },
            role=iam_roles["poll_for_responses_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # SendMessageToLlmSecurityPlatformQueueLambdaFunction
        self.send_message_to_queue_lambda = _lambda.Function(
            self, "SendMessageToQueueLambdaFunction",
            function_name="SendMessageToQueueLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="send_message_to_queue.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "SQS_QUEUE_URL": f"https://sqs.{region}.amazonaws.com/{account}/LLmSecurityPlatformMessageQueue",
                "PROMPTS_TABLE": dynamodb_tables["prompts_table"].table_name,
                "CHALLENGE_SESSIONS_TABLE": dynamodb_tables["challenge_sessions_table"].table_name
            },
            role=iam_roles["send_message_to_queue_lambda_role"],
            memory_size=256,
            timeout=Duration.seconds(30),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # UpdateChallengeLambdaFunction
        self.update_challenge_lambda = _lambda.Function(
            self, "UpdateChallengeLambdaFunction",
            function_name="UpdateChallengeLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="update_challenge.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "CHALLENGES_TABLE": dynamodb_tables["challenges_table"].table_name
            },
            role=iam_roles["update_challenge_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # RegisterLambdaFunction
        self.register_lambda = _lambda.Function(
            self, "RegisterLambdaFunction",
            function_name="RegisterLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="register.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "USERS_TABLE": dynamodb_tables["users_table"].table_name
            },
            role=iam_roles["register_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )

        # LoginLambdaFunction
        self.login_lambda = _lambda.Function(
            self, "LoginLambdaFunction",
            function_name="LoginLambdaFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="login.lambda_handler",
            code=_lambda.Code.from_asset("lambda_handlers"),
            environment={
                "USERS_TABLE": dynamodb_tables["users_table"].table_name
            },
            role=iam_roles["login_lambda_role"],
            memory_size=128,
            timeout=Duration.seconds(15),
            architecture=_lambda.Architecture.ARM_64,
            layers=[self.auth_layer]
        )
