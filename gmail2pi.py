#!/usr/bin/python
"""
Original forked from https://github.com/joolswhitehorn/stuff-projects

Communicate with Raspberry Pi or any computer via Google Mail
Copyright (C) 2017  Jiri Dohnalek

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# IMPORTS #########################################################

import time
import imaplib
import email
import smtplib
import hashlib
import string
import random
import requests

# CONSTANTS #######################################################

# List of allowed email addresses that can send email to the
# Raspaberry Pi
ALLOWED = []

# Email address used by Raspberry Pi to probe for email with
# a specific subject to trigger action
EMAIL = ''

# Password to access the email address
PASSWORD = ''

# Triggering subject (Do not change)
SUBJECT = '(rfc822)'


# Time after which the secret key expires
TIMEOUT = 5 * 60

# How often to check email in second stage
INCREMENTS = 5

# FUNCTIONS ######################################################


def id_generator(size=15, chars=string.ascii_uppercase + string.digits):
    """
    Generate random string of 15 capital letters and numbers
    """
    return ''.join(random.choice(chars) for _ in range(size))

def generate_code():
    """
    Convert the string using md5 to create the exchange key
    """
    m = hashlib.md5()
    m.update(str(random.randint(0, 9999)) + id_generator() + str(random.randint(0, 9999)))
    return m.hexdigest()

def send_gmail(to, subject, body):
    """
    Send email

    :param to: send the email to
    :param subject: email subject
    :param body: the text of the message
    """
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login(EMAIL, PASSWORD)
    smtpObj.sendmail(EMAIL, to, 'Subject: ' + subject + '\n' + body)

def read_gmail(subject):
    """
    read the gmail address
    :param subject: trigger subject
    :return: on success dictionary {from, message}
             else false
    """

    subject = None
    sender = None
    body = ""

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(EMAIL, PASSWORD)
    
    try:
        mail.select('inbox')
    except imaplib.IMAP4.abort:
        return False
    except imaplib.IMAP4.error:
        return False
    
    try:
        status, msgs = mail.select('inbox')
        if status != 'OK':
            print "Can not connect"
            return False
    
    except imaplib.IMAP4.abort:
        return False
    except imaplib.IMAP4.error:
        return False
        
    mail.list()

    typ, data = mail.search(None, 'ALL')
    for num in data[0].split():
        typ, data = mail.fetch(num, subject)
    typ, data = mail.search(None, 'ALL')
    ids = data[0]
    id_list = ids.split()

    if len(id_list) > 0:

        latest_email_id = int(id_list[-1])

        for i in range(latest_email_id, latest_email_id - 1, -1):
            typ, data = mail.fetch(i, subject)

        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1])

        # get the body of the message
        if msg.is_multipart():
            for payload in msg.get_payload():
                try:
                    body += payload.get_payload()
                except TypeError:
                    body += ""
        else:
            body = msg.get_payload()

        # get the subject of the message
        subject = msg['subject']
        sender = msg['from']

        # get from who is the message
        sender = sender.replace('<', '')
        sender = sender.replace('>', '')

        # Remove used emails from mailbox
        typ, data = mail.search(None, 'ALL')

    for num in data[0].split():
        mail.store(num, '+FLAGS', '\\Deleted')
        mail.expunge()
        mail.close()
        mail.logout()

    if subject is None or sender is None:
        return False

    count = 0
    for _email in ALLOWED:
        if sender.find(_email) is not -1:
            count += 1
    if count is 0:
        return False

    sender = sender.split()[len(sender.split()) - 1]

    # Strip the uneccesary text fro the body
    if "\n" in body:
        body = body.split("\n")[0]

    return {'sender': sender, 'subject': subject, 'body': body}

def main():
    """ Main routine """
    print "Waiting for an email"

    while True:

        while True:

            secret_key = None
            first_reply = False
            second_reply = False

            # The first phase email
            first_reply = read_gmail(SUBJECT)
            # print "first reply:", first_reply

            if first_reply is False:
                pass

            else:

                print "Email received"
                secret_key = generate_code()
                print "Generated Code: " + secret_key
                original_sender = first_reply['sender']
                send_gmail(original_sender, SUBJECT + " " + secret_key, "")
                print "Reply sent to " + first_reply['sender']
                print "Waiting for reply"

                # Allow reply within 5 minutes
                timecount = 0

                break

            time.sleep(15)

        while True:

            # Timeout the key in 5 minutes
            if timecount == TIMEOUT:

                print "Timeout"
                print "Destroying the key"
                secret_key = None  # destroy the key

                send_gmail(original_sender, "System Timeout", "You have run out of time, please start again")
                break

            # The second phase email
            second_reply = read_gmail(SUBJECT)
            # print "second reply:", second_reply

            if second_reply is False:
                pass

            else:
                print "Email received from " + second_reply['sender']
                print "Checking key"

                condition1 = second_reply['sender'] == original_sender
                condition2 = second_reply['subject'].find(secret_key) is not -1

                if condition1 and condition2:

                    command = second_reply['body'].upper().strip()
                    print "Secret key matched"
                    print "Command to execute:" + command

                    send_gmail(
                        original_sender,
                        second_reply['subject'],
                        'Command "{}" executed succesfully'.format(
                            command.strip()
                        )
                    )

                    print "Confirmation sent to " + original_sender
                    secret_key = None  # destroy the key
                    print "Destroying the key"
                    print "Waiting for an email"

                else:

                    print "Key did not match"
                    print "Generating new key"
                    secret_key = generate_code()
                    print "New generated code: " + secret_key
                    send_gmail(original_sender, SUBJECT + " [NEW] " + secret_key, "")
                    print "New key sent to " + original_sender

                break
            
            time.sleep(INCREMENTS)
            timecount += INCREMENTS


###########################


if __name__ == '__main__':
    main()
