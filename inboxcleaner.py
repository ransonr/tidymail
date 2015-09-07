import httplib2
import oauth2client
import os

from apiclient import discovery
from collections import defaultdict
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://mail.google.com'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail Inbox Cleaner'
UNCATEGORIZED_LABEL_ID = 'Label_37'  # REPLACE THIS WITH YOUR DESIRED LABEL ID!!!


class EmailLabelCounter:
    def __init__(self):
        self.label_count_dict = defaultdict(int)
        self.email_count = 0

    def add_labels(self, label_ids):
        for label_id in label_ids:
            if label_id.startswith('Label_'):
                self.label_count_dict[label_id] += 1

    def get_suggested_label(self):
        if len(self.label_count_dict) == 0:
            return UNCATEGORIZED_LABEL_ID
        else:
            return max(self.label_count_dict, key=self.label_count_dict.get)

class InboxCleaner:
    def __init__(self):
        self.mailbox = self.get_mailbox()

    def get_mailbox(self):
        """Gets valid user credentials from file"""
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
    
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)

        credential_path = os.path.join(credential_dir, 'gmail-quickstart.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME

            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatability with Python 2.6
                credentials = tools.run(flow, store)

            print 'Storing credentials to ' + credential_path

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)

        return service.users()

    def get_label_dict(self):
        """Return a list of all labels in the mailbox"""
        labels = self.mailbox.labels().list(userId='me').execute()
        labels = labels.get('labels', [])
        label_dict = {l['id']: l['name'] for l in labels}
        return label_dict

    def print_labels(self):
        """Prints all labels and their IDs"""
        labels = self.get_labels()
        for label in labels:
            print label['name'], label['id']

    def get_messages(self, labelId='INBOX', query=None, older_than_days=7):
        """Return a list of messages for the given labelId and query
        
        Note: The list contains msg IDs. If more information is wanted, you
        need to retrieve the specific message by ID.
        """
        query = ('' if query is None else query) +  ' older_than:{0}d'.format(older_than_days)
        msg_dict = self.mailbox.messages().list(userId='me', labelIds=labelId, q=query).execute()

        # msg_next_page_token = msg_dict.get('nextPageToken', '')
        # msg_count = msg_dict.get('resultSizeEstimate', 0)
        # print 'Retrieved {0} messages...'.format(msg_count)

        return msg_dict.get('messages', [])

    def get_message_by_id(self, msg_id):
        """Return a tuple of labelsIds, msg"""
        msg = self.mailbox.messages().get(
            userId='me',
            id=msg_id,
            format='metadata',
            metadataHeaders=['From']
        ).execute()
        return msg.get('labelIds', []), msg.get('payload', {})

    def assign_label_to_email(self, msg_id, label_id):
        self.mailbox.messages().modify(
            userId='me',
            id=msg_id,
            body={'addLabelIds': [label_id], 'removeLabelIds': ['INBOX']}
        ).execute()

    def get_clean_email_address(self, sender):
        return sender[sender.find('<')+1:sender.find('>')]

    def clean(self):
        """Goes through messages in inbox and moves them to the suggested label
        
        The suggested label is taken to be the label where the most messages from the
        sender exists. If there are no messages from the sender in any label, moves
        the message to UNCATEGORIZED_LABEL_ID
        """
        label_dict = self.get_label_dict()
        msgs = self.get_messages()

        for msg in msgs:
            msg_id = msg.get('id', 0)
            _, msg = self.get_message_by_id(msg_id)

            headers = msg.get('headers', {})[0]
            sender = headers.get('value', None)

            sender = self.get_clean_email_address(sender)
            sender_msgs = self.get_messages(labelId=None, query='from:{0} has:userlabels'.format(sender))

            label_counter = EmailLabelCounter()

            for sender_msg in sender_msgs:
                label_ids, sender_msg = self.get_message_by_id(sender_msg.get('id', 0))
                label_counter.add_labels(label_ids)

            suggested_label_id = label_counter.get_suggested_label()
            self.assign_label_to_email(msg_id, suggested_label_id)
            suggested_label = label_dict[suggested_label_id]
            print 'Moving message from {0} to label {1}'.format(sender, suggested_label)

        print 'Moved {0} messages, your mailbox is now clean'.format(len(msgs))


def main():
    inbox_cleaner = InboxCleaner()
    inbox_cleaner.clean()


if __name__ == '__main__':
    main()
