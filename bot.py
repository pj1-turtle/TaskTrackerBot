from dotenv import load_dotenv

DEBUG = True
if DEBUG:
    load_dotenv()


from typing import List
import db_service
from utilities.general_utilities import remove_all, sort_dict_by_value
from utilities.bot_utilities import displayTasks, get_and_add_task, input_role_from_user, get_role_by_attribute, get_role_from_mention, task_completion_screen
from schemas import tasks
import os
from datetime import date

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='-')

@bot.command()
async def addTask(ctx) -> None:
    await get_and_add_task(ctx, bot)


@bot.command()
async def addTaskToRole(ctx) -> None:
    role: discord.Role = await input_role_from_user(
        ctx=ctx,
        bot=bot,
        error_message="Sorry, there doesn't seem to be a role with this name. Please do not mention the role and make sure to provide the role name"
    )
    if not role:
        return
    if role not in ctx.author.roles:
        await ctx.send('Sorry, you are not authorized to make this command')
        return
    await get_and_add_task(ctx, bot, role=role)


@bot.command()
async def getTasksByRole(ctx) -> None:
    role: discord.Role = await input_role_from_user(
        ctx=ctx,
        bot=bot,
        error_message="Sorry, there doesn't seem to be a role with this name. Please do not mention the role and make sure to provide the role name"
    )
    if not role:
        return
    if role not in ctx.author.roles:
        await ctx.send('Sorry, you are not authorized to make this command')
        return

    await ctx.send("Getting tasks...")
    mapped_tasks = await db_service.get_guild_tasks(ctx.guild, role=role)
    await displayTasks(ctx, mapped_tasks)

@bot.command()
async def getTasks(ctx) -> None:
    mapped_tasks = await db_service.get_guild_tasks(ctx.guild, role=None)
    await displayTasks(ctx, mapped_tasks)
    

@bot.command()
async def markCompleteByRole(ctx):
    role: discord.Role = await input_role_from_user(
        ctx=ctx,
        bot=bot,
        error_message="Sorry, there doesn't seem to be a role with this name. Please do not mention the role and make sure to provide the role name"
    )

    await task_completion_screen(ctx, bot, role=role)


@bot.command()
async def markComplete(ctx) -> None:
    await task_completion_screen(ctx, bot, role=None)


@bot.command()
async def countMessage(ctx, messages=None) -> None:
    def check(message: discord.Message) -> bool:
        if ctx.author != message.author:
            return False
        return True

    counts = {}
    messages_to_count = []
    if messages != None:
        messages_to_count = messages.split(',')
    
    await ctx.send("What channel would you like to count in?")
    channel_id = remove_all((await bot.wait_for('message', check=check)).content, ['<', '>', '#'])
    channel: discord.TextChannel = bot.get_channel(int(channel_id))

    async for message in channel.history(limit=None):
        if messages_to_count != []:
            if message.content.lower() in [string.lower() for string in messages_to_count]:
                if str(message.author.name) in counts.keys():
                    counts[str(message.author.name)] += 1
                else:
                    counts[str(message.author.name)] = 1
        elif messages_to_count == []:
            if str(message.author.name) in counts.keys():
                counts[str(message.author.name)] += 1
            else:
                counts[str(message.author.name)] = 1

    counts = sort_dict_by_value(counts)
    message_count_embed = discord.Embed(
        type='rich',
        title='Message Count'
    )
    message_count_embed.description = f'Total: {sum(counts.values())}\n'
    for member_name in counts.keys():
        message_count_embed.description += f'{member_name}: {counts.get(member_name)}\n'
    
    await ctx.send(embed=message_count_embed)

@bot.command()
async def purgeRole(ctx) -> None:
    
    def check(message: discord.Message) -> bool:
        if message.author != ctx.author:
            return False
        return True
    role: discord.Role = await input_role_from_user(
        ctx=ctx,
        bot=bot,
        error_message="Sorry, there doesn't seem to be a role with this name. Please do not mention the role and make sure to provide the role name"
    )

    for member in ctx.guild.members:
        print(member)
        print(f'Removing {role.name} from {member.name}...')
        if role in member.roles:
            await member.remove_roles([role], reason=f'purgeRole command issued by {ctx.author.name}')

@bot.command()
async def pingVC(ctx):
    vc_role: discord.Role = get_role_by_attribute('name', ctx.author.voice.channel.name, ctx.guild.roles)
    await ctx.send(vc_role.mention)


@bot.command()
async def setStatus(ctx, new_status: str) -> None:
    possible_statuses = ['dnd', 'online', 'idle', 'invisible']
    if new_status in possible_statuses:
        await bot.change_presence(status=new_status)
    return


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    if before.channel == None and after.channel != None:
        guild: discord.Guild = after.channel.guild
        role = get_role_by_attribute('name', after.channel.name, roles=guild.roles)
        if role == None:
            role = await guild.create_role(name=after.channel.name)
        
        await member.add_roles(role)
    elif before.channel != None and after.channel == None:
        guild: discord.Guild = before.channel.guild
        role = get_role_by_attribute('name', before.channel.name, roles=guild.roles)
        await member.remove_roles(role)

    elif before.channel != None and after.channel != None and before.channel != after.channel:
        guild: discord.Guild = before.channel.guild
        before_role = get_role_by_attribute('name', before.channel.name, roles=guild.roles)
        after_role = get_role_by_attribute('name', after.channel.name, roles=guild.roles)
        if before_role == None:
            before_role = await guild.create_role(name=before.channel.name)
        if after_role == None:
            after_role = await guild.create_role(name=after.channel.name)
        await member.remove_roles(before_role)
        await member.add_roles(after_role)


token = str(os.getenv('DISCORD_TOKEN'))
bot.run(token)


