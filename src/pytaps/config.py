# pytaps/email_utils.py

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List

def send_email_with_attachments(
    sender_email: str,
    receiver_emails: List[str],
    subject: str,
    body: str,
    password: str,
    smtp_server: str,
    smtp_port: int,
    attachment_paths: List[str] = None,
    is_html: bool = False
) -> bool:
    """
    Sends an email to multiple recipients with optional file attachments.

    Args:
        sender_email (str): The sender's email address.
        receiver_emails (List[str]): A list of recipient email addresses.
        subject (str): The subject line of the email.
        body (str): The main content of the email.
        password (str): The sender's email password.
        smtp_server (str): The SMTP server address (e.g., "smtp.gmail.com").
        smtp_port (int): The SMTP server port (e.g., 587 for TLS).
        attachment_paths (List[str], optional): A list of full file paths to attach.
                                                 Defaults to None (no attachments).
        is_html (bool, optional): Set to True if the body content is HTML. Defaults to False (plain text).

    Returns:
        bool: True if all emails were sent successfully, False otherwise.
              Note: If sending to multiple recipients, it attempts to send to all,
              and returns False if any single send fails.
    """
    if attachment_paths is None:
        attachment_paths = []

    all_succeeded = True

    for receiver_email in receiver_emails:
        try:
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "html" if is_html else "plain"))

            for attachment_file_path in attachment_paths:
                if not os.path.exists(attachment_file_path):
                    print(f"Warning: Attachment file not found at '{attachment_file_path}'. Skipping this attachment for {receiver_email}.")
                    continue # Skip this attachment, but try to send the email
                try:
                    with open(attachment_file_path, 'rb') as f:
                        attachment = MIMEApplication(f.read())
                        filename = os.path.basename(attachment_file_path)
                        attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                        message.attach(attachment)
                except Exception as attach_e:
                    print(f"Error attaching file '{attachment_file_path}' for {receiver_email}: {attach_e}")
                    # Decide if you want to fail the whole email send or just skip this attachment
                    # For now, we'll skip the attachment and try to send the rest of the email
                    continue

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Secure the connection
            server.login(sender_email, password)
            text = message.as_string()
            server.sendmail(sender_email, receiver_email, text)
            server.quit()
            print(f"Email sent successfully to {receiver_email}!")
        except Exception as e:
            print(f"An error occurred while sending email to {receiver_email}: {e}")
            all_succeeded = False # Mark as failed if any recipient fails

    return all_succeeded

# Example of how to use it (for testing/demonstration)
if __name__ == '__main__':
    # This part would typically be in your main script, not the library itself
    # For demonstration, replace with your actual details and a dummy file
    DUMMY_SENDER = "your_email@example.com"
    DUMMY_RECEIVERS = ["recipient1@example.com", "recipient2@example.com"]
    DUMMY_PASSWORD = "your_app_password_or_email_password" # Use app passwords for Gmail/Outlook
    DUMMY_SMTP_SERVER = "smtp.example.com" # e.g., "smtp.gmail.com"
    DUMMY_SMTP_PORT = 587

    # Create a dummy file for attachment
    dummy_file_name = "test_attachment.txt"
    with open(dummy_file_name, "w") as f:
        f.write("This is a test attachment from pytaps!")

    print("\n--- Attempting to send a test email ---")
    success = send_email_with_attachments(
        sender_email=DUMMY_SENDER,
        receiver_emails=DUMMY_RECEIVERS,
        subject="Test Email from pytaps",
        body="Hello,\nThis is a test email sent using pytaps.email_utils.send_email_with_attachments.\n\nRegards,\nYour Script",
        password=DUMMY_PASSWORD,
        smtp_server=DUMMY_SMTP_SERVER,
        smtp_port=DUMMY_SMTP_PORT,
        attachment_paths=[dummy_file_name]
    )
    print(f"Email sending overall status: {success}")

    # Clean up dummy file
    if os.path.exists(dummy_file_name):
        os.remove(dummy_file_name)
