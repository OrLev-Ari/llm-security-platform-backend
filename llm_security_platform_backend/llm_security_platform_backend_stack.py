
from aws_cdk import Stack
from constructs import Construct
from .constructs.iam_construct import IAMConstruct
from .constructs.dynamodb_construct import DynamoDBConstruct
from .constructs.lambda_construct import LambdaConstruct
from .constructs.apigateway_construct import ApiGatewayConstruct
from .constructs.sqs_construct import SqsConstruct


class LlmSecurityPlatformBackendStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Instantiate modular constructs
        iam_construct = IAMConstruct(self, "IAMConstruct")
        dynamodb_construct = DynamoDBConstruct(self, "DynamoDBConstruct")

        # SQS
        sqs_construct = SqsConstruct(self, "SqsConstruct")

        # Pass references to Lambda construct
        lambda_construct = LambdaConstruct(
            self,
            "LambdaConstruct",
            dynamodb_tables={
                "challenge_sessions_table": dynamodb_construct.challenge_sessions_table,
                "prompts_table": dynamodb_construct.prompts_table,
                "challenges_table": dynamodb_construct.challenges_table,
                "users_table": dynamodb_construct.users_table
            },
            iam_roles={
                "create_challenge_lambda_role": iam_construct.create_challenge_lambda_role,
                "start_challenge_lambda_role": iam_construct.start_challenge_lambda_role,
                "delete_challenge_lambda_role": iam_construct.delete_challenge_lambda_role,
                "get_owner_challenge_lambda_role": iam_construct.get_owner_challenge_lambda_role,
                "get_challenge_lambda_role": iam_construct.get_challenge_lambda_role,
                "list_owner_challenges_lambda_role": iam_construct.list_owner_challenges_lambda_role,
                "list_user_successful_challenges_lambda_role": iam_construct.list_user_successful_challenges_lambda_role,
                "list_challenges_lambda_role": iam_construct.list_challenges_lambda_role,
                "poll_for_responses_lambda_role": iam_construct.poll_for_responses_lambda_role,
                "send_message_to_queue_lambda_role": iam_construct.send_message_to_queue_lambda_role,
                "update_challenge_lambda_role": iam_construct.update_challenge_lambda_role,
                "register_lambda_role": iam_construct.register_lambda_role,
                "login_lambda_role": iam_construct.login_lambda_role
            }
        )

        # Pass all Lambda functions to API Gateway construct
        apigateway_construct = ApiGatewayConstruct(
            self,
            "ApiGatewayConstruct",
            lambda_functions={
                "create_challenge_lambda": lambda_construct.create_challenge_lambda,
                "start_challenge_lambda": lambda_construct.start_challenge_lambda,
                "delete_challenge_lambda": lambda_construct.delete_challenge_lambda,
                "get_owner_challenge_lambda": lambda_construct.get_owner_challenge_lambda,
                "get_challenge_lambda": lambda_construct.get_challenge_lambda,
                "list_owner_challenges_lambda": lambda_construct.list_owner_challenges_lambda,
                "list_user_successful_challenges_lambda": lambda_construct.list_user_successful_challenges_lambda,
                "list_challenges_lambda": lambda_construct.list_challenges_lambda,
                "poll_for_responses_lambda": lambda_construct.poll_for_responses_lambda,
                "send_message_to_queue_lambda": lambda_construct.send_message_to_queue_lambda,
                "update_challenge_lambda": lambda_construct.update_challenge_lambda,
                "register_lambda": lambda_construct.register_lambda,
                "login_lambda": lambda_construct.login_lambda
            }
        )
