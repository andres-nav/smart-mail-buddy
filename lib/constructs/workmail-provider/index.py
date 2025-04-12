import boto3
import json
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

workmail_client = boto3.client("workmail")


def handler(event, _):
    logger.info("Received event: %s", json.dumps(event))

    request_type = event["RequestType"]
    properties = event.get("ResourceProperties", {})
    operation = properties.get("Operation")

    response_data = {}
    physical_id = event.get("PhysicalResourceId", f"workmail-{time.time()}")

    try:
        if request_type == "Create":
            if operation == "CreateOrganization":
                response_data = create_organization(properties)
                physical_id = response_data.get("OrganizationId")

            elif operation == "CreateUser":
                response_data = create_user(properties)
                physical_id = (
                    f"user-{properties.get('OrganizationId')}-{properties.get('Name')}"
                )

            elif operation == "CreateEmailFlowRule":
                response_data = create_email_flow_rule(properties)
                physical_id = (
                    f"rule-{properties.get('OrganizationId')}-{properties.get('Name')}"
                )

        elif request_type == "Update":
            # Handle updates for each resource type
            if operation == "CreateEmailFlowRule":
                response_data = update_email_flow_rule(properties)
            else:
                logger.info(f"Update operation not implemented for {operation}")

        elif request_type == "Delete":
            # Handle deletions
            if operation == "CreateOrganization":
                delete_organization(properties, physical_id)
            elif operation == "CreateEmailFlowRule":
                delete_email_flow_rule(properties)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "Status": "FAILED",
            "Reason": str(e),
            "PhysicalResourceId": physical_id,
            "Data": {},
        }

    return {
        "Status": "SUCCESS",
        "PhysicalResourceId": physical_id,
        "Data": response_data,
    }


def create_organization(properties):
    """Create a WorkMail organization"""
    org_name = properties.get("OrganizationName")
    domain_name = properties.get("DomainName")

    # Generate alias from organization name
    alias = org_name.lower().replace(" ", "-")

    # Create a unique directory ID
    directory_id = f"d-{int(time.time())}"

    # Create the organization
    response = workmail_client.create_organization(
        DirectoryId=directory_id,
        Alias=alias,
        Domains=[{"DomainName": domain_name}] if domain_name else [],
        EnableInteroperability=properties.get("EnableInteroperability", False),
    )

    org_id = response["OrganizationId"]
    logger.info(f"Created WorkMail organization: {org_id}")

    # Wait for organization to become active
    for _ in range(30):
        desc = workmail_client.describe_organization(OrganizationId=org_id)
        if desc["State"] == "ACTIVE":
            break
        logger.info(f"Waiting for organization {org_id} to become active...")
        time.sleep(10)

    return {"OrganizationId": org_id}


def create_user(properties):
    """Create a WorkMail user"""
    org_id = properties.get("OrganizationId")
    name = properties.get("Name")
    email = properties.get("Email")
    password = properties.get("Password")

    # Create user in WorkMail
    user_response = workmail_client.create_user(
        OrganizationId=org_id, Name=name, DisplayName=name, Password=password
    )

    user_id = user_response["UserId"]

    # Register user to WorkMail
    workmail_client.register_to_work_mail(
        OrganizationId=org_id, EntityId=user_id, Email=email
    )

    logger.info(f"Created WorkMail user: {email}")

    return {"UserId": user_id}


def create_email_flow_rule(properties):
    """Create an email flow rule to trigger Lambda"""
    org_id = properties.get("OrganizationId")
    rule_name = properties.get("Name")
    lambda_arn = properties.get("LambdaArn")
    sync_enabled = properties.get("SyncEnabled", True)

    # Create the rule
    workmail_client.create_email_flow_rule(
        OrganizationId=org_id,
        Name=rule_name,
        Enabled=properties.get("Enabled", True),
        Rule={
            "Actions": [
                {
                    "LambdaAction": {
                        "FunctionArn": lambda_arn,
                        "OrganizationArn": f"arn:aws:workmail:{boto3.session.Session().region_name}:{boto3.client('sts').get_caller_identity().get('Account')}:organization/{org_id}",
                    }
                }
            ],
            "Conditions": [],  # Apply to all emails
        },
        RunLambdaAsynchronously=not sync_enabled,
    )

    logger.info(f"Created email flow rule: {rule_name} for organization {org_id}")

    return {"RuleName": rule_name}


def update_email_flow_rule(properties):
    """Update an existing email flow rule"""
    # Implementation depends on WorkMail API capabilities
    # This is a placeholder for rule updates
    return create_email_flow_rule(properties)


def delete_organization(_, org_id):
    """Delete a WorkMail organization"""
    if not org_id.startswith("m-"):
        logger.info(f"Not deleting organization: Invalid ID format: {org_id}")
        return

    try:
        workmail_client.delete_organization(OrganizationId=org_id, DeleteDirectory=True)
        logger.info(f"Deleted WorkMail organization: {org_id}")
    except Exception as e:
        logger.error(f"Error deleting organization {org_id}: {str(e)}")


def delete_email_flow_rule(properties):
    """Delete an email flow rule"""
    org_id = properties.get("OrganizationId")
    rule_name = properties.get("Name")

    try:
        workmail_client.delete_email_flow_rule(OrganizationId=org_id, Name=rule_name)
        logger.info(f"Deleted email flow rule: {rule_name}")
    except Exception as e:
        logger.error(f"Error deleting email flow rule {rule_name}: {str(e)}")
