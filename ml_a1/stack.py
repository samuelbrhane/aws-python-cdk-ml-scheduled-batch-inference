from __future__ import annotations

from constructs import Construct
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    Size,
    aws_s3 as s3,
    aws_sns as sns,
    aws_logs as logs,
    aws_stepfunctions as sfn,
    aws_iam as iam,
    aws_sagemaker as sagemaker,
    aws_ec2 as ec2,
    aws_stepfunctions_tasks as tasks,
    aws_scheduler as scheduler,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
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
        
        # IAM role used by SageMaker to read/write S3
        self.sagemaker_execution_role = iam.Role(
            self,
            "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )

        # Allow reading batch input + writing batch output
        self.input_bucket.grant_read(self.sagemaker_execution_role)
        self.output_bucket.grant_read_write(self.sagemaker_execution_role)
        
        # SageMaker Model
        model_data_url = self.input_bucket.s3_url_for_object("model/model.tar.gz")

        self.model = sagemaker.CfnModel(
            self,
            "BatchInferenceModel",
            execution_role_arn=self.sagemaker_execution_role.role_arn,
            primary_container=sagemaker.CfnModel.ContainerDefinitionProperty(
                image="public.ecr.aws/sagemaker/sagemaker-xgboost:1.7-1",
                model_data_url=model_data_url,
            ),
        )

        
        # Step Functions task: start a SageMaker Batch Transform job
        transform_task = tasks.SageMakerCreateTransformJob(
            self,
            "RunBatchTransform",
            transform_job_name=sfn.JsonPath.format(
                "ml-a1-{}",
                sfn.JsonPath.string_at("$$.Execution.Name"),
            ),
            model_name=self.model.ref,
            transform_input=tasks.TransformInput(
                transform_data_source=tasks.TransformDataSource(
                    s3_data_source=tasks.TransformS3DataSource(
                        s3_uri=f"s3://{self.input_bucket.bucket_name}/input/",
                        s3_data_type=tasks.S3DataType.S3_PREFIX,
                    )
                )
            ),
            transform_output=tasks.TransformOutput(
                s3_output_path=f"s3://{self.output_bucket.bucket_name}/output/",
                assemble_with=tasks.AssembleWith.LINE,
            ),
            transform_resources=tasks.TransformResources(
                instance_count=1,
                instance_type=ec2.InstanceType("ml.m5.large"),
            ),
            max_concurrent_transforms=1,
            max_payload=Size.mebibytes(6),
        )

        # If transform fails, publish to SNS
        notify_failure = tasks.SnsPublish(
            self,
            "NotifyFailure",
            topic=self.failure_topic,
            subject="ML-A1 Batch Inference Pipeline Failed",
            message=sfn.TaskInput.from_text(
                "ML-A1 batch inference pipeline failed. Check Step Functions logs for details."
            ),
        )

        # Catch failures from the transform task
        transform_task.add_catch(
            handler=notify_failure,
            errors=["States.ALL"],
            result_path="$.error",
        )

        definition = transform_task
        self.state_machine = sfn.StateMachine(
            self,
            "BatchInferenceStateMachine",
            definition=definition,
            timeout=Duration.minutes(30),
            logs=sfn.LogOptions(
                destination=self.sfn_log_group,
                level=sfn.LogLevel.ALL,
            ),
        )

        # CloudWatch Alarm: notify on any failed execution
        self.failed_executions_alarm = cw.Alarm(
            self,
            "StateMachineFailedExecutionsAlarm",
            metric=self.state_machine.metric_failed(),
            threshold=1,
            evaluation_periods=1,
            datapoints_to_alarm=1,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
            alarm_description="Alarm when the ML-A1 batch inference Step Functions execution fails.",
        )

        self.failed_executions_alarm.add_alarm_action(
            cw_actions.SnsAction(self.failure_topic)
        )

        # EventBridge Scheduler
        self.scheduler_role = iam.Role(
            self,
            "SchedulerStartExecutionRole",
            assumed_by=iam.ServicePrincipal("scheduler.amazonaws.com"),
        )

        self.state_machine.grant_start_execution(self.scheduler_role)

        # EventBridge Scheduler (schedule -> Step Functions)
        self.schedule = scheduler.CfnSchedule(
            self,
            "BatchInferenceSchedule",
            schedule_expression="rate(1 day)", 
            flexible_time_window=scheduler.CfnSchedule.FlexibleTimeWindowProperty(
                mode="OFF"
            ),
            target=scheduler.CfnSchedule.TargetProperty(
                arn=self.state_machine.state_machine_arn,
                role_arn=self.scheduler_role.role_arn,
                input='{"source":"eventbridge-scheduler","pipeline":"ml-a1-batch"}',
            ),
        )

