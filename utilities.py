from datetime import date
import calendar
from models.task import TaskOut
from typing import Dict, List
import discord

def get_day_from_date(date_input: date) -> str:
    day, month, year = [int(i) for i in date_input.strftime("%d/%m/%Y").split('/')]
    new_date = date(year=year, month=month, day=day)
    return new_date.strftime("%A") 

def get_month_from_date(date_input: date) -> str:
    day, month, year = [int(i) for i in date_input.strftime("%d/%m/%Y").split('/')]
    new_date = date(year=year, month=month, day=day)
    return calendar.month_name[new_date.month]

def log(log_title: str, log_content: str) -> None:
    print(f'[{log_title.upper()}]: {log_content}')

def remove_all(string: str, substrings: List[str]) -> str:
    for substring in substrings:
        string = string.replace(substring, '')
    return string

def get_role_from_mention(role_mention: str, roles: List[discord.Role]) -> discord.Role:
    role_id = remove_all(role_mention, ['<', '>', '!', '@', '&'])
    return get_role_from_id(role_id, roles)

def get_role_from_id(role_id: str, roles: List[discord.Role]) -> discord.Role:
    for role in roles:
        if str(role.id) == role_id:
            return role
    return None

def get_role_by_name(role_name: str, roles: List[discord.Role]) -> discord.Role:
    for role in roles:
        if str(role.name) == role_name:
            return role
    return None

def create_task_embed(task: TaskOut) -> discord.Embed:
    task_embed = discord.Embed(
        type="rich",
        title=task.title
    )
    task_embed.color = discord.Colour(0x3fce8)
    task_embed.description = f'Task Id: {task.task_id}\n'
    task_embed.description += f'Task content: {task.content}\n'
    task_embed.description += f'Deadline: {task.deadline}\n'
    task_embed.description += f'Date assigned: {task.date_assigned}'
    if task.role_id != '':
        task_embed.description += f'\nGroup: {"<@&%s>" % int(task.role_id)}'

    return task_embed

async def displayTasks(ctx, mapped_tasks: List[TaskOut]) -> bool:
    if len(mapped_tasks) == 0:
        await ctx.send('No tasks. Woohoo!')
        return True
        
    for task in mapped_tasks:
        task_embed = create_task_embed(task)
        await ctx.send(embed=task_embed)
    return False

def sum_dict_values(dictionary: Dict[str, int]) -> int:
    total = 0
    for value in dictionary.values():
        total += value
    return total






