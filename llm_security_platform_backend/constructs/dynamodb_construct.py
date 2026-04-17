from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

class DynamoDBConstruct(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # ChallengeSessionsTable
        self.challenge_sessions_table = dynamodb.Table(
            self, "ChallengeSessionsTable",
            partition_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="ChallengeSessionsTable"
        )
        self.challenge_sessions_table.add_global_secondary_index(
            index_name="UserIdIndex",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="started_at", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL
        )

        # PromptsTable
        self.prompts_table = dynamodb.Table(
            self, "PromptsTable",
            partition_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="PromptsTable"
        )

        # ChallengesTable
        self.challenges_table = dynamodb.Table(
            self, "ChallengesTable",
            partition_key=dynamodb.Attribute(name="challenge_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="ChallengesTable"
        )

        # UsersTable
        # Note: Admin users must be created manually via DynamoDB console
        # Set is_admin=True for admin accounts during manual insertion
        self.users_table = dynamodb.Table(
            self, "UsersTable",
            partition_key=dynamodb.Attribute(name="username", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name="UsersTable"
        )
