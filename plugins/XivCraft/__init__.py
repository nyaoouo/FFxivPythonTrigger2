import re
from ctypes import *
from traceback import format_exc
from time import sleep

from FFxivPythonTrigger import PluginBase, api, EventBase, process_event
from FFxivPythonTrigger.AddressManager import AddressManager
from FFxivPythonTrigger.SaintCoinach import realm
from FFxivPythonTrigger.hook import Hook
from FFxivPythonTrigger.memory import read_ushort, scan_pattern, read_memory, scan_address
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct, PointerStruct
from .simulator import Models, Manager, Craft
from .solvers import SkyBuilder23Astar as SkyBuilder23, JustDoIt, MacroCraft, SkyBuilder4Astar, SkyBuilders
import win32com.client

speaker = win32com.client.Dispatch("SAPI.SpVoice")

recipe_sheet = realm.game_data.get_sheet('Recipe')
craft_start_sig = "40 53 48 83 EC ? 48 8B D9 C6 81 ? ? ? ? ? E8 ? ? ? ? 48 8D 4B ?"
craft_status_sig = "8B 05 ? ? ? ? BE ? ? ? ? 89 44 24 ?"
base_quality_ptr_sig = "48 83 3D ? ? ? ? ? 74 ? E8 ? ? ? ? 48 8B C8 E8 ? ? ? ? 3C ? 0F B6 CB"

CraftStatus = OffsetStruct({
    'round': (c_uint, 0x18),
    'current_progress': (c_uint, 0x1c),
    'current_quality': (c_uint, 0x24),
    'current_durability': (c_uint, 0x30),
    'status_id': (c_ushort, 0x38)
})
BaseQualityPtr = PointerStruct(c_uint, 0x60, 0x408)

registered_solvers = [
    JustDoIt.JustDoIt,
    MacroCraft.MacroCraft,
    SkyBuilders.SkyBuilders,
    # SkyBuilder23.SkyBuilder23,
    # SkyBuilder4Astar.SkyBuilder4,
]

callback = lambda ans: speaker.Speak(ans)


class CraftStart(EventBase):
    id = "craft_start"
    name = "craft start"

    def __init__(self, recipe: Models.Recipe, player: Models.Player, base_quality: int):
        self.recipe = recipe
        self.player = player
        self.base_quality = base_quality

    def __str__(self):
        return f"CraftStart;{self.recipe};{self.player};{self.base_quality}"


class CraftAction(EventBase):
    id = "craft_action"
    name = "craft action"

    def __init__(self, craft: Craft.Craft, skill: Models.Skill):
        self.craft = craft
        self.skill = skill

    def __str__(self):
        return f"CraftAction;{self.skill.name}"


class CraftEnd(EventBase):
    id = "craft_end"
    name = "craft end"

    def __str__(self):
        return "CraftEnd"


class XivCraft(PluginBase):
    name = "XivCraft"

    def __init__(self):
        super(XivCraft, self).__init__()

        class ChatLogRegexProcessor(object):
            def __init__(_self):
                _self.data = dict()

            def register(_self, channel_id, regex, callback):
                if channel_id not in _self.data:
                    _self.data[channel_id] = set()
                _self.data[channel_id].add((re.compile(regex), callback))

            def process(_self, chat_log):
                if chat_log.channel_id in _self.data:
                    for regex, callback in _self.data[chat_log.channel_id]:
                        result = regex.search(chat_log.message)
                        if result: self.create_mission(callback, chat_log, result)

        class CraftStartHook(Hook):
            restype = c_int64
            argtypes = [c_int64]

            def hook_function(_self, a1):
                ans = _self.original(a1)
                recipe_id = read_ushort(a1 + 880)
                try:
                    self._recipe = recipe_sheet[recipe_id] if recipe_id else None
                except Exception:
                    self.logger.error("error in craft start hook:\n" + format_exc())
                return ans

        am = AddressManager(self.storage.data, self.logger)
        self.craft_start_hook = CraftStartHook(am.get('craft_start', scan_pattern, craft_start_sig))
        self.craft_status = read_memory(CraftStatus, am.get('craft_status', scan_address, craft_status_sig, cmd_len=6))
        self.base_quality = read_memory(BaseQualityPtr, am.get('base_quality_ptr', scan_address, base_quality_ptr_sig, cmd_len=8, ptr_idx=3))
        self.storage.save()

        self.chat_log_processor = ChatLogRegexProcessor()

        self.chat_log_processor.register(2114, "^(.+)开始练习制作\ue0bb(.+)。$", self.craft_start)
        self.chat_log_processor.register(2114, "^(.+)开始制作“\ue0bb(.+)”(×\d+)?。$", self.craft_start)

        self.chat_log_processor.register(2091, "^(.+)发动了“(.+)”(。)$", self.craft_next)
        self.chat_log_processor.register(2114, "^(.+)发动“(.+)”  \ue06f (成功|失败)$", self.craft_next)
        # self.chat_log_processor.register(56, "^@Craft next$", self.craft_next)

        self.chat_log_processor.register(2114, "^(.+)练习制作\ue0bb(.+)成功了！$", self.craft_end)
        self.chat_log_processor.register(2114, "^(.+)练习制作\ue0bb(.+)失败了……$", self.craft_end)
        self.chat_log_processor.register(2114, "^(.+)停止了练习。$", self.craft_end)
        self.chat_log_processor.register(2242, "^(.+)制作“\ue0bb(.+)”(×\d+)?成功！$", self.craft_end)
        self.chat_log_processor.register(2114, "^(.+)制作失败了……$", self.craft_end)
        self.chat_log_processor.register(2114, "^(.+)中止了制作作业。$", self.craft_end)

        self._recipe = None
        self.solver = None
        self.base_data = None
        self.name = None
        self.register_event("log_event", self.chat_log_processor.process)

    def get_base_data(self):
        recipe = Models.Recipe(self._recipe)
        me = api.XivMemory.actor_table.get_me()
        me_info = api.XivMemory.player_info
        player = Models.Player(me.level, me_info.craft, me_info.control, me.maxCP)
        return recipe, player

    def get_current_craft(self):
        me = api.XivMemory.actor_table.get_me()
        recipe, player = self.base_data
        effects = dict()
        for eid, effect in me.effects.get_items():
            if eid in Manager.effects_id:
                new_effect = Manager.effects_id[eid](effect.param)
                effects[new_effect.name] = new_effect
        return Craft.Craft(
            recipe=recipe,
            player=player,
            craft_round=self.craft_status.round,
            current_progress=self.craft_status.current_progress,
            current_quality=self.craft_status.current_quality,
            current_durability=self.craft_status.current_durability,
            current_cp=me.currentCP,
            status=Manager.status_id[self.craft_status.status_id or 1](),
            effects=effects,
        )

    def craft_start(self, chat_log, regex_result):
        self.name = api.XivMemory.actor_table.get_me().Name
        if regex_result.group(1)!=self.name:return
        recipe, player = self.base_data = self.get_base_data()
        self.logger.info("start recipe:" + recipe.detail_str)
        craft = Craft.Craft(recipe=recipe, player=player, current_quality=self.base_quality.value)
        process_event(CraftStart(recipe, player, self.base_quality.value))
        for solver in registered_solvers:
            if solver.suitable(craft):
                self.solver = solver(craft=craft, logger=self.logger)
                break
        if self.solver is not None:
            self.logger.info("solver found, starting to solve...")
            ans = self.solver.process(craft, None)
            if ans is not None and callback is not None: self.create_mission(callback, ans)
        else:
            self.logger.info("no solver found, please add a solver for this recipe")

    def craft_next(self, chat_log, regex_result):
        if regex_result.group(1)!=self.name:return
        sleep(0.5)
        try:
            skill = Manager.skills[regex_result.group(2) + ('' if regex_result.group(3) != "失败" else ':fail')]()
        except KeyError:
            return
        craft = self.get_current_craft()
        if skill == "观察":
            craft.add_effect("观察", 1)
            craft.merge_effects()
        self.logger.debug(f"use skill:{skill.name}")
        self.logger.debug(craft)
        process_event(CraftAction(craft, skill))
        if self.solver is not None:
            ans = self.solver.process(craft, skill)
            self.logger.info("suggested skill '%s'" % ans)
            if ans and callback is not None: self.create_mission(callback, ans)

    def craft_end(self, chat_log, regex_result):
        if regex_result.group(1) != self.name: return
        process_event(CraftEnd())
        self.solver = None
        self.logger.info("end craft")

    def _start(self):
        self.craft_start_hook.enable()

    def _onunload(self):
        self.craft_start_hook.uninstall()
