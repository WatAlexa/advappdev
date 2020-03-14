import peewee


class Ticker(peewee.Model):
    id = peewee.UUIDField(primary_key=True)
    # timestamp in milliseconds
    timestamp = peewee.BigIntegerField()
    # the latest trades price
    