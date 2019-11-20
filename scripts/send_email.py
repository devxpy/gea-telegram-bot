import base64
import os.path
import pickle
import sys
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from pathlib import Path

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

BASE_DIR = Path(__file__).parent.parent
CREDENTIALS = BASE_DIR / 'credentials.json'
TOKEN_CACHE = BASE_DIR / 'token.pickle'


def send_message(body: str, *, to: str, using_resource):
    return (
        using_resource.users()
        .messages()
        .send(
            userId='me',
            body=create_message('devxpy@gmail.com', to, 'Appointment update', body),
        )
        .execute()
    )


def get_resource():
    """
    Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_CACHE):
        with open(TOKEN_CACHE, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_CACHE, 'wb') as token:
            pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def create_message(sender, to, subject, message_text):
    """
    Create a message for an email.

    Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.

    Returns:
        An object containing a base64url encoded email object.
  """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


if __name__ == '__main__':
    resource = get_resource()
    print(resource)
    print(sys.argv)
    msg = send_message(sys.argv[2], to=sys.argv[1], using_resource=resource)
    print(msg)
