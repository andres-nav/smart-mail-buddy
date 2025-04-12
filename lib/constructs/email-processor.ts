import { Code, LayerVersion, Runtime, Function } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { execSync } from "child_process";
import * as path from "path";
import * as fs from "fs";

export interface EmailProcessorProps {
  readonly stackName: string;
}

export class EmailProcessor extends Construct {
  readonly emailProcessorLambda: Function;

  constructor(scope: Construct, id: string, props: EmailProcessorProps) {
    super(scope, id);

    this.emailProcessorLambda = new Function(this, "Lambda", {
      runtime: Runtime.PYTHON_3_10,
      handler: "main.handler",
      code: Code.fromAsset("lambda"),
      layers: [this.createDependenciesLayer(props.stackName, "lambda/index")],
    });
  }

  private createDependenciesLayer(
    projectName: string,
    functionName: string,
  ): LayerVersion {
    const requirementsFile = "lambda/requirements.txt";
    const outputDir = ".build/app"; // Temporary directory to store the dependencies

    // Install dependencies if SKIP_PIP is not set
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
            `pip install -r ${requirementsFile} -t ${path.join(outputDir, "python")}`,
            {
              stdio: "inherit",
            },
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
