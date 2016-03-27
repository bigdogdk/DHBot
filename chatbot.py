import datetime
from datetime import datetime
import asyncio
import json
import os
import requests
import time

import dice
import discord

class Chatbot(object):
	"""docstring for chatbot"""

	def __init__(self, settings_file):
		f = open(settings_file, 'r')
		settings = json.load(f)
		f.close()
		self.credential_location = settings["Credentials"]
		self.server_name = settings["Server Name"]
		self.event_text_file = settings["Events"]
		self.help_text_file = settings["Help"]
		self.mission_text_file = settings["Mission"]
		self.guild_id = settings["Guild ID"]
		self.api_key = settings["API Key"]
		self.away_list = settings["Away"]

	async def _weekly_event(self, event_day, event_hour, event_minute):
		"""
		This function computes the timedelta for events that occur weekly.
		event_day is an integer between 0 and 6, where 0 is monday and 6 is sunday.
		event_hour is an integer between 0 and 23
		event_minute is an integer between 0 and 59
		Provide these times in UTC
		event_time is a datetime object. The day is initially set to be the same as the current day.
		This value is then altered based on a comparison with event_day, due to the lack of 
		support for days of the week.
		"""
		now = datetime.datetime.utcnow()
		event_time = datetime.datetime(now.year, now.month, now.day, hour=event_hour, minute=event_minute)

		if event_day > now.weekday():
			x = event_day - now.weekday()
			event_time = event_time + datetime.timedelta(days=x)
			return (event_time - now)
		elif event_day < now.weekday():
			x = abs(event_day - now.weekday())
			event_time = event_time + datetime.timedelta(days=(7-x))
			return (event_time - now)
		elif event_day == now.weekday():
			if event_time.hour > now.hour:
				return (event_time - now)
			elif event_time.hour < now.hour:
				event_time = event_time + datetime.timedelta(days=7)
				return (event_time - now)
			elif event_time.hour == now.hour:
				if event_time.minute > now.minute:
					return (event_time - now)
				elif event_time.minute == now.minute or event_time.minute < now.minute:
					event_time = event_time + datetime.timedelta(days=7)
					return (event_time - now)
	
	async def _daily_event(self, event_hour, event_minute):
		""" Like weekly_event, but for an event that repeats daily """
		now = datetime.datetime.utcnow()
		event_time = datetime.datetime(now.year, now.month, now.day, hour=event_hour, minute=event_minute)

		if event_time > now:
			return (event_time - now)
		elif event_time == now or event_time < now:
			event_time = event_time + datetime.timedelta(days=1)
			return (event_time - now)

	async def away_fnc(self, client, message, query):
		f = open(self.away_list, 'r')
		away = json.load(f)
		f.close()

		if query == 'return':
			if message.author.name not in away:
				await client.send_message(message.channel, 'You are not currently set as away.')
			else:
				del away[message.author.name]
				await client.send_message(message.channel, "You are no longer set as away.")
				f = open(self.away_list, 'w')
				f.write(str(json.dumps(away)))
				f.close()

		if query == 'set':
			try:
				away_data = message.content.partition(' ')[2]
				account_name = away_data.partition('; ')[0]
				duration = int(away_data.partition('; ')[2])
			except:
				await client.send_message(message.channel, "There was an error processing your request. You may need to ensure the duration is an integer.")
			if message.author.name in away:
				await client.send_message(message.channel, 'You are already set as away.')
			else:
				away[message.author.name] = {"Account Name": account_name, "Away on": str(time.strftime("%d/%m/%Y")), "Duration": duration}
				f = open(self.away_list, 'w')
				f.write(str(json.dumps(away)))
				f.close()
				await client.send_message(message.channel, 'You have been set away for ' +str(duration) + ' days.')

		if query == 'whois':
			if self.check_role(client, message, 'Leadership') == False:
				await client.send_message(message.channel, "You do not have permission to view the away list.")
			else:
				with open(self.away_list, 'r') as f:
					json_away = json.load(f)
				formatted_away = 'Discord Name, GW2 Account Name, Date Set Away, Away Duration (in Days) \r\n'
				for x in sorted(json_away):
					formatted_away += "{}, {}, {}, {} \r\n".format(x, json_away[x]["Account Name"], json_away[x]["Away on"], json_away[x]["Duration"])
				with open('formatted_away.txt', 'w') as f:
					f.write(formatted_away)
				await client.send_message(message.author, 'Here is the requested file:')
				await client.send_file(message.author, 'formatted_away.txt')

	def check_name(self, client, member_name):
		cnt = 0
		serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
		for x in serv.members:
			if x.name == member_name:
				cnt += 1
		if cnt == 1:
			return 'Unique'
		if cnt > 1:
			return 'Multi'
		if cnt == 0:
			return 'None'

	def check_role(self, client, message_or_member, role_test):
		serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
		if isinstance(message_or_member, discord.message.Message) == True:
			msg = message_or_member
			mem = discord.utils.find(lambda m: m.id == msg.author.id, serv.members)
		elif isinstance(message_or_member, (discord.user.User)) == True:
			member = message_or_member
			mem = discord.utils.find(lambda m: m.id == member.id, serv.members)

		user_roles = []
		for x in mem.roles:
			user_roles.append(x.name)

		if role_test in user_roles:
			return True
		else:
			return False

	async def clear(self, client, message):
		if self.check_role(client, message, 'Admin') == True:
			split_message = message.content.split(' ', 2)
			chan_name = split_message[1]
			chan = discord.utils.find(lambda m: m.name == chan_name, message.channel.server.channels)
			message_list = []
			for x in client.logs_from(chan):
				message_list += [x]
			list_to_delete = message_list[0:int(split_message[2])]
			for x in list_to_delete:
				await client.delete_message(x)
		else:
			await client.send_message(message.channel, 'I can\'t let you do that, ' + message.author.name +'.')

	async def displayname(self, client, message, query):
		x = open("display_names.txt", 'r')
		disp_names = json.load(x)
		x.close()

		if query == 'self':
			if message.author.id in disp_names:
				await client.send_message(message.channel, "Your display name has alread been entered as {}. If this is not correct, please inform an Admin.".format(disp_names[message.author.id]))
			else:
				error_check = message.content.partition(' ')[2].partition('.')
				if len(error_check[2]) == 4:
					disp_names[message.author.id] = {"display name": message.content.partition(' ')[2], "verified": "n"}
					await client.send_message(message.channel, "Your display name has been entered as {}. If you made an error, please contact an Admin.".format(message.content.partition(' ')[2]))
				else:
					await client.send_message(message.channel, "Please ensure that you include the 4 digits at the end of your display name.")

		if query == 'send' and self.check_role(client, message, "Leadership") == True:
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			x = open('display_names.txt', 'r')
			display_names = json.load(x)
			x.close()
			member_list = ''
			for x in serv.members:
				if x.id in display_names:
					member_list += '{}, {}, {}, {}\r\n'.format(x.name, x.id, display_names[x.id]["display name"], display_names[x.id]["verified"])
				else:
					member_list += '{}, {}, N/A, n\r\n'.format(x.name, x.id)
			x = open ('discord_roster.txt', 'w')
			x.write(member_list)
			x.close()
			await client.send_file(message.author, 'discord_roster.txt')

		if query == 'set':
			if self.check_role(client, message, 'Admin') == True:
				discord_id = message.content.partition(' ')[2].partition('; ')[0]
				disp_name = message.content.partition(' ')[2].partition('; ')[2]
				error_check = disp_name.partition('.')
				if len(error_check[2]) == 4:
					serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
					member = discord.utils.find(lambda m: m.id == discord_id, serv.members)
					if member.id in disp_names:
						old_name = disp_names[member.id]["display name"]
					else:
						old_name = "N/A"
					disp_names[member.id] = {"display name": disp_name, "verified": "y"}
					await client.send_message(message.channel, "{} has changed {}'s display name from {} to {}.".format(message.author, member.name, old_name, disp_name))
				else:
					await client.send_message(message.channel, "Please ensure that you include the 4 digits at the end of your display name.")
			else:
				await client.send_message(message.channel, "You do not have permission to set display names.")

		if query == 'verify' and self.check_role(client, message, "Admin") == True:
			member_id = message.content.partition(' ')[2]
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			member = discord.utils.find(lambda m: m.id == discord_id, serv.members)
			if member_id in disp_names:
				disp_names[member_id]["verified"] = "yes"
				await client.send_message(message.channel, "{} has verified {}'s Display Name.".format(message.author.name, member.name))

		y = open("display_names.txt", 'w')
		y.write(str(json.dumps(disp_names)))
		y.close()

	async def file_interface(self, client, message, file_name, query):
		if file_name == 'events':
			location = self.event_text_file
		elif file_name == 'help':
			location = self.help_text_file

		if query == 'read':
			text_file = open(location, 'r')
			await client.send_message(message.channel, text_file.read())
			text_file.close()
		elif query == 'write':
			if self.check_role(client, message, 'Leadership') == True:
				text_file = open(location, 'w')
				new_text = message.content.partition(' ')[2]
				text_file.write(new_text)
				text_file.close()
				await client.send_message(message.channel, str(message.author) +' has updated the ' + str(file_name) + ' message.')
			else:
				await client.send_message(message.channel, 'You do not have permission to edit the ' + str(file_name) + ' message.')

	def get_bot_credential(self, credential):
		""" Extracts the paramater credential from a formatted text file """
		x = open(self.credential_location, 'r')
		bot_json = json.load(x)
		x.close()
		return bot_json[credential]

	async def group(self, client, message, query):
		#try:
			with open('groups.txt', 'r') as f:
				all_groups = json.load(f)

			if query == 'add' or query =='remove':
				if self.check_role(client, message, 'Leadership') == False:
					await client.send_message(message.channel, 'You do not have permission to add members to this group.')
				else:
					result_message = ''
					not_a_member = ''
					multiple_member = ''
					member_list = []
					group_info = message.content.partition(' ')[2].split('; ')
					group_names = group_info[0].lower().split(', ')
					member_names = group_info[1].split(', ')
					serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
					for x in member_names:
						try:
							member_query = int(x)
							member = discord.utils.find(lambda m: m.id == str(member_query), serv.members)
							if member != None:
								member_list += [member]
							else:
								not_a_member += '{}, '.format(x)
						except:
							member_query = x
							if self.check_name(client, member_query) == "None":
								not_a_member += '{}, '.format(x)
							if self.check_name(client, member_query) == "Multi":
								multiple_member += '{}, '.format(x)
							if self.check_name(client, member_query) == "Unique":
								member = discord.utils.find(lambda m: m.name == member_query, serv.members)
								member_list += [member]
					if not_a_member != '':
						result_message += 'The following are not members of this Discord server: {}\n'.format(not_a_member[:-2])
					if multiple_member != '':
						result_message += 'There are multiple members with the following names. Please use IDs: {}\n'.format(multiple_member[:-2])
					#try:
					if query == 'add':
						for x in group_names:
							already_in_list = ''
							added_list = ''
							for y in member_list:
								if y.id in all_groups[x]["members"]:
									already_in_list += '{}, '.format(y.name)
								else:
									all_groups[x]["members"] += [y.id]
									added_list += '{}, '.format(y.name)
							if already_in_list != '':
								result_message += 'The following members are already in the group {}: {}\n'.format(all_groups[x]["name"], already_in_list[:-2])
							if added_list != '':
								result_message += 'The following members were added to the group {}: {}\n'.format(all_groups[x]["name"], added_list[:-2])

					if query == 'remove':
						for x in group_names:
							not_in_list = ''
							removed_list = ''
							for y in member_list:
								if y.id in all_groups[x]["members"]:
									all_groups[x]["members"].remove(y.id)
									removed_list += '{}, '.format(y.name)
								else:
									not_in_list += '{}, '.format(y.name)
							if not_in_list != '':
								result_message += 'The following members are not in the group {}: {}\n'.format(all_groups[x]["name"], not_in_list[:-2])
							if removed_list != '':
								result_message += 'The following members were removed from the group {}: {}\n'.format(all_groups[x]["name"], removed_list[:-2])

					await client.send_message(message.channel, result_message)
					#except:
					#	pass

			if query == 'call':
				group_name = message.content.partition(' ')[2].lower()
				if group_name not in all_groups:
					await client.send_message(message.channel, "There is no group with that name.")
				else:
					mention_list = ''
					serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
					for x in all_groups[group_name]["members"]:
						user = discord.utils.find(lambda m: m.id == x, serv.members)
						if user == 'None':
							all_groups[group_name]["members"].remove(x)
							await client.send_message(message.channel, 'User ID {} was removed from the group {} because they are not a member of this server.'.format(x, all_groups[group_name]["name"]))
						else:
							mention_list += '<@'+x+'> '
					await client.send_message(message.channel, "{} has called the group {}:\n{}".format(message.author, all_groups[group_name]["name"], mention_list))

			if query == 'close':
				if self.check_role(client, message, 'Leadership') == False:
					client.send_message(message.channel, 'You do not have permission to do that.')
				else:
					group_name = message.content.partition(' ')[2].lower()
					if all_groups[group_name]["restriction"] == "closed":
						await client.send_message(message.channel, 'That group is already closed.')
					else:
						all_groups[group_name]["restriction"] = "closed"
						await client.send_message(message.channel, '{} is now a closed group.'.format(all_groups[group_name]["name"]))

			if query == 'create':
				if self.check_role(client, message, 'Leadership') == False:
					await client.send_message(message.channel, 'You do not have permission to create a group.')
				else:
					group_info = message.content.partition(' ')[2].split('; ')
					group_name = group_info[0]
					group_description = group_info[1]
					group_restriction = group_info[2].lower()
					all_groups[group_name.lower()] = {"name": group_name, "members": [], "description": group_description, "restriction": group_restriction}
					await client.send_message(message.channel, '{} has created the group {}.'.format(message.author.name, group_name))

			if query == 'delete':
				if self.check_role(client, message, 'Admin') == False:
					await client.send_message(message.channel, 'You do not have permission to delete a group.')
				else:
					group_name = message.content.partition(' ')[2].lower()
					group_Name = all_groups[group_name]["name"]
					del all_groups[group_name]
					await client.send_message(message.channel, '{} has deleted the group {}.'.format(message.author.name, group_Name))

			if query == 'enroll':
				group_names = message.content.partition(' ')[2].lower().split(', ')
				closed_list = ''
				already_in_list = ''
				added_list = ''
				for x in group_names:
					if all_groups[x]["restriction"] == 'closed':
						closed_list += '{}, '.format(all_groups[x]["name"])
					elif message.author.id in all_groups[x]["members"]:
						already_in_list += '{}, '.format(all_groups[x]["name"])
					else:
						all_groups[x]["members"] += [message.author.id]
						added_list += '{}, '.format(all_groups[x]["name"])
				if closed_list != '':
					closed_list = closed_list[:-2]
					await client.send_message(message.channel, 'You will need a member of Leadership to add you to the group(s): {}.'.format(closed_list))
				if already_in_list != '':
					already_in_list = already_in_list[:-2]	
					await client.send_message(message.channel, "You are already a member of the group(s): {}.".format(already_in_list))
				if added_list != '':
					added_list = added_list[:-2]	
					await client.send_message(message.channel, "You have been added to the group(s): {}.".format(added_list))

			if query == 'info':
				group_name = group_name = message.content.partition(' ')[2].lower()
				await client.send_message(message.channel, "{}: {}".format(all_groups[group_name]["name"], all_groups[group_name]["description"]))

			if query == 'list':
				group_list = ''
				for x in sorted(all_groups):
					group_list += '{}: {}\n'.format(all_groups[x]["name"], all_groups[x]["description"])
				await client.send_message(message.channel, "The following is a list of available groups and their descriptions:")
				await client.send_message(message.channel, group_list)

			if query == 'members':
				member_list = []
				group_name = group_name = message.content.partition(' ')[2].lower()
				for x in all_groups[group_name]["members"]:
					serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
					mem = discord.utils.find(lambda m: m.id == x, serv.members)
					member_list += [mem.name]
				member_list_text = ''
				for x in sorted(member_list):
					member_list_text += '{}, '.format(x)
				member_list_text = member_list_text[:-2]
				await client.send_message(message.channel, 'The following is a list of members of the group {}:\n{}'.format(all_groups[group_name]["name"], member_list_text))

			if query == 'mine':
				group_list = ''
				for x in all_groups:
					if message.author.id in all_groups[x]["members"]:
						group_list += '{}, '.format(all_groups[x]["name"])
				group_list = group_list[:-2]
				await client.send_message(message.channel, "These are the groups {} is currently a member of:\n{}".format(message.author, group_list))

			if query == 'open':
				if self.check_role(client, message, 'Leadership') == False:
					client.send_message(message.channel, 'You do not have permission to do that.')
				else:
					group_name = message.content.partition(' ')[2].lower()
					if all_groups[group_name]["restriction"] == "open":
						await client.send_message(message.channel, 'That group is already open.')
					else:
						all_groups[group_name]["restriction"] = "open"
						await client.send_message(message.channel, '{} is now an open group.'.format(all_groups[group_name]["name"]))

			if query == 'remove all':
				if self.check_role(client, message, 'Leadership') == False:
					await client.send_message(message.channel, 'You do not have permission to add members to this group.')
				else:
					serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
					try:
						member_query = int(message.content.partition(' ')[2])
						member = discord.utils.find(lambda m: m.id == str(member_query), serv.members)
					except:
						member_query = message.content.partition(' ')[2]
						if self.check_name(client, member_query) == "None":
							await client.send_message(message.channel, "There is no member with the name {}.".format(member_query))
						if self.check_name(client, member_query) == "Multi":
							await client.send_message(message.channel, "There is more than one member with the name {}. Please use their Discord ID.".format(member_query))
						if self.check_name(client, member_query) == "Unique":
							member = discord.utils.find(lambda m: m.name == member_query, serv.members)
					try:
						group_list = ''
						for x in all_groups:
							if member.id in all_groups[x]["members"]:
								all_groups[x]["members"].remove(member.id)
								group_list += "{}, ".format(all_groups[x]["name"])
						group_list = group_list[:-2]
						await client.send_message(message.channel, "{} has removed {} from the following groups:\n{}".format(message.author, member.name, group_list))
					except:
						pass

			if query == 'unenroll':
				group_name = message.content.partition(' ')[2].lower()
				if message.author.id in all_groups[group_name]["members"]:
					all_groups[group_name]["members"].remove(message.author.id)
					await client.send_message(message.channel, "You have been removed from the group {}.".format(all_groups[group_name]["name"]))
				else:
					await client.send_message(message.channel, "You are not a member of that group.")

			with open('groups.txt', 'w') as f:
				f.write(str(json.dumps(all_groups)))
		#except:
		#	await client.send_message(message.channel, "There was an error processing your request.")

	async def greet(self, client, message):
		await client.send_message(message.channel, 'Howdy {}!'.format(message.author.mention))

	async def id_fnc(self, client, message, query):
		if query =='other' and self.check_role(client, message, "Leadership") == True:
			name = message.content.partition(' ')[2]
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			for x in serv.members:
				if x.name == name:
					await client.send_message(message.author, "The ID for {} is {} who joined on {}".format(x.name, x.id, x.joined_at))

		if query == 'self':
			await client.send_message(message.channel, 'Your Discord ID is: {}'.format(message.author.id))

	async def help(self, client, message, query):
		f = open(self.help_text_file, 'r')
		help_file = json.load(f)
		f.close()

		if query == 'admin':
			help_list = ''
			for x in sorted(help_file["Admin Commands"]):
				help_list += x + '\n'
			await client.send_message(message.channel, 'The following is a list of commands that are usable by Admins. For more information about a specific command, please type \"!help <command>\".\n\n' + help_list)

		if query == 'info':
			help_query = message.content.partition(' ')[2]
			await client.send_message(message.channel, help_file[help_query])

		if query == 'read':
			help_list = ''
			for x in sorted(help_file["Commands"]):
				help_list += x + '\n'
			await client.send_message(message.channel, 'The following is a list of commands that I understand. For more information about a specific command, please type \"!help <command>\".\n\n' + help_list)

		if self.check_role(client, message, 'Admin'):
			if query == 'add':
				help_msg = message.content.partition(' ')[2].partition('; ')
				help_name = help_msg[0]
				help_text = help_msg[2]
				if help_name not in help_file["Commands"]:
					help_file["Commands"].append(help_name)
					help_file[help_name] = help_text
					await client.send_message(message.channel, 'The help entry for ' +help_name + ' has been created.')
				else:
					await client.send_message(message.channel, 'That help entry already exists. Please use !edit-help instead.')

			if query == 'add-admin':
				help_msg = message.content.partition(' ')[2].partition('; ')
				help_name = help_msg[0]
				help_text = help_msg[2]
				if help_name not in help_file["Admin Commands"]:
					help_file["Admin Commands"].append(help_name)
					help_file[help_name] = help_text
					await client.send_message(message.channel, 'The help entry for ' +help_name + ' has been created.')
				else:
					await client.send_message(message.channel, 'That help entry already exists. Please use !edit-help instead.')

			if query == 'delete':
				help_name = message.content.partition(' ')[2]
				if help_name in help_file["Commands"]:
					help_file["Commands"].remove(help_name)
					del help_file[help_name]
					await client.send_message(message.channel, 'The help entry for ' +help_name + ' has been deleted.')
				else:
					await client.send_message(message.channel, 'There is no help entry by that name.')

			if query == 'delete-admin':
				help_name = message.content.partition(' ')[2]
				if help_name in help_file["Admin Commands"]:
					help_file["Admin Commands"].remove(help_name)
					del help_file[help_name]
					await client.send_message(message.channel, 'The help entry for ' +help_name + ' has been deleted.')
				else:
					await client.send_message(message.channel, 'There is no help entry by that name.')
			if query == 'edit':
				help_msg = message.content.partition(' ')[2].partition('; ')
				help_name = help_msg[0]
				help_text = help_msg[2]
				if help_name in help_file["Commands"] or help_name in help_file["Admin Commands"]:
					help_file[help_name] = help_text
					await client.send_message(message.channel, 'The information for ' +help_name + ' has been edited.')
				else:
					await client.send_message(message.channel, 'There is no help entry for ' + help_name +'. Please use !add-help or !add-adminhelp to create it.')

		f = open(self.help_text_file, 'w')
		f.write(str(json.dumps(help_file)))
		f.close()

	async def lmgtfy(self, client, message):
		search = message.content.partition(' ')[2].replace(' ','+')
		await client.send_message(message.channel, 'http://lmgtfy.com/?q='+search)
	
	def log_fnc(self, member, query):
		try:
			with open ('discord_logs.txt', 'r') as f:
				discord_logs = json.load(f)
		except:
			discord_logs = {}

		if query == 'last on':
			if str(member.status) == 'online':
				return 'now'
			else:
				try:
					last_login = datetime.strptime(discord_logs[member.id]['last login'], '%Y-%m-%d %H:%M:%S.%f')
					last_logoff = datetime.strptime(discord_logs[member.id]['last logoff'], '%Y-%m-%d %H:%M:%S.%f')
					if last_login > last_logoff:
						return last_login
					else:
						return last_logoff
				except:
					return 'before tracking'

	def member_lookup(self, client, id_or_name, serv):
		try:
			member = discord.utils.find(lambda m: m.id == str(int(id_or_name)), serv.members)
			return member
		except:
			if self.check_name(client, id_or_name) == 'None' or self.check_name(client, id_or_name) == 'Multi':
				return None
			else:
				member = discord.utils.find(lambda m: m.name == id_or_name, serv.members)
				return member
		
	def log_fnc(self, member, query):
		try:
			with open ('discord_logs.txt', 'r') as f:
				discord_logs = json.load(f)
		except:
			discord_logs = {}

		if query == 'last on':
			if str(member.status) == 'online':
				return 'now'
			else:
				try:
					last_login = datetime.strptime(discord_logs[member.id]['last login'], '%Y-%m-%d %H:%M:%S.%f')
					last_logoff = datetime.strptime(discord_logs[member.id]['last logoff'], '%Y-%m-%d %H:%M:%S.%f')
					if last_login > last_logoff:
						return last_login
					else:
						return last_logoff
				except:
					return 'before tracking'

	def member_lookup(self, client, id_or_name, serv):
		try:
			member = discord.utils.find(lambda m: m.id == str(int(id_or_name)), serv.members)
			return member
		except:
			if self.check_name(client, id_or_name) == 'None' or self.check_name(client, id_or_name) == 'Multi':
				return None
			else:
				member = discord.utils.find(lambda m: m.name == id_or_name, serv.members)
				return member

	async def mission(self, client, message, query):
		try:
			with open('mission.txt', 'r') as f:
				mission_data = json.load(f)
		except:
			mission_data = {}
		mission_list = []

		if query == 'add' and self.check_role(client, message, "Leadership") == True:
			try:
				mission_name = message.content.partition(' ')[2].partition('; ')[0]
				for x in mission_data:
					mission_list += [str(x).lower()]
				if mission_name.lower() in mission_list:
					await client.send_message(message.channel, "There is already a mission entry with that name.")
				else:
					mission_details = message.content.partition(' ')[2].partition('; ')[2]
					mission_data[mission_name] = mission_details
					await client.send_message(message.channel, "{} has created the mission entry for {}.".format(message.author.name, mission_name))
			except:
				await client.send_message(message.channel, "There was an error processing your request.")

		if query == 'delete' and self.check_role(client, message, "Leadership") == True:
			try:
				mission_name = message.content.partition(' ')[2].lower()
				for x in mission_data:
					mission_list += [str(x).lower()]
					if str(x).lower() == mission_name:
						del mission_data[mission_name]
						await client.send_message(message.channel, "{} has removed the mission entry {}.".format(message.author.name, mission_name))
				if mission_name not in mission_list:
					await client.send_message(message.channel, "There is no mission with that name.")
			except:
				await client.send_message(message.channel, "There was an error processing your request.")

		if query == 'edit' and self.check_role(client, message, "Leadership") == True:
			try:
				mission_name = message.content.partition(' ')[2].partition('; ')[0].lower()
				for x in mission_data:
					mission_list += [str(x).lower()]
					if mission_name == str(x).lower():
						mission_details = message.content.partition(' ')[2].partition('; ')[2]
						mission_data[x] = mission_details
						await client.send_message(message.channel, "{} has edited the mission entry for {}.".format(message.author.name, x))
				if mission_name not in mission_list:
					await client.send_message(message.channel, "There is no mission entry with that name. Please use `!mission-add <name>; <description>`")
			except:
				await client.send_message(message.channel, "There was an error processing your request.")

		if query == 'info':
			mission = message.content.lower().partition(' ' )[2]
			for x in mission_data:
				mission_list += [str(x).lower()]
				if str(x).lower() == mission:
					await client.send_message(message.channel, mission_data[x])
			if mission not in mission_list:
				await client.send_message(message.channel, 'There is no mission with that name.')

		if query == 'list':
			mission_list = ''
			for x in sorted(mission_data):
				mission_list += '{}, '.format(x)
			mission_list = mission_list[:-2]
			await client.send_message(message.channel, 'The following is a list of missions with availalble information:\n{}'.format(mission_list))

		if query == 'add' or query == 'delete' or query =='edit':
			with open("mission.txt", 'w') as f:
				f.write(str(json.dumps(mission_data)))

	async def play(self, client, message, serv):
		if self.check_role(client, message, "Admin") == True:
			channel = message.author.voice_channel
			voice = await client.join_voice_channel(channel)
			sound_clip = message.content.lower().partition(' ')[2]
			if sound_clip == 'sadtrombone':
				player = voice.create_ffmpeg_player('sounds/sad_trombone.mp3')
			player.start()
			await asyncio.sleep(4)
			player.stop()
			await voice.disconnect()

	async def price(self, client, message):
		try:
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
			await client.send_message(message.channel, 'The current buy price of ' +item_name +' is ' +str(bgold).zfill(2) +'g ' +str(bsilver).zfill(2)+ 's ' +str(bcopper).zfill(2)+ 'c. \nThe current sell price is ' +str(sgold).zfill(2) +'g ' +str(ssilver).zfill(2)+ 's ' +str(scopper).zfill(2)+ 'c.')
		except:
			await client.send_message(message.channel, 'There was an error processing your request.')

	async def purge(self, client, message):
		if self.check_role(client, message, 'Admin') == True:
			split_message = message.content.split(' ', 2)
			user_name = split_message[1]
			user = discord.utils.find(lambda m: m.name == user_name, message.channel.server.members)
			message_list = []
			for x in client.logs_from(message.channel):
				if x.author.name == user.name:
					message_list += [x]
			list_to_delete = message_list[0:int(split_message[2])]
			for x in list_to_delete:
				await client.delete_message(x)
		else:
			await client.send_message(message.channel, 'I can\'t let you do that, ' +message.author.name)

	async def role_fnc(self, client, sender, channel, member_id_or_name, role_names, query):
		if self.check_role(client, sender, 'Admin') == False and self.check_role(client, sender, 'Bot') == False:
			await client.send_message(channel, "You do not have permission to do that.")
		else:
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			try:
				member_id = int(member_id_or_name)
				member = discord.utils.find(lambda m: m.id == str(member_id), serv.members)
			except:
				member_name = member_id_or_name
				if self.check_name(client, member_name) == "None":
					await client.send_message(channel, "There is no user with that name.")
					member == None
				if self.check_name(client, member_name) == "Multi":
					await client.send_message(channel, "There is no user with that name.")
					member == None
				if self.check_name(client, member_name) == "Unique":
					member = discord.utils.find(lambda m: m.name == member_name, serv.members)
			if member != None:
				role_list = []
				non_role = ''
				role_name_text = ''
				for x in role_names:
					role = discord.utils.find(lambda m: m.name == x, serv.roles)
					if role == None:
						non_role += '{}, '.format(x)
					else:
						role_list += [role]
						role_name_text += '{}, '.format(role.name)
				non_role = non_role[:-2]
				role_name_text = role_name_text[:-2]
				if non_role != '':
					await client.send_message(channel, 'The following roles were not recognized: {}'.format(non_role))
				
				if query == 'assign':
					await client.add_roles(member, *role_list)
					await client.send_message(channel, '{} has assigned the role(s) {} to {}.'.format(sender.name, role_name_text, member.name))

				if query == 'remove':
					await client.remove_roles(member, *role_list)
					await client.send_message(channel, '{} has removed the role(s) {} from {}.'.format(sender.name, role_name_text, member.name))

	async def roll_dice(self, client, message):
		droll = message.content.partition(' ')[2]
		clean = droll.split('d')
		if 0 < int(clean[0]) < 51 and 0 < int(clean[1]) < 1001:
			await client.send_message(message.channel, str(dice.roll(droll)))
		else:
			await client.send_message(message.channel, 'Not an appropriate amount or size of dice.')

	async def roster_fnc(self, client, message, query):
		if self.check_role(client, message, 'Leadership') == False:
			await client.send_message(message.channel, 'You do not have permission to use the roster functions.')

		elif query == 'copy':
			response = requests.get("https://api.guildwars2.com/v2/guild/"+ self.guild_id +"/members?access_token="+ self.api_key)
			full_roster = json.loads(response.text)
			with open('display_names.txt', 'r') as f:
				display_names = json.load(f)
			json_roster = {}
			formatted_roster = ''
			for x in full_roster:
				if str(x["joined"]) == "None":
					join_date = "None"
				else:
					join_data = x["joined"].partition('T')[0]
					join_year = join_data.split('-')[0]
					join_month = join_data.split('-')[1]
					join_day = join_data.split('-')[2]
					join_date = datetime(int(join_year), int(join_month), int(join_day)).strftime('%y-%m-%d')
				json_roster[x["name"]] = {"name": x["name"], "rank": x["rank"], "joined": join_date, "discord id": "N/A", "discord name": "N/A", "roles": "N/A"}
				for y in display_names:
					if str(display_names[y]["display name"]) == str(x["name"]):
						serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
						member = discord.utils.find(lambda m: m.id == str(y), serv.members)
						if member != None:
							json_roster[x["name"]]["discord id"] = member.id
							json_roster[x["name"]]["discord name"] = member.name
							role_list = ''
							for z in member.roles:
								role_list += '{}; '.format(z.name)
							role_list = role_list[:-2]
							json_roster[x["name"]]["roles"] = role_list
			for y in sorted(json_roster):
				formatted_roster += '{}, {}, {}, {}, {}, {}\r\n'.format(y, json_roster[y]["rank"],str(json_roster[y]["joined"]), json_roster[y]["discord id"], json_roster[y]["discord name"], json_roster[y]["roles"])
			with open('formatted_roster.txt', 'w') as g:
				g.write(formatted_roster)
			await client.send_message(message.author, 'Here is the updated copy of the guild roster.')
			await client.send_file(message.author, 'formatted_roster.txt')

		elif query == 'promotion':
			response = requests.get("https://api.guildwars2.com/v2/guild/"+ self.guild_id +"/members?access_token="+ self.api_key)
			full_roster = json.loads(response.text)
			json_roster = {}
			for x in full_roster:
				json_roster[x["name"]] = {"rank": x["rank"], "joined": x["joined"]}
			app_squire_list = {}
			promotion_list = {}
			formatted_promotion = ''
			for x in json_roster:
				if json_roster[x]['rank'] == 'Squire' or json_roster[x]['rank'] == 'Applicant':
					app_squire_list[x] = json_roster[x]
			with open('app_squire_list.txt', 'w') as f:
				f.write(str(json.dumps(app_squire_list)))
			for x in app_squire_list:
				join_data = app_squire_list[x]['joined'].partition('T')[0]
				join_year = join_data.split('-')[0]
				join_month = join_data.split('-')[1]
				join_day = join_data.split('-')[2]
				join_date = datetime(int(join_year), int(join_month), int(join_day))
				current_time = datetime.now()
				current_date = datetime(current_time.year, current_time.month, current_time.day)
				days_passed = (current_date - join_date).days
				if app_squire_list[x]['rank'] == 'Applicant' and days_passed > 30:
					promotion_list[x] = app_squire_list[x]
					promotion_list[x]['days passed'] = days_passed
				elif app_squire_list[x]['rank'] == 'Squire' and days_passed > 60:
					promotion_list[x] = app_squire_list[x]
					promotion_list[x]['days passed'] = days_passed
			for x in sorted(promotion_list):
				formatted_promotion += x + ', ' + promotion_list[x]["rank"] + ', ' + str(promotion_list[x]["joined"].partition('T')[0]) + ', ' + str(promotion_list[x]["days passed"]) + '\r\n'
			with open('promotion_list.txt', 'w') as f:
				f.write(formatted_promotion)
			await client.send_message(message.author, 'Here is the updated copy of the promotion list.')
			await client.send_file(message.author, 'promotion_list.txt')

		elif query == 'send':
			raw_time = os.path.getmtime('formatted_roster.txt')
			mod_time = datetime.fromtimestamp(raw_time)
			await client.send_message(message.author, 'Here is the most recent roster, generated on {}. If you need a more up-to-date copy, please use !roster-formattedcopy.'.format(mod_time))
			await client.send_file(message.author, 'formatted_roster.txt')

		elif query == 'send promotion':
			await client.send_message(message.author, 'Here is the most recent list of potential promotions, generated on {}. If you need a more up-to-date copy, please use !roster-promotion.'.format(datetime.fromtimestamp(os.path.getmtime('promotion_list.txt'))))
			await client.send_file(message.author, 'promotion_list.txt')

		elif query == 'send specified':
			fields = message.content.partition(' ')[2].split(', ')
			response = requests.get("https://api.guildwars2.com/v2/guild/"+ self.guild_id +"/members?access_token="+ self.api_key)
			full_roster = json.loads(response.text)
			with open('display_names.txt', 'r') as f:
				display_names = json.load(f)
			json_roster = {}
			specified_roster = ''
			for x in full_roster:
				json_roster[x["name"]] = {"name": x["name"], "rank": x["rank"], "joined": x["joined"], "discord id": "N/A", "discord name": "N/A", "roles": "N/A"}
				for y in display_names:
					if str(display_names[y]["display name"]) == str(x["name"]):
						serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
						member = discord.utils.find(lambda m: m.id == str(y), serv.members)
						if member != None:
							json_roster[x["name"]]["discord id"] = member.id
							json_roster[x["name"]]["discord name"] = member.name
							json_roster[x["name"]]["roles"] = member.roles
			for y in sorted(json_roster):
				specified_roster += '{}, '.format(y)
				for x in fields:
					specified_roster += '{}, '.format(json_roster[y][x])
				specified_roster = specified_roster[:-2] + "\r\n"
			with open('specified_roster.txt', 'w') as g:
				g.write(specified_roster)
			with open('test.txt', 'w') as g:
				g.write(test_string)
			await client.send_message(message.author, 'Here is the updated copy of the guild roster with the fields you asked for.')
			await client.send_file(message.author, 'specified_roster.txt')
			await client.send_file(message.author, 'test.txt')

	async def stop_bot(self, client, message):
		if self.check_role(client, message, 'BotManager') == True:
			client.logout()
		else:
			await client.send_message(message.channel, 'You do not have permission to stop DHBot.')

	async def time_to_missions(self, client, message):
		mission_time_delta = self._weekly_event(6, 1, 10)
		m, s = divmod(mission_time_delta.seconds, 60)
		h, m = divmod(m, 60)
		await client.send_message(message.channel, 'Time remaining until guild missions: ' +str(mission_time_delta.days) + ' days ' + str(h) + ' hours ' + str(m) + ' minutes ' + str(s) + ' seconds.\n Meet in Queensdale!')

	async def time_to_reset(self, client, message):
		reset_time_delta = self._daily_event(0, 0)
		m, s = divmod(reset_time_delta.seconds, 60)
		h, m = divmod(m, 60)
		await client.send_message(message.channel, 'Time remaining until reset: ' + str(h) + ' hours ' + str(m) + ' minutes ' + str(s) + ' seconds.')

	async def time_to_wvw_reset(self, client, message):
		wvw_time_delta = self._weekly_event(5, 0, 0)
		m, s = divmod(wvw_time_delta.seconds, 60)
		h, m = divmod(m, 60)
		await client.send_message(message.channel, 'Time remaining until WvW reset: ' + str(wvw_time_delta.days) + ' days ' + str(h) + ' hours ' + str(m) + ' minutes ' + str(s) + ' seconds.')

	async def wiki(self, client, message):
		search = message.content.partition(' ')[2].replace(' ', '_')
		await client.send_message(message.channel, 'http://wiki.guildwars2.com/wiki/Special:Search/'+search)