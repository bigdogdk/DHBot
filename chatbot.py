import datetime
from datetime import datetime
import json
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

		if query == 'return':
			if message.author.name not in away:
				await client.send_message(message.channel, 'You are not currently set as away.')
			else:
				del away[message.author.name]
				await client.send_message(message.channel, "You are no longer set as away.")
				f = open(self.away_list, 'w')
				f.write(str(json.dumps(away)))
				f.close()

		if query == 'whois':
			if self.check_role(client, message, 'Admin') == False and self.check_role(client, message, 'Leadership') == False:
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
			if self.check_role(client, message, 'Admin') == True:
				text_file = open(location, 'w')
				new_text = message.content.partition(' ')[2]
				text_file.write(new_text)
				text_file.close()
				await client.send_message(message.channel, str(message.author) +' has updated the ' + str(file_name) + ' message.')
			else:
				await client.send_message(message.channel, 'You do not have permission to edit the ' + str(file_name) + ' message.')

	async def help(self, client, message, query):
		f = open(self.help_text_file, 'r')
		help_file = json.load(f)
		f.close()

		if query == 'read':
			help_list = ''
			for x in sorted(help_file["Commands"]):
				help_list += x + '\n'
			await client.send_message(message.channel, 'The following is a list of commands that I understand. For more information about a specific command, please type \"!help <command>\".\n\n' + help_list)

		if query == 'admin':
			help_list = ''
			for x in sorted(help_file["Admin Commands"]):
				help_list += x + '\n'
			await client.send_message(message.channel, 'The following is a list of commands that are usable by Admins. For more information about a specific command, please type \"!help <command>\".\n\n' + help_list)

		if query == 'info':
			help_query = message.content.partition(' ')[2]
			await client.send_message(message.channel, help_file[help_query])

		if self.check_role(client, message, 'Admin'):
			if query == 'edit':
				help_msg = message.content.partition(' ')[2].partition('; ')
				help_name = help_msg[0]
				help_text = help_msg[2]
				if help_name in help_file["Commands"] or help_name in help_file["Admin Commands"]:
					help_file[help_name] = help_text
					await client.send_message(message.channel, 'The information for ' +help_name + ' has been edited.')
				else:
					await client.send_message(message.channel, 'There is no help entry for ' + help_name +'. Please use !add-help or !add-adminhelp to create it.')

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

		f = open(self.help_text_file, 'w')
		f.write(str(json.dumps(help_file)))
		f.close()

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
				if len(error_check) == 4:
					disp_names[message.author.id] = message.content.partition(' ')[2]
					await client.send_message(message.channel, "Your display name has been entered as {}. If you made an error, please contact an Admin.")
				else:
					await client.send_message(message.channel, "Please ensure that you include the 4 digits at the end of your display name.")

		if query == 'send':
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			x = open('display_names.txt', 'r')
			display_names = json.load(x)
			x.close()
			member_list = ''
			for x in serv.members:
				if self.check_role(client, x, "Member") == True:
					if x.id in display_names:
						member_list += '{}, {}, {}\r\n'.format(x.name, x.id, display_names[x.id])
					else:
						member_list += '{}, {}, N/A\r\n'.format(x.name, x.id)
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
						old_name = disp_names[member.id]
					else:
						old_name = "N/A"
					disp_names[member.id] = disp_name
					await client.send_message(message.channel, "{} has changed {}'s display name from {} to {}.".format(message.author, member.name, old_name, disp_name))
				else:
					await client.send_message(message.channel, "Please ensure that you include the 4 digits at the end of your display name.")
			else:
				await client.send_message(message.channel, "You do not have permission to set display names.")

		y = open("display_names.txt", 'w')
		y.write(str(json.dumps(disp_names)))
		y.close()

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
				group_name = message.content.partition(' ')[2].lower()
				if all_groups[group_name]["restriction"] == 'closed':
					await client.send_message(message.channel, 'You will need a member of Leadership to add you to that list.')
				elif message.author.id in all_groups[group_name]["members"]:
					await client.send_message(message.channel, "You are already a member of that group.")
				else:
					all_groups[group_name]["members"] += [message.author.id]
					await client.send_message(message.channel, "You have been added to the {} group.".format(all_groups[group_name]["name"]))

			if query == 'add' or query =='remove':
				group_info = message.content.partition(' ')[2].split('; ')
				group_name = group_info[0].lower()
				member_name = group_info[1]
				serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
				if self.check_role(client, message, 'Leadership') == False:
					await client.send_message(message.channel, 'You do not have permission to add members to this group.')
				else:
					cnt = 0
					for x in serv.members:
						if x.name == member_name:
							cnt += 1

					if cnt == 0:
						await client.send_message(message.channel, "There is no member with the name {}.".format(member_name))
					if cnt > 1:
						await client.send_message(message.channel, "There is more than one member with the name {}. Please use their Discord ID.".format(member_name))
					if cnt == 1:
						member = discord.utils.find(lambda m: m.name == member_name, serv.members)

						if query == 'add':
							if member.id in all_groups[group_name]["members"]:
								await client.send_message(message.channel, "{} is already a member of that group.".format(member_name))
							else:
								all_groups[group_name]["members"] += [member.id]
								await client.send_message(message.channel, "{} has added {} to the group {}.".format(message.author.name, member_name, all_groups[group_name]["name"]))

						if query == 'remove':
							if member.id in all_groups[group_name]["members"]:
								all_groups[group_name]["members"].remove(member.id)
								await client.send_message(message.channel, "{} has removed {} from the group {}.".format(message.author.name, member.name, all_groups[group_name]["name"]))
							else:
								await client.send_message(message.channel, "{} is not a member of that group.".format(member.name))


			if query == 'add_id' or query == 'remove_id':
				group_info = message.content.partition(' ')[2].split('; ')
				group_name = group_info[0].lower()
				member_id = group_info[1]
				serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
				member = discord.utils.find(lambda m: m.id == member_id, serv.members)
				if self.check_role(client, message, 'Leadership') == False:
					await client.send_message(message.channel, 'You do not have permission to add members to this group.')

				if query == 'add_id':
					if member.id in all_groups[group_name]["members"]:
						await client.send_message(message.channel, "{} is already a member of that group.".format(member.name))
					else:
						all_groups[group_name]["members"] += [member.id]
						await client.send_message(message.channel, "{} has added {} to the group {}.".format(message.author.name, member.name, all_groups[group_name]["name"]))

				if query == 'remove_id':
					if member.id in all_groups[group_name]["members"]:
						all_groups[group_name]["members"].remove(member.id)
						await client.send_message(message.channel, "{} has removed {} from the group {}.".format(message.author.name, member.name, all_groups[group_name]["name"]))
					else:
						await client.send_message(message.channel, "{} is not a member of that group.".format(member.name))

			if query == 'open':
				if self.check_role(client, message, 'Admin') == False:
					client.send_message(message.channel, 'You do not have permission to do that.')
				else:
					group_name = message.content.partition(' ')[2].lower()
					if all_groups[group_name]["restriction"] == "open":
						await client.send_message(message.channel, 'That group is already open.')
					else:
						all_groups[group_name]["restriction"] = "open"
						await client.send_message(message.channel, '{} is now an open group.'.format(all_groups[group_name]["name"]))

			if query == 'close':
				if self.check_role(client, message, 'Admin') == False:
					client.send_message(message.channel, 'You do not have permission to do that.')
				else:
					group_name = message.content.partition(' ')[2].lower()
					if all_groups[group_name]["restriction"] == "closed":
						await client.send_message(message.channel, 'That group is already closed.')
					else:
						all_groups[group_name]["restriction"] = "closed"
						await client.send_message(message.channel, '{} is now a closed group.'.format(all_groups[group_name]["name"]))

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

			if query == 'unenroll':
				group_name = message.content.partition(' ')[2].lower()
				if message.author.id in all_groups[group_name]["members"]:
					all_groups[group_name]["members"].remove(message.author.id)
					await client.send_message(message.channel, "You have been removed from the group {}.".format(all_groups[group_name]["name"]))
				else:
					await client.send_message(message.channel, "You are not a member of that group.")

			if query == 'list':
				group_list = ''
				for x in sorted(all_groups):
					group_list += '{}: {}\n'.format(all_groups[x]["name"], all_groups[x]["description"])
				await client.send_message(message.channel, "The following is a list of available groups and their descriptions:")
				await client.send_message(message.channel, group_list)

			if query == 'members':
				member_list = ''
				group_name = group_name = message.content.partition(' ')[2].lower()
				for x in sorted(all_groups[group_name]["members"]):
					member_list += '{}, '.format(x)
				member_list = member_list[:-2]
				await client.send_message(message.channel, 'The following is a list of members of the group {}:\n{}'.format(all_groups[group_name]["name"], member_list))

			if query == 'info':
				group_name = group_name = message.content.partition(' ')[2].lower()
				await client.send_message(message.channel, "{}: {}".format(all_groups[group_name]["name"], all_groups[group_name]["description"]))

			with open('groups.txt', 'w') as f:
				f.write(str(json.dumps(all_groups)))
		#except:
		#	await client.send_message(message.channel, "There was an error processing your request.")

	async def greet(self, client, message):
		await client.send_message(message.channel, 'Howdy {}!'.format(message.author.mention))

	async def id_fnc(self, client, message, query):
		if query == 'self':
			await client.send_message(message.channel, 'Your Discord ID is: {}'.format(message.author.id))

		if query =='other':
			name = message.content.partition(' ')[2]
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			for x in serv.members:
				if x.name == name:
					await client.send_message(message.author, "The ID for {} is {}".format(x.name, x.id))

	async def lmgtfy(self, client, message):
		search = message.content.partition(' ')[2].replace(' ','+')
		await client.send_message(message.channel, 'http://lmgtfy.com/?q='+search)

	async def mission(self, client, message):
		mission = message.content.partition(' ' )[2]
		with open('mission.txt', 'r') as f:
			mission_data = json.load(f)
		await client.send_message(message.channel, mission_data[mission])	

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
			json_roster = {}
			for x in full_roster:
				json_roster[x["name"]] = {"rank": x["rank"], "joined": x["joined"]}
			with open('jsonroster.txt', 'w') as g:
				g.write(str(json.dumps(json_roster)))
			await client.send_message(message.channel, 'Roster successfully created.')

		elif query == 'format':
			response = requests.get("https://api.guildwars2.com/v2/guild/"+ self.guild_id +"/members?access_token="+ self.api_key)
			full_roster = json.loads(response.text)
			json_roster = {}
			formatted_roster = ''
			for x in full_roster:
				json_roster[x["name"]] = {"name": x["name"], "rank": x["rank"], "joined": x["joined"]}
			for y in sorted(json_roster):
				formatted_roster += y + ', ' + json_roster[y]["rank"] + ', ' + str(json_roster[y]["joined"]) + '\r\n'
			with open('formattedroster.txt', 'w') as g:
				g.write(formatted_roster)
			await client.send_message(message.channel, 'Roster successfully created.')

		elif query == 'promotion':
			with open('jsonroster.txt', 'r') as f:
				json_roster = json.load(f)
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
			await client.send_message(message.channel, 'The list of potential promotionss based on join date has been updated.')

		elif query == 'send':
			await client.send_message(message.author, 'Here is the requested file:')
			await client.send_file(message.author, 'formattedroster.txt')

		elif query == 'send promotion':
			await client.send_message(message.author, 'Here is the requested file:')
			await client.send_file(message.author, 'promotion_list.txt')


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

	async def groupupdate(self, client, message):
		if message.author.id != '77165970824630272':
			pass
		else:
			serv = discord.utils.find(lambda m: m.name == self.server_name, client.servers)
			with open('groups.txt', 'r') as f:
				all_groups = json.load(f)
			for x in all_groups:
				new_member_list = []
				for y in all_groups[x]["members"]:
					member = discord.utils.find(lambda m: m.name == y, serv.members)
					new_member_list += [member.id]
				all_groups[x]["members"] = new_member_list
			with open('groups.txt', 'w') as f:
				f.write(str(json.dumps(all_groups)))
			await client.send_message(message.channel, "The group list has been updated.")