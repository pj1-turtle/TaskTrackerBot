from models.task import TaskIn, TaskOut
from typing import List
import databases
from schemas import tasks
from sqlalchemy.schema import CreateTable

DATABASE_URL = 'sqlite:///tasks.db'
db = databases.Database(DATABASE_URL)

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


async def get_mapped_tasks(query: str, values=None) -> List[TaskOut]:
    await db.connect()
    mapped_assignments: List[TaskOut] = []
    async for row in db.iterate(query=query, values=values):
        mapped_assignments.append(TaskOut(
            task_id=row[0],
            title=row[1],
            content=row[2],
            deadline=row[3],
            date_assigned=row[4],
            guild_id=row[5],
            role_id=row[6]
        ))
    await db.disconnect()
    return mapped_assignments

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


