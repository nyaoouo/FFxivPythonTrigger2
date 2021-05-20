from .struct.Actor import ActorTableNode
from .AddressManager import actor_table_addr
from FFxivPythonTrigger.memory import *


class ActorTable(ActorTableNode * 100):

    def get_actor(self, idx):
        return self[idx].main_actor[0] if self[idx].main_actor else None

    def get_pet(self, idx):
        return self[idx].pet_actor[0] if self[idx].pet_actor else None

    def get_me(self):
        return self.get_actor(0)

    def get_my_pet(self):
        return self.get_pet(0)

    def get_item(self):
        for i in range(100):
            actor = self.get_actor(i)
            if actor is not None:
                yield i, actor, self.get_pet(i)

    def get_actors_by_name(self, name: str):
        key = name.encode('utf-8')
        for i, main, pet in self.get_item():
            if main.name == key:
                yield main
            if pet is not None and pet.name == key:
                yield pet

    def get_actor_by_id(self, aid: int):
        for i, main, pet in self.get_item():
            if main.id == aid:
                return main

    def get_actors_by_id(self,*aids:int):
        target = set(aids)
        for i, main, pet in self.get_item():
            if main.id in target:
                target.remove(main.id)
                yield main
            if not target:
                break


actor_table:ActorTable = read_memory(ActorTable, actor_table_addr)
