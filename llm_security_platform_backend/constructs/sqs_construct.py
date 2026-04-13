from aws_cdk import Duration, aws_sqs as sqs
from constructs import Construct
from aws_cdk import Duration

class SqsConstruct(Construct):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # SQS Queue
        self.queue = sqs.Queue(
            self, "LLmSecurityPlatformMessageQueue",
            queue_name="LLmSecurityPlatformMessageQueue",
            visibility_timeout=Duration.seconds(30),
            retention_period=Duration.days(4),
            receive_message_wait_time=Duration.seconds(20),
            delivery_delay=Duration.seconds(0),
            max_message_size_bytes=1048576
        )
