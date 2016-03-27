#!/usr/bin/env python

import asyncio
import datetime
from datetime import datetime
import json
import os
import sys
from os.path import getmtime
import logging
import trivia

import discord

from cleverbot import cleverbot
from chatbot import Chatbot
from polls import Poll
from reminder import Reminder
from timezone import Timezone
from trivia import Trivia

# Set up the logging module to output diagnostic to the console.
logging.basicConfig()

# Create new instances of bot objects
bot = Chatbot('settings.txt')
remind_module = Reminder()
timezone_module = Timezone()
trivia_module = Trivia()
poll_module = Poll()

#cleverbot object
clever_bot = cleverbot.Session()

# Initialize client object, begin connection
client = discord.Client()

serv = ''

# Event handler
@client.event
async def on_member_join(newmember):
	admin_users = []
	leadership_names = []
	for x in newmember.server.members:
		if bot.check_role(client, x, 'Admin') == True:
			admin_users += [x]
		if bot.check_role(client, x, 'Leadership') == True:
			leadership_names += [x.name]
	notification_channel = discord.utils.find(lambda m: m.name == 'bot-notifications', newmember.server.channels)
	admin_mentions = ''
	for x in admin_users:
		admin_mentions += " " + (x.mention)
	await client.send_message(notification_channel, newmember.name + ' needs permissions. ' + admin_mentions)
	await client.send_message(newmember, 'Welcome to the Descendants of Honor Discord server. My name is ' +client.user.name +', the chat bot for this server. I have sent a message to the server Admins to let them know you have joined. They will give you appropriate permissions as soon as possible.\n\nIn the meantime, you are free to use the lobby text-chat and Public voice channels. If you are a member of the DH Guild Wars 2 guild or are considering becoming one, please take a moment to let us know your GW2 Display Name by sending the following message in this chat:\n`!display name <GW2 Display Name>`\nPlease note that you do not need to enter <>. For example:\n`!displayname Xantha.1234`\nPlease be sure to read the announcements as well.\n\nYou may also utilize some of my functions by responding to this message or by posting in a text channel. To find a list of my functions, you may type !help.\n\nIf you are having difficulties with your sound or voice in Discord, you can check https://support.discordapp.com/hc/en-us or ask in Discord or guild chat for assistance. If you encounter any problems with the bot, please contact Xorin.')

	if newmember.name in leadership_names:
		await client.send_message(newmember, "I have noticed that your name matches the name of one of our members of leadership. Please take a moment to go to your Discord settings (the cog on the lower left of the client) and change your username. If you need assistance with this, please ask. Failure to make this change may result in your Discord permissions being revoked.")
		await client.send_message(notification_channel, "The new member with user ID {} currently has the same name as {}. They have been asked to change their name.".format(newmember.id, newmember.name))

@client.event
async def on_member_update(before, after):
	notification_channel = discord.utils.find(lambda m: m.name == 'bot-notifications', after.server.channels)

	if (str(before.status) == 'offline' and str(after.status) == 'online') or ((str(before.status) == 'online' or str(before.status) == 'idle') and str(after.status) == 'offline'):
		try:
			with open('discord_logs.txt', 'r') as f:
				discord_logs = json.load(f)
		except:
			discord_logs = json.loads('{}')
		if after.id not in discord_logs:
			discord_logs[after.id] = {"last login": "N/A", "last logoff": "N/A"}
		now = str(datetime.utcnow())
		if str(after.status) == 'online':
			discord_logs[after.id]['last login'] = now
		if str(after.status) == 'offline':
			discord_logs[after.id]['last logoff'] = now
		with open('discord_logs.txt', 'w') as f:
			f.write(json.dumps(discord_logs))
	
	
	if (str(before.status) == 'offline' and str(after.status) == 'online') or ((str(before.status) == 'online' or str(before.status) == 'idle') and str(after.status) == 'offline'):
		try:
			with open('discord_logs.txt', 'r') as f:
				discord_logs = json.load(f)
		except:
			discord_logs = json.loads('{}')
		if after.id not in discord_logs:
			discord_logs[after.id] = {"last login": "N/A", "last logoff": "N/A"}
		now = str(datetime.utcnow())
		if str(after.status) == 'online':
			discord_logs[after.id]['last login'] = now
		if str(after.status) == 'offline':
			discord_logs[after.id]['last logoff'] = now
		with open('discord_logs.txt', 'w') as f:
			f.write(json.dumps(discord_logs))
	
	if str(before.status) == 'offline' and str(after.status) == 'online' and bot.check_role(client, after, "Member") == True:
			x = open("display_names.txt", 'r')
			disp_names = json.load(x)
			x.close()
			if after.id not in disp_names:
				await client.send_message(after, "My name is Xantha, the DH Discord bot. According to my records, your GW2 Display Name is not listed in our database. Please enter \n`!displayname <GW2 Display name>`\n without the <>, for example \n`!displayname Xantha.1234`\nin Discord. Be sure to use your full name, including the 4 digits at the end. If you need help, please ask an Admin.")

	leadership_names = []
	for x in after.server.members:
		if bot.check_role(client, x, 'Leadership') == True:
			leadership_names += [x.name]
	if before.name not in leadership_names and after.name in leadership_names and bot.check_role(client, after, "Leadership") == False:
		await client.send_message(after, "I have noticed that you have changed your name to the name of one of our members of leadership. Please take a moment to go to your Discord settings and change your username to something else. Failure to make this change may result in your Discord permissions being revoked.")
		await client.send_message(notification_channel, "The member with user ID {} has changed their name from {} to {}. They have been asked to change their name.".format(after.id, before.name, after.name))
	if before.name in leadership_names and after.name not in leadership_names and bot.check_role(client, after, "Leadership") == False:
		await client.send_message(after, "Thank you for changing your username.")
		await client.send_message(notification_channel, "The member with user ID {} has changed their name from {} to {}.".format(after.id, before.name, after.name))

	if str(before.status) == 'offline' and str(after.status) == 'online' and after.name == "Scottzilla":
		await client.send_message(after, ":boom: Happy birthday! :boom:")

@client.event
async def on_message(message):

	if bot.check_role(client, message, 'BotBan') == False:

		if message.content.lower() == '!test':
			await client.send_message(message.channel, serv.name)

		if message.content.lower().startswith('!play'):
			await bot.play(client, message, serv)

		if message.content.lower() == '!stop':
			await voice.disconnect()

		if message.content.startswith('{}'.format(client.user.mention)):
			cb_message = message.content.partition(' ')[2]
			answer = clever_bot.Ask(str(cb_message))
			await client.send_message(message.channel, str(answer))

		if message.content.lower() == '!adminhelp':
			await bot.help(client, message, 'admin')

		if message.content.lower().startswith('!adminhelp-add'):
			await bot.help(client, message, 'add-admin')

		if message.content.lower().startswith('!adminhelp-delete'):
			await bot.help(client, message, 'delete-admin')

		if message.content.lower().startswith('!away-return'):
			await bot.away_fnc(client, message, 'return')

		if message.content.lower().startswith('!away-set'):
			await bot.away_fnc(client, message, 'set')

		if message.content.lower().startswith('!away-whois'):
			await bot.away_fnc(client, message, 'whois')

		if message.content.lower().startswith('!checkid'):
			await bot.id_fnc(client, message, 'other')
		
		if message.content.lower().startswith('!clear'):
			await bot.clear(client, message)

		if message.content.lower().startswith('!displayname '):
			await bot.displayname(client, message, 'self')

		if message.content.lower().startswith('!displayname-send'):
			await bot.displayname(client, message, 'send')

		if message.content.lower().startswith('!displayname-set '):
			await bot.displayname(client, message, 'set')

		if message.content.lower() == '!events':
			await bot.file_interface(client, message, 'events', 'read')

		if message.content.lower().startswith('!events-edit'):
			await bot.file_interface(client, message, 'events', 'write')

		if message.content.lower().startswith('!group-create'):
			await bot.group(client, message, 'create')

		if message.content.lower().startswith('!group-delete'):
			await bot.group(client, message, 'delete')

		if message.content.lower().startswith('!group-enroll'):
			await bot.group(client, message, 'enroll')

		if message.content.lower().startswith('!group-add '):
			await bot.group(client, message, 'add')

		if message.content.lower().startswith('!group-open'):
			await bot.group(client, message, 'open')

		if message.content.lower().startswith('!group-close'):
			await bot.group(client, message, 'close')

		if message.content.lower().startswith('!group-call'):
			await bot.group(client, message, 'call')

		if message.content.lower().startswith('!group-mine'):
			await bot.group(client, message, 'mine')

		if message.content.lower().startswith('!group-remove '):
			await bot.group(client, message, 'remove')

		if message.content.lower().startswith('!group-remove_all '):
			await bot.group(client, message, 'remove all')

		if message.content.lower().startswith('!group-unenroll'):
			await bot.group(client, message, 'unenroll')

		if message.content.lower().startswith('!group-list'):
			await bot.group(client, message, 'list')

		if message.content.lower().startswith('!group-members'):
			await bot.group(client, message, 'members')

		if message.content.lower().startswith('!group-info'):
			await bot.group(client, message, 'info')

		if message.content.lower().startswith('!hello'):
			await bot.greet(client, message)

		if message.content.lower() == '!help':
			await bot.help(client, message, 'read')

		if message.content.lower().startswith('!help '):
			await bot.help(client, message, 'info')

		if message.content.lower().startswith('!help-edit'):
			await bot.help(client, message, 'edit')

		if message.content.lower().startswith('!help-add'):
			await bot.help(client, message, 'add')

		if message.content.lower().startswith('!help-delete'):
			await bot.help(client, message, 'delete')

		if message.content.startswith('!last_on '):
			id_or_name = message.content.partition(' ')[2]
			member = bot.member_lookup(client, id_or_name, serv)
			if member != None:
				last_on = bot.log_fnc(member, 'last on')
				await client.send_message(message.channel, "{} was last seen online: {}.".format(member.name, str(last_on).partition('.')[0]))
			else:
				await client.send_message(message.channel, "There was an error finding the member {}. There may be multiple or no members with that name/ID.".format(id_or_name))

		if message.content.lower().startswith('!lmgtfy'):
			await bot.lmgtfy(client, message)

		if message.content.lower().startswith('!mission '):
			await bot.mission(client, message, 'info')

		if message.content.lower().startswith('!mission-add'):
			await bot.mission(client, message, 'add')

		if message.content.lower().startswith('!mission-edit'):
			await bot.mission(client, message, 'edit')

		if message.content.lower().startswith('!mission-delete'):
			await bot.mission(client, message, 'delete')

		if message.content.lower().startswith('!mission-list'):
			await bot.mission(client, message, 'list')

		if message.content.lower().startswith('!poll-close'):
			await poll_module.poll_fnc(client, message, 'close')

		if message.content.lower().startswith('!poll-create '):
			await poll_module.poll_fnc(client, message, 'create')

		if message.content.lower().startswith('!poll-create_anon'):
			await poll_module.poll_fnc(client, message, 'create anon')

		if message.content.lower().startswith('!poll-create_multi'):
			await poll_module.poll_fnc(client, message, 'create multi')

		if message.content.lower().startswith('!poll-delete'):
			await poll_module.poll_fnc(client, message, 'delete')

		if message.content.lower().startswith('!poll-info'):
			await poll_module.poll_fnc(client, message, 'info')

		if message.content.lower().startswith('!poll-list'):
			await poll_module.poll_fnc(client, message, 'list')

		if message.content.lower().startswith('!poll-open'):
			await poll_module.poll_fnc(client, message, 'open')

		if message.content.lower().startswith('!poll-results'):
			await poll_module.poll_fnc(client, message, 'results')

		if message.content.lower().startswith('!price'):
			await bot.price(client, message)

		if message.content.lower().startswith('!purge'):
			await bot.purge(client, message)

		if message.content.lower().startswith('!quit'):
			await bot.stop_bot(client, message)

		if message.content.lower().startswith('!remindme'):
			await remind_module.run(client, message, bot)

		if message.content.lower().startswith('!food'):
			await asyncio.sleep(10) #25 minutes = 1500
			await client.send_message(message.channel, "Food check!")

		if message.content.lower().startswith('!reminder'):
			await remind_module.channel(client, message, bot)

		if message.content.lower().startswith('!remind-group'):
			await remind_module.run(client, message, bot)

		if message.content.lower().startswith('!tz'):
			await timezone_module.setTimeZone(client, message)

		if message.content.lower().startswith('!role-assign'):
			member_id_or_name = message.content.partition(' ')[2].partition('; ')[0]
			role_names = message.content.partition(' ')[2].partition('; ')[2].split(', ')
			await bot.role_fnc(client, message.author, message.channel, member_id_or_name, role_names, 'assign')

		if message.content.lower().startswith('!role-remove'):
			member_id_or_name = message.content.partition(' ')[2].partition('; ')[0]
			role_names = message.content.partition(' ')[2].partition('; ')[2].split(', ')
			await bot.role_fnc(client, message.author, message.channel, member_id_or_name, role_names, 'remove')

		if message.content.lower().startswith('!roll'):
			await bot.roll_dice(client, message)

		if message.content.lower().startswith('!roster-copy'):
			await bot.roster_fnc(client, message, 'copy')

		if message.content.lower().startswith('!roster-promotion'):
			await bot.roster_fnc(client, message, 'promotion')

		if message.content.lower() == '!roster-send':
			await bot.roster_fnc(client, message, 'send')

		if message.content.lower().startswith('!roster-send '):
			await bot.roster_fnc(client, message, 'send specified')

		if message.content.lower().startswith('!roster-sendpromotion'):
			await bot.roster_fnc(client, message, 'send promotion')

		if message.content.lower().startswith('!survey-change'):
			await poll_module.survey_fnc(client, message, 'change')

		if message.content.lower().startswith('!survey-close'):
			await poll_module.survey_fnc(client, message, 'close')

		if message.content.lower().startswith('!survey-create'):
			await poll_module.survey_fnc(client, message, 'create')

		if message.content.lower().startswith('!survey-delete'):
			await poll_module.survey_fnc(client, message, 'delete')

		if message.content.lower().startswith('!survey-info'):
			await poll_module.survey_fnc(client, message, 'info')

		if message.content.lower().startswith('!survey-list'):
			await poll_module.survey_fnc(client, message, 'list')

		if message.content.lower().startswith('!survey-open'):
			await poll_module.survey_fnc(client, message, 'open')

		if message.content.lower().startswith('!survey-results'):
			await poll_module.survey_fnc(client, message, 'results')

		if message.content.lower().startswith('!survey-submit'):
			await poll_module.survey_fnc(client, message, 'submit')

		if message.content.lower().startswith('!timetomissions'):
			await bot.time_to_missions(client, message)

		if message.content.lower().startswith('!timetoreset'):
			await bot.time_to_reset(client, message)

		if message.content.lower().startswith('!timetowvwreset'):
			await bot.time_to_wvw_reset(client, message)

		if message.content.lower().startswith('!vote '):
			await poll_module.poll_fnc(client, message, 'vote')

		if message.content.lower().startswith('!vote-admin'):
			await poll_module.poll_fnc(client, message, 'admin')

		if message.content.lower().startswith('!vote-change'):
			await poll_module.poll_fnc(client, message, 'change')

		if message.content.lower().startswith('!vote-remove'):
			await poll_module.poll_fnc(client, message, 'vote remove')

		if message.content.lower() == '!whatismyid':
			await bot.id_fnc(client, message, 'self')

		if message.content.lower().startswith('!wiki'):
			await bot.wiki(client, message)

		if message.content.lower().startswith('!trivia'):
			if bot.check_role(client, message, 'Admin') == True or bot.check_role(client, message, 'Trivia Admin') == True:
				await trivia_module.trivia_fncs(client, message)
			else:
				await client.send_message(message.channel, 'You do not have permission to do that.')

		if message.content.lower() == str(trivia.trivia_answer).lower():
			if message.channel.is_private == True:
				pass
			elif message.channel.name == 'trivia':
				await trivia_module.correct_answer(client, message)

		if '(╯°□°）╯︵ ┻━┻' in message.content:
			await client.send_message(message.channel, '┬─┬﻿ ノ( ゜-゜ノ) \n\n' +str(message.author.name) + ', what did the table do to you?')


@client.event
async def on_ready():
	print('Logged in as')
	print(client.user.name)
	print(client.user.id)
	print('------')
	global serv
	serv = discord.utils.find(lambda m: m.name == bot.server_name, client.servers)
	await remind_module.check(client)

#if not client.is_logged_in:
#	print('Logging in to Discord failed')
#	exit(1)

client.run(bot.get_bot_credential('Username'), bot.get_bot_credential('Password'))