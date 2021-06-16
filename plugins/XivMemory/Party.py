from ctypes import *
from FFxivPythonTrigger.memory import read_memory
from FFxivPythonTrigger.memory.StructFactory import OffsetStruct
from .struct.Party import PartyMember as PartyMemberStruct
from .ActorTable import actor_table
from .AddressManager import party_addr


class PartyMember(PartyMemberStruct):
    @property
    def actor(self):
        if self.id == 0 or self.id == 0xe0000000:
            return None
        else:
            actor_table.get_actor_by_id(self.id)


class PartyList(OffsetStruct({
    "members": (PartyMember * 28, 0),
    'flag': (c_ubyte, 15700),
    'main_size': (c_ubyte, 15708),
})):
    def main_party(self):
        for i in range(self.main_size):
            if self.members[i].id != 0xe0000000:
                yield self.members[i]

    def party_2(self):
        for i in range(8, 16):
            if self.members[i].id != 0xe0000000:
                yield self.members[i]

    def party_3(self):
        for i in range(16, 24):
            if self.members[i].id != 0xe0000000:
                yield self.members[i]

    def alliance(self):
        for i in self.main_party(): yield i
        for i in self.party_2(): yield i
        for i in self.party_3(): yield i


party = read_memory(PartyList, party_addr)
