import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { EmailProcessor } from "../constructs/email-processor";

export class ServiceStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    new EmailProcessor(this, "EmailProcessor", {
stackName: this.stackName,
      organizationName: "EmailAttachmentProcessor",
      userName: "processor",
      userEmail: "processor@example.com",
      userPassword: "SecurePassword123!",  // Use AWS Secrets Manager in production
    });
  }
}
