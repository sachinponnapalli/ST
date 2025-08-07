import os
from peewee import *
from dotenv import load_dotenv
import pandas as pd
from datetime import time, datetime

load_dotenv()

# db = SqliteDatabase("db.sqlite3")
db = PostgresqlDatabase(
    os.getenv("POSTGRES_DB"),
    user = os.getenv("POSTGRES_USER"),
    password = os.getenv("POSTGRES_PASSWORD"),
    host = os.getenv("DB_HOST"),
    port = os.getenv("DB_PORT")
)


db.connect()
print("DB connected")


class Signal(Model):
    datetime = DateTimeField()
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    supertrend = FloatField()
    trend = IntegerField()  # -1 = bearish, 1 = bullish
    trade = BooleanField()
    class Meta:
        database = db
        table_name = 'signal'
        schema = 'algo'



class Config(Model):
    sell_strike = CharField()
    buy_strike = CharField()

    class Meta:
        database = db
        table_name = 'config'
        schema = 'algo'


class Latest_15_min_candle(Model):
    datetime = DateTimeField()
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    class Meta:
        database = db
        table_name = 'latest_15_min_candle'
        schema = 'algo'


db.execute_sql("CREATE SCHEMA IF NOT EXISTS algo;")
db.create_tables([Signal,Config,Latest_15_min_candle], safe=True)

if __name__ == "__main__":
    Config.get_or_create(
        id=1,  # Use a fixed ID to ensure a single row
        defaults={
            "sell_strike":"OTM2",  # Default auto_trade valu
            "buy_strike":"OTM6",
            })
