from aws_cdk import aws_apigateway as apigateway
from constructs import Construct


class ApiGatewayConstruct(Construct):
    def __init__(self, scope: Construct, id: str, lambda_functions: dict):
        super().__init__(scope, id)


        self.api = apigateway.RestApi(
            self, "LLmSecurityPlatformApiGW",
            rest_api_name="LLmSecurityPlatformApiGW",
            deploy_options=apigateway.StageOptions(stage_name="prod")
        )



        # /admin
        admin_resource = self.api.root.add_resource("admin")

        # /admin/challenges
        admin_challenges_resource = admin_resource.add_resource("challenges")
        admin_challenges_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_owner_challenges_lambda"])
        )
        admin_challenges_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["create_challenge_lambda"])
        )

        # /admin/challenges/{challenge_id}
        admin_challenge_id_resource = admin_challenges_resource.add_resource("{challenge_id}")
        admin_challenge_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_owner_challenge_lambda"])
        )
        admin_challenge_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(lambda_functions["delete_challenge_lambda"])
        )
        admin_challenge_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(lambda_functions["update_challenge_lambda"])
        )

        # /challenges
        challenges_resource = self.api.root.add_resource("challenges")
        challenges_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_challenges_lambda"])
        )

        # /challenges/completedchallenges
        completed_challenges_resource = challenges_resource.add_resource("completedchallenges")
        completed_challenges_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_user_successful_challenges_lambda"])
        )

        # /challenges/{challenge_id}
        challenge_id_resource = challenges_resource.add_resource("{challenge_id}")
        challenge_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_challenge_lambda"])
        )

        # /challenges/{challenge_id}/start
        challenge_id_resource.add_resource("start").add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["start_challenge_lambda"])
        )

        # /sessions
        sessions_resource = self.api.root.add_resource("sessions")
        # /sessions/{session_id}
        session_id_resource = sessions_resource.add_resource("{session_id}")
        session_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["poll_for_responses_lambda"])
        )
        # /sessions/{session_id}/messages
        session_id_resource.add_resource("messages").add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["send_message_to_queue_lambda"])
        )
