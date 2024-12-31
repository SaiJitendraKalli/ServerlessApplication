#!/usr/bin/env python3
import os

import aws_cdk as cdk

from serverless_application.serverless_application_stack import ServerlessApplicationStack

app = cdk.App()
ServerlessApplicationStack(app, "ServerlessApplication",
                           stack_name="ServerlessApplicationStack",
                           description="Serverless Application Stack")

app.synth()
