import boto3
import os
import json
import datetime
import uuid
from email.parser import BytesParser
from email.policy import default

s3_client = boto3.client("s3")
workmail_client = boto3.client("workmail")


def handler(event, context):
    """Process WorkMail email event, extract attachments and store in S3"""
    print("Received WorkMail event:", json.dumps(event))

    # Get environment variables
    bucket_name = os.environ["ATTACHMENT_BUCKET"]

    # Get message details from WorkMail event
    message_id = event["messageId"]
    organization_id = event["organizationId"]

    # Get raw message content from WorkMail
    raw_msg = workmail_client.get_raw_message_content(
        messageId=message_id, organizationId=organization_id
    )

    # Parse the raw email
    parsed_email = BytesParser(policy=default).parse(raw_msg["messageContent"])

    sender = parsed_email["From"]
    recipients = parsed_email["To"]
    subject = parsed_email["Subject"] or "No Subject"
    date_received = parsed_email["Date"]

    print(f"Processing email from {sender} with subject: {subject}")

    # Process attachments
    attachment_count = 0
    attachments_info = []

    for part in parsed_email.walk():
        content_disposition = part.get("Content-Disposition", "")

        # Check if this part is an attachment
        if "attachment" in content_disposition:
            attachment_count += 1
            filename = part.get_filename()

            # Generate a unique filename if none is present
            if not filename:
                extension = ".bin"
                if part.get_content_type() == "text/plain":
                    extension = ".txt"
                elif part.get_content_type() == "application/pdf":
                    extension = ".pdf"
                filename = f"attachment-{uuid.uuid4()}{extension}"

            content_type = part.get_content_type()
            payload = part.get_payload(decode=True)

            # Create a folder structure based on sender and date
            sender_formatted = format_path_friendly(sender)
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            key = f"{sender_formatted}/{today}/{message_id}/{filename}"

            # Upload attachment to S3
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=payload,
                ContentType=content_type,
                Metadata={
                    "sender": sender,
                    "subject": subject,
                    "date": date_received,
                    "message_id": message_id,
                },
            )

            print(f"Saved attachment: {key}")
            attachments_info.append(
                {
                    "filename": filename,
                    "s3_key": key,
                    "content_type": content_type,
                    "size_bytes": len(payload),
                }
            )

    print(f"Processed {attachment_count} attachments from email {message_id}")

    # Return result to WorkMail
    return {
        "actions": [
            {
                "action": {
                    "type": "DEFAULT"  # Continue with default email delivery
                },
                "allRecipients": True,
            }
        ]
    }


def format_path_friendly(text):
    """Convert text to a format suitable for S3 paths"""
    if "<" in text:
        # Extract name from format: "Name <email@example.com>"
        name = text.split("<")[0].strip()
        if name:
            text = name

    # Replace special characters
    import re

    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text.lower()
