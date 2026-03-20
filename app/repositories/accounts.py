from typing import Mapping, Any

from clients.postgres import get_pg_connection
from errors import AccountNotFoundError
from models.accounts import AccountModel
from metrics import observe_db_query


class AccountPostgresStorage:
    @observe_db_query("insert")
    async def create(self, login: str, password: str) -> Mapping[str, Any]:
        query = '''
            INSERT INTO account (login, password)
            VALUES ($1::TEXT, $2::TEXT)
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            return dict(await connection.fetchrow(query, login, password))

    @observe_db_query("select")
    async def select(self, id: int) -> Mapping[str, Any]:
        query = '''
            SELECT *
            FROM account
            WHERE id = $1::INTEGER
            LIMIT 1
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)

            raise AccountNotFoundError()

    @observe_db_query("select")
    async def select_by_login_and_password(self, login: str, password: str) -> Mapping[str, Any]:
        query = '''
            SELECT *
            FROM account
            WHERE login = $1::TEXT AND password = $2::TEXT
            LIMIT 1
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, login, password)

            if row:
                return dict(row)

            raise AccountNotFoundError()

    @observe_db_query("delete")
    async def delete(self, id: int) -> Mapping[str, Any]:
        query = '''
            DELETE FROM account
            WHERE id = $1::INTEGER
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)

            raise AccountNotFoundError()

    @observe_db_query("update")
    async def block(self, id: int) -> Mapping[str, Any]:
        query = '''
            UPDATE account
            SET is_blocked = TRUE
            WHERE id = $1::INTEGER
            RETURNING *
        '''
        async with get_pg_connection() as connection:
            row = await connection.fetchrow(query, id)

            if row:
                return dict(row)

            raise AccountNotFoundError()


class AccountRepository:
    account_postgres_storage: AccountPostgresStorage = AccountPostgresStorage()

    async def create(self, login: str, password: str) -> AccountModel:
        raw = await self.account_postgres_storage.create(login, password)
        return AccountModel(**raw)

    async def get(self, account_id: int) -> AccountModel:
        raw = await self.account_postgres_storage.select(account_id)
        return AccountModel(**raw)

    async def get_by_login_and_password(self, login: str, password: str) -> AccountModel:
        raw = await self.account_postgres_storage.select_by_login_and_password(login, password)
        return AccountModel(**raw)

    async def delete(self, account_id: int) -> AccountModel:
        raw = await self.account_postgres_storage.delete(account_id)
        return AccountModel(**raw)

    async def block(self, account_id: int) -> AccountModel:
        raw = await self.account_postgres_storage.block(account_id)
        return AccountModel(**raw)
