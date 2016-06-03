import os
import json
import asyncio
import discord

from datetime import *
from functools import partial
from json import JSONDecoder
from chatbot import Chatbot

from timezone import Timezone


class Reminder(object):

    """
    Messages should have the format:
    !remindme (MM/DD/YY) time(in 24hr format ex:22:30) [message]
    !remindme repeat time(in 24hr format ex:22:30) (how many times) [message]
    !remindme in HH MM [message]
    !remind-group [group]; HH MM [message]
    """

    def __init__(self):
        pass

    async def respond(self, client, user, text):
        await client.send_message(user, 'Reminder: ' + text)

    async def group(self, client, message, bot):
        grp = message.content.partition('; ')[0].partition(' ')[2]
        hours = int(message.content.partition('; ')[2].split(' ', 2)[0])
        minutes = float(message.content.partition('; ')[2].split(' ', 2)[1])
        text = message.content.partition('; ')[2].split(' ', 2)[2]

        seconds = hours*60*60 + minutes*60

        await client.send_message(message.channel, 'Reminder set.')
        message.content = '!group-call {}'.format(grp)
        await asyncio.sleep(seconds)
        await bot.group(client, message, 'call')
        await client.send_message(message.channel, "Reminder: {}".format(text))

    async def channel(self, client, message, bot):
        hours = int(message.content.split(' ', 2)[1]).split(':')[1]
        minutes = float(message.content.split(' ', 2)[1]).split(':')[2]
        text = message.content.split(' ', 3)[3]

        seconds = hours*60*60 + minutes*60

        await client.send_message(message.channel, 'Reminder set.')
        await asyncio.sleep(seconds)
        await client.send_message(message.channel, 'Reminder: ' + text)

    async def run(self, client, message, bot):
        option = message.content.split(' ', 3)[1]

        with open('users.json') as data_file:
            data = json.load(data_file)
            while message.author.name not in data:
                await Timezone().check(client, message)
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
                await self.check(client)

    async def check(self, client):
        if os.path.isfile("timezone.txt"):
            pass
        else:
            Timezone.tzList(self)
        if os.path.isfile("users.json"):
            pass
        else:
            with open("users.json", 'w')as fr:
                fr.write("{}")
        if os.path.isfile('reminder.json'):
            pass
        else:
            with open('reminder.json', "w") as frr:
                frr.write("{}")

        if os.path.isfile('reminderRepeat.json'):
            pass
        else:
            with open('reminderRepeat.json', "w") as frrr:
                frrr.write("{}")

        self.purge()

        dateFMT = '%m/%d/%Y'
        timeFMT = '%H:%M'

        current_date = datetime.today().date()

        within_hour = (datetime.today() + timedelta(hours = 1)).strftime(timeFMT)

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

        with open('reminderRepeat.json', 'r+') as data_file_reminder_repeat:
            data_reminder_repeat = json.load(data_file_reminder_repeat)
            for data_reminder_repeat_each in data_reminder_repeat:
                message_time = data_reminder_repeat[data_reminder_repeat_each]['time']
                if message_time <= within_hour:
                    message = data_reminder_repeat[data_reminder_repeat_each]['message']
                    serv = discord.utils.find(lambda m: m.name == Chatbot('settings.txt').server_name, client.servers)
                    user = discord.utils.find(lambda m: m.name == data_reminder_repeat_each, serv.members)
                    time_seconds = datetime.strptime(message_time, timeFMT) - datetime.strptime(datetime.today().strftime(timeFMT), timeFMT)
                    await asyncio.sleep(time_seconds.seconds)
                    await client.send_message(user, message)

                    data_reminder_repeat[data_reminder_repeat_each]['how_many'] = int(data_reminder_repeat[data_reminder_repeat_each]['how_many']) - 1
                    data_file_reminder_repeat.seek(0)
                    data_file_reminder_repeat.write(json.dumps(data_reminder_repeat))
                    data_file_reminder_repeat.truncate()

    def purge(self):
        with open('reminder.json', 'r+') as fr:
            file_r = json.load(fr)
            for file_each_r in list(file_r):
                message_date = datetime.strptime(file_r[file_each_r]['date'], '%m/%d/%Y').date()
                message_time = datetime.strptime(file_r[file_each_r]['time'], '%H:%M').time()
                current_date = datetime.today().date()
                current_time = datetime.today().time()
                if message_date <= current_date and message_time <= current_time:
                    del file_r[file_each_r]
                    fr.seek(0)
                    fr.write(json.dumps(file_r))
                    fr.truncate()
        with open('reminderRepeat.json', 'r+') as frr:
            file_rr = json.load(frr)
            for file_each_rr in list(file_rr):
                how_many = file_rr[file_each_rr]['how_many']
                if how_many is 0:
                    del file_rr[file_each_rr]
                    frr.seek(0)
                    frr.write(json.dumps(file_rr))
                    frr.truncate()

async def save(client, message, option):
    if option == 'repeat':
        #TODO make it add not overwrite
        reminder_time = Timezone().convertToSystemTime(message)
        text = message.content.split(' ', 4)[4]
        how_many = message.content.split(' ', 4)[3]

        with open('reminderRepeat.json') as infile:
            reminder_repeat = json.load(infile)

        reminder_repeat[message.author.name] = {"time": reminder_time, "message": text, "how_many": how_many}

        with open('reminderRepeat.json', 'w') as outfile:
            json.dump(reminder_repeat, outfile)

        await client.send_message(message.channel, 'Reminder set.')

    else:
        #TODO make it add not overwrite
        reminder_time = Timezone().convertToSystemTime(message)
        text = message.content.split(' ', 3)[3]

        with open("reminder.json") as infile:
            reminder = json.load(infile)
        reminder[message.author.name] = {"time": reminder_time, "message": text, "date": option}

        with open("reminder.json", 'w') as outfile:
            json.dump(reminder, outfile)

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
