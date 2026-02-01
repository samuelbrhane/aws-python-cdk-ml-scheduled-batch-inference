#!/usr/bin/env python3
import aws_cdk as cdk

from ml_a1.stack import MlA1ScheduledBatchInferenceStack

app = cdk.App()

MlA1ScheduledBatchInferenceStack(
    app,
    "MlA1ScheduledBatchInferenceStack",
)

app.synth()
