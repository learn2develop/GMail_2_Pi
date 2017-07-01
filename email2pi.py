#imports for thermometer reading
import os
import glob
import time
#imports for gmail reading
import imaplib
import email

import smtplib

import hashlib
import string
import random


ALLOWED = []

EMAIL = 'email here'
PASSWORD = 'password'
SUBJECT = 'subject'


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
    m.update( str(random.randint(0,9999)) + id_generator() + str(random.randint(0,9999)) )
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
    smtpObj.login(ADDR, PASS)
    smtpObj.sendmail(ADDR, to, 'Subject: ' + subject + '\n' + body)


def read_gmail(subject):
    """
    read the gmail address
    :param subject: trigger subject
    :return: on success dictionary {from, message}
             else false
    """

    varSubject = None
    varFrom = None

    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(ADDR, PASS)
    mail.select('inbox')

    status, msgs = mail.select('inbox')
    if status != 'OK':
        print "Can not connect"
        return

    mail.list()

    typ, data = mail.search(None, 'ALL')
    for num in data[0].split():
        typ, data = mail.fetch(num, subject)
    typ, data = mail.search(None, 'ALL')
    ids = data[0]
    id_list = ids.split()

    if len(id_list) > 0:

        latest_email_id = int( id_list[-1] )

        for i in range( latest_email_id, latest_email_id-1, -1):
            typ, data = mail.fetch( i, subject)

        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1])

        varSubject = msg['subject']
        varFrom = msg['from']
        varFrom = varFrom.replace('<','')
        varFrom = varFrom.replace('>','')

        #Remove used emails from mailbox
        typ, data = mail.search(None, 'ALL')

    for num in data[0].split():
        mail.store(num, '+FLAGS', '\\Deleted')
        mail.expunge()
        mail.close()
        mail.logout()

    if varSubject is None or varFrom is None:
        return False

    count = 0
    for _email in ALLOWED:
        if varFrom.find(_email) is not -1:
            count += 1
    if count is 0:
        return False


    message = varSubject.replace(subject, '')
    message = message.replace('Re:','')
    message = message.strip()

    sender = varFrom.split()[len(varFrom.split())-1]

    return { 'sender': sender, 'message' : message }


def main():

    print "Waiting for an email"

    while True:

        secret_key = None;

        # The first phase email
        first_reply = read_gmail(SUBJECT)
        if first_reply is False:

            pass

        else:

            print "Email received"
            secret_key = generate_code()
            print "Generated Code: " + secret_key
            original_sender = first_reply['sender']
            send_gmail(original_sender, SUBJECT, secret_key)
            print "Reply sent to " + first_reply['sender']
            print "Waiting for reply"

            # Allow reply within 5 minutes
            timeout = 5 * 60
            timecount = 0

            while True:

                # Timeout the key in 5 minutes
                if timecount == timeout:

                    print "Timeout"
                    print "Destroying the key"
                    secret_key = None # destroy the key
                    break

                # The second phase email
                second_reply = read_gmail(SUBJECT)

                if second_reply is False:

                    pass

                else:

                    print "Email received from " + second_reply['sender']
                    print "Checking key"

                    if second_reply['sender'] == original_sender and second_reply['message'].find(secret_key) is not -1:

                        command = second_reply['message'].replace(secret_key, '')
                        print "Secret key matched"
                        print "Command to execute:" + command.strip()
                        secret_key = None # destroy the key
                        print "Destroying the key"
                        print "Waiting for an email"

                    else:

                        print "Key did not match"
                        secret_key = None # destroy the key
                        print "Destroying the existing key"
                        print "Generating new key"
                        secret_key = generate_code()
                        print "Re-generated code: " + secret_key
                        send_gmail(original_sender, SUBJECT, "Old key failed, new key is " + secret_key)
                        print "New key sent to " + original_sender

                time.sleep(5)
                timecount += 5



        time.sleep(5)
