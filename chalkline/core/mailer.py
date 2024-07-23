from flask_mail import Message
from chalkline import mail
from flask import copy_current_request_context
from threading import Thread

MAIL_SENDER = 'Chalkline Baseball'

class ChalklineEmail(Message):
    def __init__(self, subject='Message from Chalkline', recipients=None, body=None, html=None, sender=MAIL_SENDER, cc=None, bcc=None, attachments=None, reply_to=None, date=None, charset=None, extra_headers=None, mail_options=None, rcpt_options=None):
        super().__init__(subject, recipients, body, html, sender, cc, bcc, attachments, reply_to, date, charset, extra_headers, mail_options, rcpt_options)

def sendMail(msg):
    mail.send(msg)

def sendBulkMail(msgList, asynchronous = True):
    @copy_current_request_context
    def sendAsync(msgList):
        logs = []
        with mail.connect() as conn:
            for msg in msgList:
                try:
                    conn.send(msg)
                    logs.append({
                        'location': None,
                        'type': 'Mail sent',
                        'desc': 'Success!',
                        'userId': msg.recipients[0],
                        'eventId': None
                    })
                except:
                    logs.append({
                        'location': None,
                        'type': 'Mail sent',
                        'desc': 'Failed',
                        'userId': msg.recipients[0],
                        'eventId': None
                    })
        
    if asynchronous: 
        Thread(target=sendAsync, args=(msgList, )).start()
    else:
        sendAsync(msgList)
    
    


