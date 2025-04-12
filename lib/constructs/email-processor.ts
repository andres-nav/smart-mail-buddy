import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import {
  Code,
  LayerVersion,
  Runtime,
  Function,
  Architecture,
} from "aws-cdk-lib/aws-lambda";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as iam from "aws-cdk-lib/aws-iam";
import * as cr from "aws-cdk-lib/custom-resources";
import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

export interface WorkMailEmailProcessorProps {
  readonly stackName: string;
  readonly organizationName: string;
  readonly domainName?: string;
  readonly userEmail?: string;
  readonly userName?: string;
  readonly userPassword?: string;
}

export class EmailProcessor extends Construct {
  public readonly attachmentBucket: s3.Bucket;
  public readonly emailProcessorLambda: Function;
  public readonly organizationId: string;

  constructor(
    scope: Construct,
    id: string,
    props: WorkMailEmailProcessorProps,
  ) {
    super(scope, id);

    // Create S3 bucket for email attachments
    this.attachmentBucket = new s3.Bucket(this, "AttachmentBucket", {
      removalPolicy: cdk.RemovalPolicy.RETAIN,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(7),
        },
      ],
      encryption: s3.BucketEncryption.S3_MANAGED,
    });

    // Create Lambda function for processing emails
    this.emailProcessorLambda = new Function(this, "EmailProcessorLambda", {
      runtime: Runtime.PYTHON_3_10,
      handler: "email_processor.handler",
      code: Code.fromAsset("lambda"),
      layers: [
        this.createDependenciesLayer(props.stackName, "lambda/email-processor"),
      ],
      architecture: Architecture.ARM_64,
      environment: {
        ATTACHMENT_BUCKET: this.attachmentBucket.bucketName,
      },
      timeout: cdk.Duration.seconds(30),
    });

    // Grant Lambda permissions to S3 bucket
    this.attachmentBucket.grantReadWrite(this.emailProcessorLambda);

    // Create WorkMail provider for custom resources
    const workMailProvider = new cr.Provider(this, "WorkMailProvider", {
      onEventHandler: new Function(this, "WorkMailProviderFunction", {
        runtime: Runtime.PYTHON_3_10,
        handler: "index.handler",
        code: Code.fromAsset(path.join(__dirname, "workmail-provider")),
        timeout: cdk.Duration.minutes(5),
      }),
    });

    // Grant permissions to WorkMail provider
    workMailProvider.onEventHandler.addToRolePolicy(
      new iam.PolicyStatement({
        actions: [
          "workmail:CreateOrganization",
          "workmail:DeleteOrganization",
          "workmail:DescribeOrganization",
          "workmail:ListOrganizations",
          "workmail:CreateUser",
          "workmail:CreateGroup",
          "workmail:CreateResource",
          "workmail:CreateAlias",
          "workmail:RegisterToWorkMail",
          "workmail:PutMailboxPermissions",
          "workmail:CreateMailDomain",
          "workmail:TestAvailability",
          "workmail:CreateEmailFlowRule",
          "workmail:PutEmailFlowRuleAction",
          "route53:ListHostedZonesByName",
          "route53:GetHostedZone",
          "route53:ChangeResourceRecordSets",
          "route53:GetChange",
          "ses:VerifyDomainIdentity",
          "ses:VerifyDomainDkim",
        ],
        resources: ["*"],
      }),
    );

    // Create WorkMail organization
    const workMailOrg = new cdk.CustomResource(this, "WorkMailOrganization", {
      serviceToken: workMailProvider.serviceToken,
      properties: {
        Operation: "CreateOrganization",
        OrganizationName: props.organizationName,
        DomainName: props.domainName || undefined,
        EnableInteroperability: true,
      },
    });

    this.organizationId = workMailOrg.getAttString("OrganizationId");

    // Create WorkMail user if specified
    if (props.userName && props.userEmail && props.userPassword) {
      new cdk.CustomResource(this, "WorkMailUser", {
        serviceToken: workMailProvider.serviceToken,
        properties: {
          Operation: "CreateUser",
          OrganizationId: this.organizationId,
          Name: props.userName,
          Email: props.userEmail,
          Password: props.userPassword,
        },
      });
    }

    // Grant Lambda permission to access WorkMail
    this.emailProcessorLambda.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["workmail:GetRawMessageContent"],
        resources: [
          `arn:aws:workmail:${cdk.Stack.of(this).region}:${
            cdk.Stack.of(this).account
          }:organization/${this.organizationId}`,
        ],
      }),
    );

    // Create WorkMail email flow rule to trigger the Lambda
    new cdk.CustomResource(this, "WorkMailEmailFlowRule", {
      serviceToken: workMailProvider.serviceToken,
      properties: {
        Operation: "CreateEmailFlowRule",
        OrganizationId: this.organizationId,
        Name: "ProcessAttachments",
        Enabled: true,
        RuleType: "RUN_LAMBDA",
        LambdaArn: this.emailProcessorLambda.functionArn,
        SyncEnabled: true,
      },
    });
  }

  private createDependenciesLayer(
    projectName: string,
    functionName: string,
  ): LayerVersion {
    const requirementsFile = "lambda/requirements.txt";
    const outputDir = ".build/app";

    if (!process.env.SKIP_PIP) {
      try {
        // Create the output directory
        execSync(`mkdir -p ${path.join(outputDir, "python")}`, {
          stdio: "inherit",
        });

        // Check if requirements file exists
        if (!fs.existsSync(requirementsFile)) {
          console.warn(`Requirements file not found: ${requirementsFile}`);
        } else {
          // Install dependencies
          execSync(
            `pip install --no-cache-dir --no-deps -r ${requirementsFile} -t ${path.join(outputDir, "python")}`,
            {
              stdio: "inherit",
            },
          );

          // Remove unnecessary files after installation
          execSync(
            `find ${path.join(outputDir, "python")} -type d -name "tests" -exec rm -rf {} +`,
            { stdio: "inherit" },
          );
        }
      } catch (error) {
        console.error("Failed to set up dependencies:", error);
        throw error;
      }
    }

    const layerId = `${projectName}-${functionName}-dependencies`.replace(
      /[^a-zA-Z0-9-]/g,
      "-",
    ); // Sanitize ID for CloudFormation

    return new LayerVersion(this, layerId, {
      code: Code.fromAsset(outputDir),
      description: "Dependencies layer",
    });
  }
}
