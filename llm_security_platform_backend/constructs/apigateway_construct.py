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

        # /auth
        auth_resource = self.api.root.add_resource("auth")
        
        # /auth/register
        auth_resource.add_resource("register").add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["register_lambda"])
        )
        
        # /auth/login
        auth_resource.add_resource("login").add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["login_lambda"])
        )



        # /admin
        admin_resource = self.api.root.add_resource("admin")

        # /admin/challenges
        admin_challenges_resource = admin_resource.add_resource("challenges")
        admin_challenges_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_owner_challenges_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )
        admin_challenges_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["create_challenge_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /admin/challenges/{challenge_id}
        admin_challenge_id_resource = admin_challenges_resource.add_resource("{challenge_id}")
        admin_challenge_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_owner_challenge_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )
        admin_challenge_id_resource.add_method(
            "DELETE",
            apigateway.LambdaIntegration(lambda_functions["delete_challenge_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )
        admin_challenge_id_resource.add_method(
            "PUT",
            apigateway.LambdaIntegration(lambda_functions["update_challenge_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /admin/challenges/completedsessions
        admin_completed_sessions_resource = admin_challenges_resource.add_resource("completedsessions")
        
        # /admin/challenges/completedsessions/{challenge_id}
        admin_completed_sessions_challenge_resource = admin_completed_sessions_resource.add_resource("{challenge_id}")
        admin_completed_sessions_challenge_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_completed_sessions_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE,
            request_parameters={
                "method.request.querystring.limit": False
            }
        )
        
        # /admin/challenges/completedsessions/{challenge_id}/{session_id}
        admin_completed_sessions_session_resource = admin_completed_sessions_challenge_resource.add_resource("{session_id}")
        admin_completed_sessions_session_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_session_chat_history_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /challenges
        challenges_resource = self.api.root.add_resource("challenges")
        challenges_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_challenges_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /challenges/completedchallenges
        completed_challenges_resource = challenges_resource.add_resource("completedchallenges")
        completed_challenges_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["list_user_successful_challenges_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /challenges/{challenge_id}
        challenge_id_resource = challenges_resource.add_resource("{challenge_id}")
        challenge_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_challenge_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /challenges/{challenge_id}/start
        challenge_id_resource.add_resource("start").add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["start_challenge_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /sessions
        sessions_resource = self.api.root.add_resource("sessions")
        # /sessions/{session_id}
        session_id_resource = sessions_resource.add_resource("{session_id}")
        session_id_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["poll_for_responses_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )
        # /sessions/{session_id}/messages
        session_id_resource.add_resource("messages").add_method(
            "POST",
            apigateway.LambdaIntegration(lambda_functions["send_message_to_queue_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE
        )

        # /leaderboards
        leaderboards_resource = self.api.root.add_resource("leaderboards")
        
        # /leaderboards/challenges
        leaderboards_challenges_resource = leaderboards_resource.add_resource("challenges")
        
        # /leaderboards/challenges/{id}
        leaderboards_challenges_resource.add_resource("{id}").add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_challenge_leaderboard_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE,
            request_parameters={
                "method.request.querystring.limit": False
            }
        )
        
        # /leaderboards/global
        leaderboards_resource.add_resource("global").add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_global_leaderboard_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE,
            request_parameters={
                "method.request.querystring.limit": False
            }
        )
        
        # /leaderboards/users
        leaderboards_users_resource = leaderboards_resource.add_resource("users")
        leaderboards_users_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(lambda_functions["get_user_scores_lambda"]),
            authorization_type=apigateway.AuthorizationType.NONE,
            request_parameters={
                "method.request.querystring.limit": False
            }
        )