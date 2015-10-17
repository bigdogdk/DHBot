import datetime
import json
import logging
import os
import requests

import dice
import discord
import gw2api

###################
# Global variables#
###################

EVENT_TEXT_FILE = "events.txt"
HELP_TEXT_FILE = 'help.txt'

#Functions
def get_bot_credential(credential):
	x = open('BotCred.txt', 'r')
	bot_json = json.load(x)
	x.close()
	return bot_json[credential]

def check_role(message, role_test):
	mem = discord.utils.find(lambda m: m.id == message.author.id, message.channel.server.members)
	user_roles = []
	for x in mem.roles:
		user_roles.append(x.name)

	if role_test in user_roles:
		return True
	else:
		return False

# Set up the logging module to output diagnostic to the console.
logging.basicConfig()

# Initialize client object, begin connection
client = discord.Client()
client.login(get_bot_credential('Username'), get_bot_credential('Password'))

if not client.is_logged_in:
	print('Logging in to Discord failed')
	exit(1)

# Event handler
@client.event
def on_message(message):

	if message.content.startswith('!edit_events'):
		if check_role(message, 'BotManager') == True:
			text_file = open(EVENT_TEXT_FILE, 'w')
			new_event_text = message.content.partition(' ')[2]
			trim_event_text = new_event_text[0:1999]
			text_file.write(trim_event_text)
			text_file.close()
			client.delete_message(message)
			client.send_message(message.channel, str(message.author) +' has updated the events message.')
		else:
			client.send_message(message.channel, 'You do not have permission to edit the event message.')


	if message.content.startswith('!events'):
		text_file = open(EVENT_TEXT_FILE, 'r')
		client.send_message(message.channel, text_file.read())
		text_file.close()


	if message.content.startswith('!hello'):
		client.send_message(message.channel, 'Hello {}!'.format(message.author.mention()))


	if message.content.startswith('!help'):
		text_file = open(HELP_TEXT_FILE, 'r')
		client.send_message(message.channel, text_file.read())
		text_file.close()

	if message.content.startswith('!price'):
		item_name = message.content.partition(' ')[2]
		response1 = requests.get("http://www.gw2spidy.com/api/v0.9/json/item-search/"+item_name)
		item_results = json.loads(response1.text)
		testresults = item_results['results']
		for x in range(len(testresults)):
			if str(item_name).lower() == str(testresults[x]['name']).lower():
				itemid = testresults[x]['data_id']
		response2 = requests.get("https://api.guildwars2.com/v2/commerce/prices/"+str(itemid))
		listing = json.loads(response2.text)
		buy_price_raw = listing['buys']['unit_price']
		sell_price_raw = listing['sells']['unit_price']
		bsilver, bcopper = divmod(buy_price_raw, 100)
		bgold, bsilver = divmod(bsilver, 100)
		ssilver, scopper = divmod(sell_price_raw, 100)
		sgold, ssilver = divmod(ssilver, 100)
		client.send_message(message.channel, 'The current buy price of ' +item_name +' is ' +str(bgold).zfill(2) +'g ' +str(bsilver).zfill(2)+ 's ' +str(bcopper).zfill(2)+ 'c. \nThe current sell price is ' +str(sgold).zfill(2) +'g ' +str(ssilver).zfill(2)+ 's ' +str(scopper).zfill(2)+ 'c.')


	if message.content.startswith('!timetohot'):
		time_remaining = datetime.datetime(2015, 10, 23,2,1) - datetime.datetime.now()
		m, s = divmod(time_remaining.seconds, 60)
		h, m = divmod(m, 60)
		client.send_message(message.channel, 'The time remaining to HoT launch is: ' +str(time_remaining.days) + ' days ' + str(h) + ' hours ' + str(m) + ' minutes ' + str(s) + ' seconds.')


	if message.content.startswith('!test'):
		if check_role(message, 'BotManager') == True:
			client.send_message(message.channel, 'You are a BotManager')
		else:
			client.send_message(message.channel, 'You are not a BotManager.')


	if message.content.startswith('!quit'):
		if check_role(message, 'BotManager') == True:
			client.logout()
		else:
			client.send_message(message.channel, 'You do not have permission to stop DHBot.')

	if message.content.startswith('!timetoreset'):
		pass

	if message.content.startswith('!timetowvwreset'):
		pass

	if message.content.startswith('!worldbosses'):
		pass

	if '(╯°□°）╯︵ ┻━┻' in message.content:
		client.send_message(message.channel, '┬─┬﻿ ノ( ゜-゜ノ) \n\n' +str(message.author.name) + ', what did the table do to you?')

	if message.content.startswith('!roll'):
		droll = message.content.partition(' ')[2]
		client.send_message(message.channel, str(dice.roll(droll)))

#	if message.content.startswith('!fractal'):
#		fractal_level = message.content.partition(' ')[2]
#		text_file = open('fractal'+str(fractal_level)+'.txt', 'r')
#		client.send_message(message.channel, 'Would you like to do a 50 fractal? ' + str(text_file.read()))
#		text_file.close()

#	if message.content.startswith('!add_fractal'):
#		fractal_level = message.content.partition(' ')[2]
#		f = open('fractal.txt', 'r')
#		f_list = json.load(f)[str(fractal_level)]
#		f.close()
#		#if message.author not in f_list:
#		f_list.append(message.author)
#			with open('fractal'+fractal_level+'.txt', 'a') as g:
#				g.write(''.format(message.author.mention))
		#	client.send_message(message.channel, str(message.author.name) + ', you have been added to the fractal ' +str(fractal_level) + ' list.')
		#else:
		#	client.send_message(message.channel, str(message.author.name) + ', you are already on that list.')


#@client.event
#def on_message(message):
#	if message.content.startswith('!id'):
#		item_name = message.content.partition(' ')[2]
#		response = requests.get("http://www.gw2spidy.com/api/v0.9/json/item-search/"+item_name)
#		item_results = json.loads(response.text)
#		item_id = item_results['results'][0]['data_id']
#		client.send_message(message.channel, item_id)
		

@client.event
def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print('------')

client.run()