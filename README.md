# TidyMail
This repository contains a Python script to organize your Gmail inbox. I use the 
[Gmail API Client Library for Python](https://developers.google.com/api-client-library/python/apis/gmail/v1?hl=en)--visit the link for library installation and authentication instructions.

Once you have followed the instructions in the link above, clone this repository and add the `client_secret.json` file to the directory. Edit the `UNCATEGORIZED_LABEL_ID` variable in the script and just run `python inboxcleaner.py`.

This script takes the simplest possible approach to guessing which folders an email should be moved to by searching for emails from the given sender and moving the message to the label that has the most emails. If there are no labeled emails from the sender, the message will be moved to the label specified by `UNCATEGORIZED_LABEL_ID`. Note that this script won't delete any messages, it only moves messages out of the Inbox label to the suggested label.

## To Do
1. This currently only works on 100 messages at a time. If there are more than 100 messages in your inbox you can simply run this multiple times for now. Getting this to work for all messages is easy to do but hasn't been implemented yet.
2. More intelligent label suggestions. Many emails will just be moved to Uncategorized but there is other information that could be incorporated (subject, keywords, etc..)
3. Add command line arguments for passing in the number of days of inbox messages to keep.
