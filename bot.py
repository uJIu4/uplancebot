# coding: utf-8

import telebot, botan, tweepy, upwork, pymongo
import time, threading, logging, random, json
import flask
from settings import *
from utils import *
from emoji import get_random_emoji


#Twitter config
auth = tweepy.OAuthHandler(twi_key, twi_secret)
auth.set_access_token(twi_token, twi_token_secret)
api = tweepy.API(auth)

#Webhook config
WEBHOOK_HOST = host
WEBHOOK_PORT = 8443  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '0.0.0.0'  # In some VPS you may need to put here the IP addr
WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (telegram_token)
# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

#Flask init
app = flask.Flask(__name__)

#Telegram bot api
logger = telebot.logger
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(telegram_token)

#Mongo
client = pymongo.MongoClient("localhost", 27017)
db = client.freelancers

# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.json
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_messages([update.message])
        
        return ''
    else:
        flask.abort(403)

# Handle '/start'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    msg = bot.send_message(message.chat.id, """\
Hi there, I am Freelance bot!
Let's start.
Write keywords separated commas for your job search.
For example: python, api, crawler 
""")
    uid = message.from_user.id 
    message_dict = json.dumps(message,  default=lambda o: o.__dict__)
    botan.track(metrika_token, uid, message_dict, 'Start')
    bot.register_next_step_handler(msg, set_query)

def set_query(message):
    #sets query for a timestamp
    delete = db.upwork.delete_many({"chat_id": message.chat.id})
    client = upwork.Client(public_key, secret_key, oauth_access_token=access_token, oauth_access_token_secret=access_token_secret)
    keywords = [x.strip() for x in message.text.split(',')]
    for keyword in keywords:
        query = {'q': keyword }
        data = client.provider_v2.search_jobs(data=query)
        freelancer = { "username": message.from_user.username, "chat_id": message.chat.id, \
            "query": keyword, "timestamp": data[0]["date_created"] }
        result = db.upwork.insert_one(freelancer)
    bot.send_message(message.chat.id, "Your query is set")


@bot.message_handler(commands=['query'])
def get_query(message):
    #show the installed query
    queries = []
    freelancer = { "chat_id": message.fchat.id }
    for query in db.upwork.find(freelancer):
        queries.append(query["query"])
    result = ",".join(queries)
    if result != None:
        bot.send_message(message.chat.id, result)
        bot.send_message(message.chat.id, "If you want change the query, use /change command")
    else:
        bot.send_message(message.chat.id, "Query is not set")

@bot.message_handler(commands=['change'])
def change_query(message):
    msg = bot.send_message(message.chat.id, """\
Dear, %s
To change a query, 
write keywords separated commas for your job search.
For example: python, api, crawler 
""" % (message.from_user.first_name,))
    bot.register_next_step_handler(msg, set_query)


def last_job():
    threading.Timer(600, last_job).start()
    freelancers = db.upwork.find()
    for freelancer in freelancers:
        client = upwork.Client(public_key, secret_key, oauth_access_token=access_token, oauth_access_token_secret=access_token_secret)
        query = {'q': freelancer['query'] }
        data = client.provider_v2.search_jobs(data=query)
        
        for x in reversed(range(len(data))):
            if parsedate(data[x]["date_created"]) > parsedate(freelancer["timestamp"]):
                if data[x]["budget"] == None:
                    cost = u''
                else:
                    cost = ' $' + str(data[x]["budget"])
                text = str(data[x]["title"]) + ' ' + cost + ' ' + str(data[x]["url"])
                #TODO: if frelanceers unsubscribed
                try:
                    bot.send_message(freelancer["chat_id"], text)
                except Exception as e:
                    if e.result.status_code == 400:
                        db.upwork.delete_many({"_id": freelancer["_id"] })
                # Tweet with probability
                if random.randint(1, 10) > 9:
                    text += " #upwork #jobs #{0}".format(freelancer["query"])
                    api.update_status(status=text)

        result = db.upwork.update_one({"_id": freelancer["_id"] }, \
            {"$set": {"timestamp": data[0]["date_created"]}})

def stat_tweet():
    threading.Timer(86400, stat_tweet).start()
    ppl = str(len(db.upwork.distinct("chat_id")))
    text = "Hey! {0} ppl already have used my services {1}. Add me in telegram -> \
        http://telegram.org/uplancebot".format(ppl, get_random_emoji())
    api.update_status(status=text)

@bot.message_handler(commands=['feedback'])
def get_feedback(message):
    msg = bot.send_message(message.chat.id, """\
Please write your feedback here, I will 
forward it to my architect.
""" )
    bot.register_next_step_handler(msg, feedback)

def feedback(message):
    sendmail(message.text, message.from_user.username)

    uid = message.from_user.id 
    message_dict = json.dumps(message,  default=lambda o: o.__dict__)
    botan.track(metrika_token, uid, message_dict, 'feedback')

    msg = bot.send_message(message.chat.id, "Thank you for your feedback!")
    

@bot.message_handler(commands=['sendall'])
def send_message_to_clients(message):
    msg = bot.send_message(message.chat.id, """\
Write a messege to all users
""" )
    bot.register_next_step_handler(msg, send_message)

def send_message(message):
    freelancers = db.upwork.distinct("chat_id")
    for freelancer in freelancers:
        bot.send_message(freelancer, message.text)



if __name__ == '__main__':
    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()

    # Set webhook
    bot.set_webhook(url=WEBHOOK_URL_BASE+WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))
    p1 = threading.Thread(target=last_job(), name="t1")
    p2 = threading.Thread(target=app.run(host=WEBHOOK_LISTEN, port=WEBHOOK_PORT, ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV), debug=False), name="t2", args=[])
    p3 = threading.Thread(target=stat_tweet(), name="t3")
    p1.start()
    p2.start()
    p3.start()


