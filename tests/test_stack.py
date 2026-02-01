import aws_cdk as cdk
from aws_cdk.assertions import Template

from ml_a1.stack import MlA1ScheduledBatchInferenceStack


def test_stack_creates_core_resources():
    app = cdk.App()
    stack = MlA1ScheduledBatchInferenceStack(app, "TestStack")

    template = Template.from_stack(stack)

    # S3: input + output buckets
    template.resource_count_is("AWS::S3::Bucket", 2)

    # SNS: failure topic
    template.resource_count_is("AWS::SNS::Topic", 1)

    # Step Functions: state machine
    template.resource_count_is("AWS::StepFunctions::StateMachine", 1)

    # EventBridge Scheduler: schedule
    template.resource_count_is("AWS::Scheduler::Schedule", 1)

    # CloudWatch: alarm
    template.resource_count_is("AWS::CloudWatch::Alarm", 1)

    # SageMaker: model
    template.resource_count_is("AWS::SageMaker::Model", 1)
