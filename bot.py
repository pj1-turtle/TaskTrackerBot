import db_service
from utilities import get_role_by_name, get_role_from_mention, remove_all, sum_dict_values, displayTasks, create_task_embed
from models.task import TaskIn, TaskOut
from schemas import tasks
from typing import List
import os
from datetime import date

import discord
from discord.ext import commands
from dotenv import load_dotenv

DEBUG = True
if DEBUG:
    load_dotenv()

bot = commands.Bot(command_prefix='-')

@bot.command()
async def addTask(ctx, role_mention=None) -> None:
    def check(message: discord.Message) -> bool:
        if ctx.author != message.author:
            return False
        return True
    
    def deadline_check(message: discord.Message) -> bool:
        if '/' not in message.content:
            return False

        date_information = message.content.split('/')
        if len(date_information) != 3:
            return False
        return True
    
    await ctx.send('Enter the task title')
    title_message: discord.Message = await bot.wait_for('message', check=check)
    title: str = str(title_message.content)

    await ctx.send('Enter the content of the task')
    content_message: discord.Message = await bot.wait_for('message', check=check)
    task_content: str = str(content_message.content)

    await ctx.send('What is the deadline? Please provide in the format DD/MM/YY')
    deadline_message: discord.Message = await bot.wait_for('message', check=deadline_check)
    deadline: str = str(deadline_message.content)

    role_id = ''
    if role_mention != None:
        role = get_role_from_mention(role_mention)
        if role == None:
            await ctx.send("Sorry, there doesn't seem to be a role with this name")
            return
        elif role not in ctx.author.roles:
            await ctx.send('Sorry, you are not authorized to make this command')
            return
        role_id = str(role.id)

    secret_guild_id = str(os.getenv('SECRET_GUILD_ID'))

    if secret_guild_id == str(ctx.guild.id):
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                if channel.name == str(title).lower():
                    await channel.send(f'{ctx.author.mention} {task_content}')
    

    await db_service.insert_one_task(TaskIn(
        title=title,
        content=task_content,
        deadline=deadline,
        date_assigned=date.today().strftime('%d/%m/%Y'),
        guild_id=str(ctx.guild.id),
        role_id=role_id
    ))
    await ctx.send('Added task to database!')

@bot.command()
async def getTasks(ctx, role_mention=None) -> None:
    role: discord.Role = None
    if role_mention != None:
        role = get_role_from_mention(role_mention, ctx.guild.roles)
        if role == None:
            await ctx.send("Sorry, there doesn't seem to be a role with this name")
            return
        elif role not in ctx.author.roles:
            await ctx.send('Sorry, you are not authorized to make this command')
            return

    await ctx.send("Getting tasks...")
    query = tasks.select().where(tasks.c.guild_id == '').where(tasks.c.role_id == '')
    values = {
        'guild_id_1': str(ctx.guild.id),
        'role_id_1': ''
    }
    if role != None:
        values['role_id_1'] = str(role.id)

    mapped_tasks = await db_service.get_mapped_tasks(query=str(query), values=values)
    await displayTasks(ctx=ctx, mapped_tasks=mapped_tasks)

@bot.command()
async def markComplete(ctx):
    def check(message: discord.Message) -> bool:
        if message.author != ctx.author:
            return False
        try:
            serial_number = int(message.content)
        except:
            return False
        
        return True

    query = tasks.select().where(tasks.c.guild_id == ctx.guild.id)
    values = {
        'guild_id_1': str(ctx.guild.id)
    }
    mapped_tasks = await db_service.get_mapped_tasks(query=str(query), values=values)
    no_tasks: bool = await displayTasks(ctx=ctx, mapped_tasks=mapped_tasks)
    if no_tasks:
        return

    await ctx.send('Please enter the serial number of the task you would like to mark as complete')
    serial_number_message: discord.Message = await bot.wait_for('message', check=check)
    serial_number: int = int(serial_number_message.content)

    for task in mapped_tasks:
        if str(task.task_id) == str(serial_number):
            task_embed = create_task_embed(task)
            await ctx.send(embed=task_embed)
            await ctx.send('Removing this task...')
            await db_service.delete_one_task(task)
            await ctx.send('Done!')
            return
    
    await ctx.send(f"Sorry, doesn't look like there's a task with the id of {serial_number}")


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

    
    await ctx.send(f'Total: {sum_dict_values(counts)}')
    for member_name in counts.keys():
        await ctx.send(f'{member_name}: {counts.get(member_name)}')


@bot.command()
async def changeStatusTo(ctx, new_status: str) -> None:
    possible_statuses = ['dnd', 'online', 'idle', 'invisible']
    if new_status in possible_statuses:
        await bot.change_presence(status=new_status)
    return


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    # await bot.change_presence(status=discord.Status.do_not_disturb)

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    if before.channel == None and after.channel != None:
        guild: discord.Guild = after.channel.guild
        role = get_role_by_name(role_name=after.channel.name, roles=guild.roles)
        if role == None:
            role = await guild.create_role(name=after.channel.name)
        
        await member.add_roles(role)
    elif before.channel != None and after.channel == None:
        guild: discord.Guild = before.channel.guild
        role = get_role_by_name(role_name=before.channel.name, roles=guild.roles)
        await member.remove_roles(role)

    elif before.channel != None and after.channel != None and before.channel != after.channel:
        guild: discord.Guild = before.channel.guild
        before_role = get_role_by_name(role_name=before.channel.name, roles=guild.roles)
        after_role = get_role_by_name(role_name=after.channel.name, roles=guild.roles)
        if before_role == None:
            before_role = await guild.create_role(name=before.channel.name)
        if after_role == None:
            after_role = await guild.create_role(name=after.channel.name)
        await member.remove_roles(before_role)
        await member.add_roles(after_role)

token: str = str(os.getenv('DISCORD_TOKEN'))
bot.run(token)


