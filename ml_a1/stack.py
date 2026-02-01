from __future__ import annotations

from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_sns as sns,
)

class MlA1ScheduledBatchInferenceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 (input)
        self.input_bucket = s3.Bucket(
            self,
            "InputBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,  
        )

        # S3 (output)
        self.output_bucket = s3.Bucket(
            self,
            "OutputBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        
        # SNS for failures
        self.failure_topic = sns.Topic(
            self,
            "FailureAlertsTopic",
            display_name="ML-A1 Batch Inference Failure Alerts",
        )

        # Step Functions workflow
        # EventBridge Scheduler trigger
        # CloudWatch logs + alarms
        # SageMaker model + batch transform integration
        pass
