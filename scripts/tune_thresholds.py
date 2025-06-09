import statistics
from civsim import World, Simulation, Entity
from civsim.actions import RestAction, ConsumeAction, MoveToAction
from civsim.world import Resource

# Parameter ranges
consume_levels = [8, 12, 16]
gather_levels = [30, 40, 50]


class TestEntity(Entity):
    consume_level = 12
    gather_level = 50

    def plan_action(self, world):
        if self.needs.energy <= 20:
            return RestAction()
        if self.needs.health < 30:
            if (
                self.needs.thirst > 5
                and self.inventory.items.get(Resource.WATER, 0) > 0
            ):
                return ConsumeAction(Resource.WATER)
            for food in (Resource.MEAT, Resource.BERRIES):
                if self.needs.hunger > 5 and self.inventory.items.get(food, 0) > 0:
                    return ConsumeAction(food)
        if (
            self.needs.thirst >= self.consume_level
            and self.inventory.items.get(Resource.WATER, 0) > 0
        ):
            return ConsumeAction(Resource.WATER)
        if self.needs.hunger >= self.consume_level:
            for food in (Resource.MEAT, Resource.BERRIES):
                if self.inventory.items.get(food, 0) > 0:
                    return ConsumeAction(food)
        if (
            self.needs.thirst >= self.gather_level
            and self.inventory.items.get(Resource.WATER, 0) == 0
        ):
            loc = self.remembered_adjacent_tile_for_resource(world, Resource.WATER)
            if loc:
                return MoveToAction(target=loc)
        if self.needs.hunger >= self.gather_level and not any(
            self.inventory.items.get(res, 0) > 0
            for res in (Resource.MEAT, Resource.BERRIES)
        ):
            for res in (Resource.ANIMAL, Resource.BERRY_BUSH):
                loc = self.remembered_adjacent_tile_for_resource(world, res)
                if loc:
                    return MoveToAction(target=loc)
        return super().plan_action(world)


results = {}
for c in consume_levels:
    for g in gather_levels:
        world = World(width=20, height=20, seed=4, resource_scale=4)
        entities = [TestEntity(id=i, x=10, y=10) for i in range(5)]
        for e in entities:
            e.consume_level = c
            e.gather_level = g
        sim = Simulation(world=world, entities=entities)
        for _ in range(50):
            sim.step()
        avg_hunger = statistics.mean(e.needs.hunger for e in sim.entities)
        results[(c, g)] = avg_hunger
print(results)
