from telegram import Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters)
import logging
import os
import redis
import requests
import pyodbc
import re

global redis1
def main():
  updater = Updater(token=(os.environ['ACCESS_TOKEN']), use_context=True)
  dispatcher = updater.dispatcher
  global redis1
  redis1 = redis.Redis(host=(os.environ['HOST']),
    password=(os.environ['PASSWORD']),
    port=(os.environ['REDISPORT']))

  logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

  chatgpt_handler = MessageHandler(Filters.text & (~Filters.command), equiped_chatgpt)
  dispatcher.add_handler(CommandHandler("start", greeetings))
  dispatcher.add_handler(chatgpt_handler)

  updater.start_polling()
  updater.idle()

def get_config():
    config = {
        'BASICURL': os.environ.get('BASICURL'),
        'MODELNAME': os.environ.get('MODELNAME'),
        'APIVERSION': os.environ.get('APIVERSION'),
        'ACCESS_TOKEN_GPT': os.environ.get('ACCESS_TOKEN_GPT')
    }
    if None in config.values():
        raise ValueError("Environment variables are not properly set.")
    return config

def submit(message):
    config = get_config()
    conversation = [{"role": "user", "content": message}]
    url = 'https://chatgpt.hkbu.edu.hk/general/rest/deployments/gpt-4-turbo/chat/completions/?api-version=2023-12-01-preview'
    headers = {'Content-Type': 'application/json', 'api-key': '9f72f5f8-fcdc-4052-a80c-cf8c906b1955'}
    payload = {'messages': conversation}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data['choices'][0]['message']['content']
    else:
        return 'Error:', response.status_code, response.text

def greeetings(update, context):
    prompts = 'Play a role of chatbot specified in Hong Kong Hiking, if the topic is not related to Hong Kong Hiking, give notifications and must not give answers to the clients.'
    greeting_message = submit(prompts)
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    reply_message = 'Welcome to the Hong Kong Hiking Helper Chatbot! Let us get started! How can I assist you with your hiking plans today? '
    context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)

def equiped_chatgpt(update, context):
    sentence = update.message.text
    if keyword_finding(sentence) != None:
        reply_message = query(keyword_finding(sentence))
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)
    elif keyword_finding(sentence) == None:
        prompts = 'Play a role of chatbot specified in Hong Kong Hiking, if the topic is not related to Hong Kong Hiking, give notifications and must not give answers to the clients.'
        greeting_message = submit(prompts)
        reply_message = submit(sentence)
        logging.info("Update: " + str(update))
        logging.info("context: " + str(context))
        context.bot.send_message(chat_id=update.effective_chat.id, text=reply_message)

def keyword_finding(sentence):
    keywords = []
    server = os.environ.get('SERVER')
    database = os.environ.get('DATABASE')
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    driver = os.environ.get('DRIVER')

    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM Hiking_Information")
            row = cursor.fetchone()
            while row:
                keywords.append(str(row[0]))
                row = cursor.fetchone()

    sentence_lower = sentence.lower()
    keywords_lower = [keyword.lower() for keyword in keywords]
    for keyword in keywords_lower:
        if re.search(keyword, sentence_lower):
            return keyword
                

def query(trails):
    server = os.environ.get('SERVER')
    database = os.environ.get('DATABASE')
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    driver = os.environ.get('DRIVER')
    trail_name = trails.capitalize()

    with pyodbc.connect('DRIVER='+driver+';SERVER=tcp:'+server+';PORT=1433;DATABASE='+database+';UID='+username+';PWD='+ password) as conn:
        with conn.cursor() as cursor:
            query_message = "SELECT * FROM Hiking_Information WHERE Trail_Name = ?" 
            cursor.execute(query_message, (trail_name))
            row = cursor.fetchone()
            while row:
                suggestions_sentence = 'Give some suggestions for ' + trail_name + ' when go hiking.'
                reply_message = submit(suggestions_sentence)
                query_reply_message = 'Trail Name: ' + str(row[0]) + '\nVideo URL: ' + str(row[1]) + '\nPicture URL: ' + str(row[2]) + '\nTips for This Trail: \n' + reply_message
                row = cursor.fetchone()
                return query_reply_message
                 

if __name__ == '__main__':
    main()
