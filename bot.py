# coding: utf-8
import json
import upwork

from settings import *
#from tornado import gen, ioloop
#main_loop = ioloop.IOLoop.instance()
#main_loop.run_sync(forever)
import telebot
import pymongo
import botan
import time, threading
import datetime
from tornado import gen, ioloop

bot = telebot.TeleBot(telegram_token)

client = pymongo.MongoClient("localhost", 27017)
db = client.freelancers

class jobfeed():
    def __init__:
        self.title
        self.budget
        self.url

def parsedate(string):
    return datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S%z")

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
    botan.track(metrika_token, uid, message_dict, 'Search')
    bot.register_next_step_handler(msg, set_query)

def set_query(message):
    #first query for a timestamp
    client = upwork.Client(public_key, secret_key, oauth_access_token=access_token, oauth_access_token_secret=access_token_secret)
    query = {'q': message.text }
    data = client.provider_v2.search_jobs(data=query)
    freelancer = { "username": message.from_user.username, "chat_id": message.chat.id, \
        "query": message.text, "timestamp": data[0]["date_created"] }
    result = db.upwork.replace_one({"username": message.from_user.username}, freelancer, True)
    bot.send_message(message.chat.id, "Your query is: %s" % freelancer["query"])



@bot.message_handler(commands=['query'])
def get_query(message):
    #show the installed query
    freelancer = { "username": message.from_user.username }
    result = db.upwork.find_one(freelancer)
    if result != None:
        bot.send_message(message.chat.id, result["query"])
        bot.send_message(message.chat.id, "If you want change the query, use /change command")
    else:
        bot.send_message(message.chat.id, "Query is not set")

@bot.message_handler(commands=['change'])
def change_query(message):
    freelancer = { "username": message.from_user.username }
    result = db.upwork.find_one(freelancer)
    if result == None:
        query = "not set"
    else:
        query = result["query"]
    msg = bot.send_message(message.chat.id, """\
Dear, %s
Your query is %s
To change a query, 
write keywords separated commas for your job search.
For example: python, api, crawler 
""" % (message.from_user.first_name, query))
    bot.register_next_step_handler(msg, set_query)


def last_job():
    threading.Timer(100, last_job).start()
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

                bot.send_message(freelancer["chat_id"], text)
        #    else:
        #        bot.send_message(freelancer["chat_id"], "ooops")
        #update = {"username": freelancer["username"] },{"$set": {"timestamp": data[0]["date_created"]}}
        result = db.upwork.update_one({"username": freelancer["username"] },{"$set": {"timestamp": data[0]["date_created"]}})

def main():
    last_job()
    bot.polling()

main_loop = ioloop.IOLoop.instance()
main_loop.run_sync(main)