from main import *
from telethon.tl.functions.users import GetFullUserRequest


async def get_user_id(username):
    async with client:
        full = await client(GetFullUserRequest(username))

        return full.full_user.id


async def check_rights(message, args):
    recipients_id = await get_user_id(args[1])
    actioned_role_name = args[2]

    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query1 = f'SELECT user_role FROM users WHERE user_id = "{message.from_user.id}"'

        query2 = f'SELECT user_role FROM users WHERE user_id = "{recipients_id}"'

        query3 = f'SELECT rowid FROM roles WHERE role = "{actioned_role_name}"'

        roles_ids = [cursor.execute(query1).fetchone()[0], cursor.execute(query2).fetchone()[0], cursor.execute(query3).fetchone()[0]]

        flag = True

        if roles_ids[0] <= roles_ids[1]:
            flag = False

        if roles_ids[0] < roles_ids[2]:
            flag = False

        if roles_ids[1] == roles_ids[2]:
            flag = False

        if 4 in roles_ids:
            flag = False

        return flag


async def check_mute_rights(message, args):
    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query1 = f'SELECT user_role FROM users WHERE user_id = "{message.from_user.id}"'

        query2 = f'SELECT user_role FROM users WHERE user_id = "{args[4]}"'

    roles_ids = [cursor.execute(query1).fetchone()[0], cursor.execute(query2).fetchone()[0]]

    flag = True

    if roles_ids[0] <= roles_ids[1]:
        flag = False

    if roles_ids[0] == 4 or roles_ids[1] == 4:
        flag = False

    return flag


async def is_muted(user_id):
    with sq.connect('users.db') as db:
        cursor = db.cursor()

        query = f'SELECT user_role FROM users WHERE user_id = "{user_id}"'

        user_role = cursor.execute(query).fetchone()[0]

    if user_role == 4:
        return True

    return False
