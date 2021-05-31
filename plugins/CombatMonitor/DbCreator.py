import sqlite3

ability_table = '''
CREATE TABLE IF NOT EXISTS `AbilityEvent` (
`id` INTEGER PRIMARY KEY,
`timestamp` INTEGER NOT NULL ,
`source_id` INTEGER ,
`target_id` INTEGER NOT NULL ,
`ability_id` INTEGER,
`type` VARCHAR NOT NULL ,
`param` INTEGER NOT NULL 
);
'''

ability_tag_table = '''
CREATE TABLE IF NOT EXISTS `AbilityTags` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT ,
`ability_event_id` INTEGER NOT NULL ,
`tag` VARCHAR NOT NULL ,
FOREIGN KEY (`ability_event_id`) REFERENCES AbilityEvent(`id`)
);
'''


def get_con(path=":memory:"):
    conn = sqlite3.connect(path,check_same_thread=False)
    c = conn.cursor()
    c.execute(ability_table)
    c.execute(ability_tag_table)
    conn.commit()
    return conn
