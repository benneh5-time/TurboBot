class Rogue:
    def __init__(self):
        self.health = 3
        self.items = {
            "Mithril Armor": True,
            "Buckler": True,
            "Ring of Power": True,
            "Invisibility Cloak": True,
            "Vorpal Dagger": True,
            "Healing Potion": True,
        }
        self.alive = True

    def use_item(self, item):
        if self.items.get(item):
            self.items[item] = False
            return True
        return False

    def is_alive(self):
        return self.alive

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.alive = False