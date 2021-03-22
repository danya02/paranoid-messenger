import peewee as pw

db = pw.SqliteDatabase('data.db') # TODO: move this to a config file

class MyModel(pw.Model):
    class Meta:
        database = db

def create_table(model):
    db.create_tables([model])
    return model

