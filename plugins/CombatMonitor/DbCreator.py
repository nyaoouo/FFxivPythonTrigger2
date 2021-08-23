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

insert_ability = """
INSERT INTO `AbilityEvent`
(`id`,`timestamp`,`source_id`,`target_id`,`ability_id`,`type`,`param`)
VALUES (?,?,?,?,?,?,?)
"""
insert_ability_tag = """
INSERT INTO `AbilityTags`
(`ability_event_id`,`tag`)
VALUES (?,?);
"""
select_damage_from = """
SELECT SUM(`param`)
FROM `AbilityEvent`
WHERE
    (`source_id` = ?) AND
    (`timestamp` BETWEEN ? AND ?) AND
    (`type` IN ('damage' ,'dot', 'dot_sim'));
"""
select_taken_damage_from = """
SELECT SUM(`param`)
FROM `AbilityEvent`
WHERE
    (`target_id` = ?) AND
    (`timestamp` BETWEEN ? AND ?) AND
    (`type` IN ('damage' ,'dot'));
"""
select_sim_dot_damage_from = """
SELECT SUM(`param`)
FROM `AbilityEvent`
WHERE
    (`source_id` = ?) AND
    (`timestamp` BETWEEN ? AND ?) AND
    (`type` = 'dot_sim');
"""

select_sim_dot_damage_group_from = """
SELECT `ability_id`, SUM(`param`)
FROM `AbilityEvent`
WHERE
    (`source_id` = ?) AND
    (`timestamp` BETWEEN ? AND ?) AND
    (`type` = 'dot_sim')
GROUP BY `ability_id`;
"""


def get_con(path=":memory:"):
    conn = sqlite3.connect(path, check_same_thread=False)
    c = conn.cursor()
    c.execute(ability_table)
    c.execute(ability_tag_table)
    conn.commit()
    return conn
