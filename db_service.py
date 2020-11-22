import os
import discord
from sqlalchemy.sql.selectable import Select
from models.task import TaskIn, TaskOut
from typing import Any, Dict, List
import databases
from schemas import tasks
from sqlalchemy.schema import CreateTable

DATABASE_URI = str(os.getenv('DATABASE_URI'))
db = databases.Database(DATABASE_URI)

schemas = {
    'tasks': tasks
}

async def create_table(table_name: str) -> None:
    table = schemas.get(table_name)
    if table != None:
        await db.connect()
        sql_statement = str(CreateTable(table))
        await db.execute(sql_statement)
        await db.disconnect()


async def delete_one_task(task: TaskOut) -> None:
    query = str(tasks.delete().where(tasks.c.id == 'id_1'))
    values = {
        'id_1': task.task_id
    }
    await db.connect()
    await db.execute(query=str(query), values=values)
    await db.disconnect()

async def get_guild_tasks(guild: discord.Guild, role: discord.Role=None) -> List[TaskOut]:
    role_id: str = ''
    if role != None:
        role_id = str(role.id)
    return await filter_tasks_by({
        "equalTo": {
            "guild_id": str(guild.id),
            "role_id": str(role_id)
        }
    })



async def filter_tasks_by(filters: Dict[str, Dict[str, Any]]=None) -> List[TaskOut]:
    query: Select = tasks.select()
    values = {}

    if filters:
        if filters.get('equalTo') != None:
            for filter in filters['equalTo'].keys():
                if filters['equalTo'].get(filter) != None:
                    query = query.where(getattr(tasks.c, filter) == '')
                    values[filter + '_1'] = filters['equalTo'].get(filter)

        if filters.get('lessThan') != None:
            for filter in filters['lessThan'].keys():
                if filters['lessThan'].get(filter) != None:
                    query = query.where(getattr(tasks.c, filter) <= '')
                    values[filter + '_1'] = filters['lessThan'].get(filter)

        if filters.get('greaterThan') != None:
            for filter in filters['greaterThan'].keys():
                if filters['greaterThan'].get(filter) != None:
                    query = query.where(getattr(tasks.c, filter) >= '')
                    values[filter + '_1'] = filters['greaterThan'].get(filter)
    
    if values == {}:
        values = None
    return await get_tasks(query=str(query), values=values)


async def get_tasks(query: str, values=None) -> List[TaskOut]:
    await db.connect()
    mapped_tasks: List[TaskOut] = []
    async for row in db.iterate(query=query, values=values):
        mapped_tasks.append(TaskOut(
            task_id=row[0],
            title=row[1],
            content=row[2],
            deadline=row[3],
            date_assigned=row[4],
            guild_id=row[5],
            role_id=row[6]
        ))
    await db.disconnect()
    return mapped_tasks


async def insert_one_task(task: TaskIn) -> None:
    query = tasks.insert()
    await db.connect()
    await db.execute(query=query, values=task.to_dict())
    await db.disconnect()


async def insert_many_tasks(task_inputs: List[TaskIn]) -> None:
    query = tasks.insert()
    await db.connect()
    await db.execute_many(query=query, values=[task_inputs[i].to_dict() for i in range(0, len(task_inputs))])
    await db.disconnect()


