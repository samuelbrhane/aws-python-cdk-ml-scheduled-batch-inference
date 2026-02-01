from __future__ import annotations
import aws_cdk as cdk

from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_sns as sns,
    aws_logs as logs,
    aws_stepfunctions as sfn,
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

        # CloudWatch Logs (Step Functions)
        self.sfn_log_group = logs.LogGroup(
            self,
            "StateMachineLogs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # Step Functions (orchestration)
        definition = sfn.Pass(self, "StartBatchPipeline")

        self.state_machine = sfn.StateMachine(
            self,
            "BatchInferenceStateMachine",
            definition=definition,
            timeout=cdk.Duration.minutes(30),
            logs=sfn.LogOptions(
                destination=self.sfn_log_group,
                level=sfn.LogLevel.ALL,
            ),
        )
        
        # EventBridge Scheduler trigger
        # CloudWatch logs + alarms
        # SageMaker model + batch transform integration
        pass
