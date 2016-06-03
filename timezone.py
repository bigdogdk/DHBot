import json
import os
import pytz

from datetime import datetime
from tzlocal import get_localzone


class Timezone(object):

    def __init__(self):
        pass

    def run (self):
        pass

    async def check(self, client, message):
        print("checking.")
        if os.path.isfile("users.json"):
            print("file exists.")
        else:
            with open("users.json", 'a'):
                os.utime("users.json", None)

        if os.stat('users.json').st_size == 0:
            pass
        else:
            with open("users.json") as data_file:
                if message.author.name in data_file:
                    print("Timezone set.")
                else:
                    await client.send_message(message.author, "You have not set your timezone.")
                    await client.send_message(message.author, "Please DM me '!tz' and you time zone.(according to the format in this file)")
                    await client.send_file(message.author, 'timezone.txt')

    async def setTimeZone(self, client, message):
        if len(message.content) < 4:
            await client.send_message(message.author, "You have not set your timezone.")
            await client.send_message(message.author, "Please message me '!tz' and you timezone.(according to the format in this file)")
            await client.send_file(message.author, 'timezone.txt')
        else:
            await client.send_message(message.author, "You set your timezone as " + message.content.split(' ', 2)[1] + ".")
            with open("users.json") as infile:
                users = json.load(infile)
            users[message.author.name] = message.content.split(' ', 2)[1]
            with open("users.json", 'w') as outfile:
                json.dump(users, outfile)

    def convertToSystemTime(self, message):
        system_tz = get_localzone()
        with open("users.json") as data_file:
            data = json.load(data_file)
        user_tz = data.get(message.author.name)
        message_time = message.content.split(' ', 3)[2]

        naive_time = datetime.strptime(message_time, '%H:%M')
        tz = pytz.timezone(user_tz)

        aware_time = tz.normalize(tz.localize(naive_time))

        final_time = aware_time.astimezone(system_tz)

        return final_time.strftime('%H:%M')

    def tzList(self):
        alltz = pytz.all_timezones.__str__()
        print(alltz)
        alltzfinal = alltz.replace(',', '\r\n')
        print(alltzfinal)
        with open("timezone.txt", 'w') as file:
            file.write(alltz)
