# AWS Python CDK – Scheduled ML Batch Inference Pipeline

This repository contains a complete example of a scheduled batch inference pipeline on AWS, built using Infrastructure as Code (IaC) with AWS CDK (Python).

The pipeline runs a SageMaker Batch Transform job on a schedule, orchestrated by AWS Step Functions, triggered by Amazon EventBridge Scheduler, with input and output data stored in Amazon S3. Failures are captured through CloudWatch Logs, CloudWatch Alarms, and SNS notifications.

---

## What this project does

- Runs batch machine learning inference on a fixed schedule
- Orchestrates the workflow using Step Functions
- Uses SageMaker Batch Transform for scalable batch inference
- Stores batch input and prediction output in S3
- Surfaces failures via CloudWatch and SNS
- Defines all infrastructure using AWS CDK (Python)

---

## Why batch inference

Batch inference is appropriate when:

- Predictions are generated periodically (daily, hourly, weekly)
- Low-latency responses are not required
- Large datasets must be processed efficiently
- Cost optimization is important

---

## Architecture overview

Execution flow:

1. EventBridge Scheduler triggers the pipeline on a schedule
2. Step Functions starts the batch inference workflow
3. SageMaker Batch Transform reads input data from S3
4. Predictions are written back to S3
5. Failures are logged and generate alerts through SNS

---

## AWS services used

- AWS CDK (Python) – Infrastructure as Code
- Amazon S3 – Batch input and output storage
- AWS Step Functions – Workflow orchestration
- Amazon SageMaker – Model definition and Batch Transform
- Amazon EventBridge Scheduler – Scheduled execution
- Amazon CloudWatch – Logs and alarms
- Amazon SNS – Failure notifications

---

## Repository structure

.
├── app.py
├── cdk.json
├── requirements.txt
├── ml_a1/
│ └── stack.py
├── tests/
│ └── test_stack.py
├── diagrams/
│ └── ml-a1.drawio.xml
└── README.md

---

## Using this repository

This project can be reviewed, synthesized, and tested without an AWS account.

Create and activate a virtual environment:

python -m venv .venv
.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Synthesize the infrastructure:

npx aws-cdk@2.160.0 synth

Run tests:

pytest -q

---

## Deployment (optional)

Deployment is not required to understand or evaluate this project.

If you choose to deploy it, the following prerequisites apply.

Prerequisites:

- An AWS account
- AWS credentials configured locally
- CDK bootstrap executed once per account and region

npx aws-cdk@2.160.0 bootstrap

---

## Important deployment requirements

This project intentionally uses placeholder values for the SageMaker model so that it can be synthesized safely without deployment.

To successfully deploy and run the batch inference job, you must:

1. Upload a valid model artifact to:

s3://<input-bucket>/model/model.tar.gz

2. Ensure the container image is valid and available in your AWS region.

The repository uses the following placeholder image by default:

public.ecr.aws/sagemaker/sagemaker-xgboost:1.7-1

If these requirements are not met, the stack may deploy but the Batch Transform job will fail at runtime.

---

## Design notes

- Batch inference is used instead of real-time inference to optimize cost and scalability.
- Step Functions provides clear orchestration and failure handling.
- SNS and CloudWatch ensure failures are observable.
- S3 buckets use destroy-on-delete settings for demo purposes only.
