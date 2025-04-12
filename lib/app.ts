#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { ServiceStack } from "./stacks/service";

const app = new cdk.App();

new ServiceStack(app, "SmartMailBuddy-Service", {
  stackName: "smart-mail-buddy",
  description: "Smart Mail Buddy application for processing emails",
  env: {
    account: process.env.AWS_ACCOUNT,
    region: process.env.AWS_REGION,
  },
});
