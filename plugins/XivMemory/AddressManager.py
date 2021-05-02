from FFxivPythonTrigger.memory import scan_address
from FFxivPythonTrigger.Logger import Logger
from FFxivPythonTrigger.Storage import get_module_storage
from FFxivPythonTrigger.AddressManager import AddressManager

_logger = Logger("XivMem/AddressManager")
_storage = get_module_storage("XivMem")
_am = AddressManager(_storage.data, _logger)

##########
# actor table
##########
actor_table_sig = "48 8d ?? ?? ?? ?? ?? e8 ?? ?? ?? ?? 48 8b ?? 48 8b ?? 48 8d ?? ?? ?? ?? ?? " \
                  "e8 ?? ?? ?? ?? 48 8d ?? ?? ?? ?? ?? ba ?? ?? ?? ?? e8 ?? ?? ?? ?? 89 2f"
actor_table_addr = _am.get("actor table", scan_address, actor_table_sig, cmd_len=7)

##########
# combat data
##########
combo_state_sig = "f3 0f ?? ?? ?? ?? ?? ?? f3 0f ?? ?? ?? e8 ?? ?? ?? ?? 48 8b ?? 48 8b ?? 0f b7"
combo_state_addr = _am.get("combo state", scan_address, combo_state_sig, cmd_len=8)

skill_queue_sig = "44 89 2d ?? ?? ?? ?? f3 0f 11 05 ?? ?? ?? ??"
skill_queue_addr = _am.get("skill queue", scan_address, skill_queue_sig, cmd_len=7, add=4)

is_in_fight_sig = "80 3d ?? ?? ?? ?? ?? 0f 95 c0 48 83 c4 ??"
is_in_fight_addr = _am.get("is in fight", scan_address, is_in_fight_sig, cmd_len=7, ptr_idx=2)

cool_down_group_sig = "0f b7 0d ?? ?? ?? ?? 84 c0"
cool_down_group_addr = _am.get("cool down group", scan_address, cool_down_group_sig, cmd_len=7, add=0x76)

enemies_base_sig = "48 8b 0d ?? ?? ?? ?? 4c 8b c0 33 d2"
enemies_base_addr = _am.get("enemies base", scan_address, enemies_base_sig, cmd_len=7)
enemies_shifts = [0x30, 0x58, 0x98, 0x20, 0x20]

##########
# player info
##########
gauge_sig = "48 8d ?? ?? ?? ?? ?? e8 ?? ?? ?? ?? 80 be 13 07 ?? ??"
gauge_addr = _am.get("gauge", scan_address, gauge_sig, cmd_len=7, add=0x10)

player_sig = "0f 10 ?? ?? ?? ?? ?? 40 0f ?? ?? 0f 95"
player_addr = _am.get("player", scan_address, player_sig, cmd_len=7, add=-0x11)

##########
# targets
##########
target_ptr_sig = "48 8B 05 ?? ?? ?? ?? 48 8D 0D ?? ?? ?? ?? FF 50 ?? 48 85 DB"
target_ptr_addr = _am.get("target ptr", scan_address, target_ptr_sig, cmd_len=7)

##########
# zone
##########
zone_sig = "0f b7 ?? ?? ?? ?? ?? 48 8d ?? ?? ?? f3 0f ?? ?? 33 d2"
zone_addr = _am.get("zone", scan_address, zone_sig, cmd_len=7)

##########
# skill animation lock
##########
skill_ani_lock_sig = "F3 0F ? ? ? ? ? ? 41 F6 47 20"
skill_ani_lock_addr = _am.get("skill animation lock", scan_address, skill_ani_lock_sig, cmd_len=8)

##########
# chat log
##########
chat_log_sig = "48 8b da 49 8b f8 41 8b d1 48 8b f1 ?? ?? ?? ?? ?? 48 8d 05"
chat_log_addr = _am.get("chat log", scan_address, chat_log_sig, cmd_len=24)

##########
# movement
##########
movement_sig="48 8D 0D ? ? ? ? E8 ? ? ? ? BA ? ? ? ? 48 8D 0D ? ? ? ? 0F B6 D8"
movement_addr = _am.get("movement", scan_address,movement_sig,cmd_len = 7)

_storage.save()
