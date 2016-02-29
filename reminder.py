import os
import json
import asyncio
import threading
import discord

from datetime import *
from functools import partial
from json import JSONDecoder
from chatbot import Chatbot

from timezone import Timezone


class Reminder(object):

    """
    Messages should have the format:
    !remindme [date(MM/DD/YY)|repeat|in] [time(in 24hr format ex:22:30)|hh mm (instead if within certain time)ex:00 30] [how many(if repeat)] [message]
    """

    once00, once15, once30, once45, repeat00, repeat15, repeat30, repeat45 = ([] for i in range(8))

    def __init__(self):
        pass

    async def respond(self, client, user, text):
        await client.send_message(user, 'Reminder: ' + text)

    async def run(self, client, message, bot, *query):
        if query == 'channel':
            print('channel')
            #TODO channel reminder
        else:
            option = message.content.split(' ', 3)[1]
            if os.path.isfile("users.json"):
                pass
            else:
                with open("users.json", 'a'):
                    os.utime("users.json", None)
            with open('users.json') as data_file:
                data = json.load(data_file)
                while message.author.name not in data:
                    Timezone().check(client, message)
                if option == 'in':
                    text = message.content.split(' ', 4)[4]
                    hour = float(message.content.split(' ', 4)[2])
                    minute = float(message.content.split(' ', 4)[3])
                    await client.send_message(message.channel, 'Reminder set.')
                    total_seconds = ((hour * 60) + minute)*60
                    await asyncio.sleep(total_seconds)
                    await client.send_message(message.author, "Reminder: {}".format(text))
                else:
                    await save(client, message, option)

    async def check(self, client):
        print("checking")
        dateFMT = '%m/%d/%Y'
        timeFMT = '%H:%M'
        current_date = datetime.today().date()
        within_hour = (datetime.today() + timedelta(hours = 1)).strftime(timeFMT)
        if os.stat('reminder.json').st_size == 0:
            #to prevent error if file is empty
            pass
        else:
            with open('reminder.json', 'r+') as data_file_reminder:
                data_reminder = json.load(data_file_reminder)
                for data_reminder_each in data_reminder:
                    message_date = datetime.strptime(data_reminder[data_reminder_each]['date'], dateFMT).date()
                    message_time = data_reminder[data_reminder_each]['time']
                    if message_time <= within_hour and message_date == current_date:
                        message = data_reminder[data_reminder_each]['message']
                        serv = discord.utils.find(lambda m: m.name == Chatbot('settings.txt').server_name, client.servers)
                        user = discord.utils.find(lambda m: m.name == data_reminder_each, serv.members)
                        time_seconds = datetime.strptime(message_time, timeFMT) - datetime.strptime(datetime.today().strftime(timeFMT), timeFMT)
                        await asyncio.sleep(time_seconds.seconds)
                        await client.send_message(user, message)
                        data_reminder[data_reminder_each] = "true"
                        data_file_reminder.seek(0)
                        data_file_reminder.write(json.dumps(data_reminder))
                        data_file_reminder.truncate()
        with open('reminder.json', 'r+') as data_file_reminder:
            data_reminder = json.load(data_file_reminder)
            for data_reminder_each, v in list(data_reminder.items()):
                if v == "true":
                    print("true")
                    del data_reminder[data_reminder_each]
                    data_file_reminder.seek(0)
                    data_file_reminder.write(json.dumps(data_reminder))
                    data_file_reminder.truncate()
        await asyncio.sleep(5)#30 min = 1800
        await self.check(client)

async def save(client, message, option):
    if option == 'repeat':
        reminder_time = Timezone().convertToSystemTime(message)
        text = message.content.split(' ', 4)[4]
        how_many = message.content.split(' ', 4)[3]
        data = {
            message.author.name:{
                'time': reminder_time,
                'message': text,
                'how many': how_many
            }
        }
        with open('reminderRepeat.json', 'a') as outfile:
            json.dump(data, outfile)
        await client.send_message(message.channel, 'Reminder set.')

    else:
        #TODO make it add not overwrite
        reminder_time = Timezone().convertToSystemTime(message)
        text = message.content.split(' ', 3)[3]
        reminder_file = open("reminder.json", 'r+')
        reminders = json.load(reminder_file)
        reminders[message.author.name] = {"time": reminder_time, "message": text, "date": option}
        reminder_file.seek(0)
        reminder_file.write(json.dumps(reminders))
        reminder_file.truncate()
        reminder_file.close()
        await client.send_message(message.channel, 'Reminder set.')


def json_parse(file_obj, decoder=JSONDecoder(), buffersize=2048):
    buffer = ''
    for chunk in iter(partial(file_obj.read, buffersize), ''):
        buffer += chunk
        while buffer:
            try:
                result, index = decoder.raw_decode(buffer)
                yield result
                buffer = buffer[index:]
            except ValueError:
                # Not enough data to decode, read more
                break
