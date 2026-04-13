#!/usr/bin/env python3
import os

import aws_cdk as cdk

from llm_security_platform_backend.llm_security_platform_backend_stack import LlmSecurityPlatformBackendStack


app = cdk.App()
LlmSecurityPlatformBackendStack(app, "LlmSecurityPlatformBackendStack",
    env=cdk.Environment(account='957592003036', region='us-east-1'),
    )

app.synth()
