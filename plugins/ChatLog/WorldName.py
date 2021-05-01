# from FFxivPythonTrigger.lumina import lumina
# from Lumina.Excel.GeneratedSheets import World
#
# world_sheet = lumina.GetExcelSheet[World]()

from FFxivPythonTrigger.SaintCoinach import realm
world_sheet = realm.game_data.get_sheet('World')

name_cache = dict()
translate = {
    'HuPoYuan': '琥珀原',
    'RouFengHaiWan':'柔风海湾',
    'HaiMaoChaWu':'海猫茶屋',
    'MengYuBaoJing':'梦羽宝境'
}


def get_world_name(world_id: int):
    if world_id not in name_cache:
        name_cache[world_id] = world_sheet[world_id]['Name']
    return name_cache[world_id], translate.get(name_cache[world_id])
