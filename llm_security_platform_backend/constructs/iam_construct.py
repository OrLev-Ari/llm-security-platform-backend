from aws_cdk import aws_iam as iam
from constructs import Construct


class IAMConstruct(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # SSM Parameter Store policy for JWT secret access
        self.ssm_jwt_secret_policy = iam.PolicyStatement(
            actions=["ssm:GetParameter"],
            resources=["arn:aws:ssm:us-east-1:957592003036:parameter/llmplatformsecurity/jwtsecret"]
        )

        # EC2 Role with full SQS and DynamoDB permissions
        self.ec2_llm_platform_security_role = iam.Role(
            self, "EC2LLMPlatformSecurityRole",
            role_name="EC2LLMPlatformSecurityRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        self.ec2_llm_platform_security_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:*"],
            resources=[
                "arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable",
                "arn:aws:dynamodb:us-east-1:957592003036:table/PromptsTable",
                "arn:aws:dynamodb:us-east-1:957592003036:table/ChallengeSessionsTable"
            ]
        ))
        self.ec2_llm_platform_security_role.add_to_policy(iam.PolicyStatement(
            actions=["sqs:*"],
            resources=["arn:aws:sqs:us-east-1:957592003036:LLmSecurityPlatformMessageQueue"]
        ))

        # Lambda execution roles for each Lambda function
        self.create_challenge_lambda_role = iam.Role(
            self, "CreateChallengeLambdaRole",
            role_name="CreateChallengeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.create_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:PutItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.create_challenge_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.start_challenge_lambda_role = iam.Role(
            self, "StartChallengeLambdaRole",
            role_name="StartChallengeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.start_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:GetItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.start_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:PutItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengeSessionsTable"]
        ))
        self.start_challenge_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.delete_challenge_lambda_role = iam.Role(
            self, "DeleteChallengeLambdaRole",
            role_name="DeleteChallengeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.delete_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:DeleteItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.delete_challenge_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.get_owner_challenge_lambda_role = iam.Role(
            self, "GetOwnerChallengeLambdaRole",
            role_name="GetOwnerChallengeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.get_owner_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:GetItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.get_owner_challenge_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.get_challenge_lambda_role = iam.Role(
            self, "GetChallengeLambdaRole",
            role_name="GetChallengeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.get_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:GetItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.get_challenge_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.list_owner_challenges_lambda_role = iam.Role(
            self, "ListOwnerChallengesLambdaRole",
            role_name="ListOwnerChallengesLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.list_owner_challenges_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:Scan"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.list_owner_challenges_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.list_user_successful_challenges_lambda_role = iam.Role(
            self, "ListUserSuccessfulChallengesLambdaRole",
            role_name="ListUserSuccessfulChallengesLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.list_user_successful_challenges_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:Query"],
            resources=[
                "arn:aws:dynamodb:us-east-1:957592003036:table/ChallengeSessionsTable",
                "arn:aws:dynamodb:us-east-1:957592003036:table/ChallengeSessionsTable/index/UserIdIndex"
            ]
        ))
        self.list_user_successful_challenges_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.list_challenges_lambda_role = iam.Role(
            self, "ListChallengesLambdaRole",
            role_name="ListChallengesLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.list_challenges_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:Scan"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.list_challenges_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.poll_for_responses_lambda_role = iam.Role(
            self, "PollForResponsesLambdaRole",
            role_name="PollForResponsesLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.poll_for_responses_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:Query", "dynamodb:UpdateItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/PromptsTable"]
        ))
        self.poll_for_responses_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.send_message_to_queue_lambda_role = iam.Role(
            self, "SendMessageToQueueLambdaRole",
            role_name="SendMessageToQueueLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.send_message_to_queue_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:GetItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengeSessionsTable"]
        ))
        self.send_message_to_queue_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:PutItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/PromptsTable"]
        ))
        self.send_message_to_queue_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["sqs:SendMessage"],
            resources=["arn:aws:sqs:us-east-1:957592003036:LLmSecurityPlatformMessageQueue"]
        ))
        self.send_message_to_queue_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
        self.update_challenge_lambda_role = iam.Role(
            self, "UpdateChallengeLambdaRole",
            role_name="UpdateChallengeLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.update_challenge_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:UpdateItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/ChallengesTable"]
        ))
        self.update_challenge_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)

        # Register Lambda Role
        self.register_lambda_role = iam.Role(
            self, "RegisterLambdaRole",
            role_name="RegisterLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.register_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:PutItem", "dynamodb:GetItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/UsersTable"]
        ))
        self.register_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)

        # Login Lambda Role
        self.login_lambda_role = iam.Role(
            self, "LoginLambdaRole",
            role_name="LoginLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        self.login_lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["dynamodb:GetItem"],
            resources=["arn:aws:dynamodb:us-east-1:957592003036:table/UsersTable"]
        ))
        self.login_lambda_role.add_to_policy(self.ssm_jwt_secret_policy)
