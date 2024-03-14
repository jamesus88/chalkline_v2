from flask_mail import Message
from chalkline import mail
from flask import copy_current_request_context
from threading import Thread

MAIL_SENDER = 'Chalkline Baseball'

class ChalklineEmail(Message):
    def __init__(self, subject='Message from Chalkline', recipients=None, body=None, html=None, sender=MAIL_SENDER, cc=None, bcc=None, attachments=None, reply_to=None, date=None, charset=None, extra_headers=None, mail_options=None, rcpt_options=None):
        super().__init__(subject, recipients, body, html, sender, cc, bcc, attachments, reply_to, date, charset, extra_headers, mail_options, rcpt_options)

def sendMail(msg):
    try:
        mail.send(msg)
        print("Mail sent to", msg.recipients)
    except:
        print("Unable to send mail to", msg.recipients)

def sendBulkMail(msgList, asynchronous = True):
    @copy_current_request_context
    def sendAsync(msgList):
        with mail.connect() as conn:
            for msg in msgList:
                try:
                    conn.send(msg)
                    print("Mail sent to", msg.recipients)
                except:
                    print("Unable to send mail to", msg.recipients)
                    
        if asynchronous: print("Finished Mail Thread process.")
        
    if asynchronous: 
        print("Started Mail Thread...")
        Thread(target=sendAsync, args=(msgList, )).start()
    else:
        print("Sending mail synchronously")
        sendAsync(msgList)
    
    


