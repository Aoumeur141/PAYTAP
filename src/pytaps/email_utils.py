# pytaps/email_utils.py
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging
from typing import List, Union, Optional

logger = logging.getLogger(__name__) # Module-level logger

def send_email(
    sender_email: str,
    receiver_emails: Union[str, List[str]],
    subject: str,
    body: str,
    password: str,
    smtp_server: str,
    smtp_port: int,
    attachments: Optional[List[Union[str, os.PathLike]]] = None,
    logger_instance: Optional[logging.Logger] = None
) -> bool:
    current_logger = logger_instance if logger_instance is not None else logger

    if isinstance(receiver_emails, str):
        receiver_emails_list = [receiver_emails]
    else:
        receiver_emails_list = receiver_emails

    current_logger.info(f"Attempting to send email from '{sender_email}' to {receiver_emails_list} with subject: '{subject}'")
    current_logger.debug(f"Attachments list received by send_email: {attachments}") # ADD THIS LINE

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            current_logger.debug("Successfully logged into SMTP server.")

            for receiver_email in receiver_emails_list:
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = receiver_email
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain"))

                if attachments:
                    current_logger.debug(f"Found {len(attachments)} attachments to process.") # ADD THIS LINE
                    for attachment_file in attachments:
                        attachment_path = os.fspath(attachment_file) # Ensure path is string for open()
                        current_logger.debug(f"Processing attachment: '{attachment_path}'") # ADD THIS LINE
                        if not os.path.exists(attachment_path):
                            current_logger.warning(f"Attachment file NOT FOUND at '{attachment_path}'. Skipping this attachment.") # Ensure this warning is clear
                            continue
                        current_logger.debug(f"Attachment file found at '{attachment_path}'. Attempting to open and attach.") # ADD THIS LINE
                        try:
                            with open(attachment_path, 'rb') as f:
                                attachment = MIMEApplication(f.read())
                                filename = os.path.basename(attachment_path)
                                attachment.add_header('Content-Disposition', 'attachment', filename=filename)
                                message.attach(attachment)
                            current_logger.debug(f"Successfully attached file: '{filename}'") # This is the original debug log
                        except Exception as attach_e:
                            current_logger.error(f"Failed to open or attach file '{attachment_path}': {attach_e}", exc_info=True)
                            # For critical errors during attachment, you might choose to raise or return False
                            # For now, we log and continue to try sending the email without this specific attachment.
                else: # ADD THIS ELSE BLOCK
                    current_logger.debug("No attachments provided or attachments list was empty.")

                text = message.as_string()
                server.sendmail(sender_email, receiver_email, text)
                current_logger.info(f"Email successfully sent to '{receiver_email}'.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        current_logger.critical(f"SMTP authentication failed: Invalid username or password for '{sender_email}'. Error: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        current_logger.critical(f"SMTP connection failed: Could not connect to '{smtp_server}:{smtp_port}'. Error: {e}")
        return False
    except smtplib.SMTPException as e:
        current_logger.critical(f"An SMTP error occurred while sending email: {e}", exc_info=True)
        return False
    except Exception as e:
        current_logger.critical(f"An unexpected error occurred while sending the email: {e}", exc_info=True)
        return False
