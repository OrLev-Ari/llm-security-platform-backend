#!/usr/bin/env python3
import os

import aws_cdk as cdk

from llm_security_platform_backend.llm_security_platform_backend_stack import LlmSecurityPlatformBackendStack


app = cdk.App()
LlmSecurityPlatformBackendStack(app, "LlmSecurityPlatformBackendStack",
    env=cdk.Environment(
        account=os.environ.get('CDK_DEFAULT_ACCOUNT'),
        region=os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')
    ),
    )

app.synth()
