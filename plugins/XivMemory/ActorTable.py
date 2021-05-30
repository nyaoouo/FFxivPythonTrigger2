from .struct.Actor import Actor
from .AddressManager import actor_table_addr
from FFxivPythonTrigger.memory import *

SIZE = 424


class ActorTable(POINTER(Actor) * SIZE):

    def get_actor(self,idx:int):
        return self[idx][0] if self[idx] else None

    def get_me(self):
        return self.get_actor(0)

    def get_item(self):
        for i in range(SIZE):
            actor = self.get_actor(i)
            if actor is not None:
                yield actor

    def get_actors_by_name(self, name: str):
        key = name.encode('utf-8')
        for actor in self.get_item():
            if actor.name == key:
                yield actor

    def get_actor_by_id(self, aid: int):
        for actor in self.get_item():
            if actor.id == aid:
                return actor

    def get_actors_by_id(self, *aids: int):
        target = set(aids)
        for main in self.get_item():
            if main.id in target:
                target.remove(main.id)
                yield main
            if not target:
                break


actor_table: ActorTable = read_memory(ActorTable, actor_table_addr)
