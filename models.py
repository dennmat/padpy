from enum import Enum

from dataset import get_all_raw_data

ElementTypes = Enum("ElementTypes", "Fire Water Wood Dark Light NoElement")
ElementIds = {
    0 : ElementTypes.Fire,
    1 : ElementTypes.Water,
    2 : ElementTypes.Wood,
    3 : ElementTypes.Dark,
    4 : ElementTypes.Light,
    None : ElementTypes.NoElement,
}

TypeTypes = Enum("TypeTypes", "EvoMaterial Balanced Physical Healer Dragon God Attacker Devil AwokenSkillMaterial Protected EnhanceMaterial NoType")
TypeIds = { 
    0 : TypeTypes.EvoMaterial,
    1 : TypeTypes.Balanced,
    2 : TypeTypes.Physical,
    3 : TypeTypes.Healer,
    4 : TypeTypes.Dragon,
    5 : TypeTypes.God,
    6 : TypeTypes.Attacker,
    7 : TypeTypes.Devil,
    12 : TypeTypes.AwokenSkillMaterial,
    13 : TypeTypes.Protected,
    14 : TypeTypes.EnhanceMaterial,
    None : TypeTypes.NoType,
}

XpCurveTypes = Enum("XpCurveTypes", "One OnePointFive Two TwoPointFive Three  Four Five NoCurve")
XpCurveIds = { 
    1000000 : XpCurveTypes.One,
    1500000 : XpCurveTypes.OnePointFive,
    2000000 : XpCurveTypes.Two,
    2500000 : XpCurveTypes.TwoPointFive,
    3000000 : XpCurveTypes.Three,
    4000000 : XpCurveTypes.Four,
    5000000 : XpCurveTypes.Five,
    None : XpCurveTypes.NoCurve,
}

class ConstraintTypes(Enum):
   Element="El"
   Type = "Ty"
   NoneSet = "NoneSet"

ConstraintIds = {
    'elem' : ConstraintTypes.Element,
    'type' : ConstraintTypes.Type,
    'none' : ConstraintTypes.NoneSet,
}
ConstraintMap = {
    ConstraintTypes.Element : ElementIds,
    ConstraintTypes.Type : TypeIds,
}


class Pad(object):
    """
    This is the main object you'll be using to access all the data

    >>> pad = Pad(verbose=False)
    >>> monsters = pad.get_all_monsters()
    >>> ice_ogre = pad.get_monster(65)
    >>> ice_ogre.feed_xp
    <FeedExp 413.0>
    >>> ice_ogre.feed_xp.calc_for_level(12)
    4956.0
    >>> ice_ogre.atk
    <Attribute 277/875 * 1.0>

    >>> monsters_in_ice_ogre_tree = pad.get_evolution_tree(ice_ogre)
    [<Monster #64 Blue Ogre>,
     <Monster #65 Ice Ogre>,
     <Monster #312 Blazing Ice Ogre>,
     <Monster #313 Wood Ice Ogre>]
    """
    def __init__(self, verbose=False):
        data = get_all_raw_data(verbose=verbose)
        self.monsters = MonsterManager(data['monsters'])
        self.evolutions = EvolutionManager(data['evolutions'])
        self.active_skills = ActiveSkillManager(data['active_skills'])
        self.awakenings = AwakeningManager(data['awakenings'])
        self.leader_skills = LeaderSkillManager(data['leader_skills'])

    def get_monster(self, id):
        monster = self.monsters.get_by_id(id)
        monster.active_skill = self.active_skills.get_by_id(monster.active_skill_name)
        monster.evolutions = self.evolutions.get_by_id(monster.id)
        monster.awakenings = self.awakenings.get_for_monster(monster)
        monster.leader_skill = self.leader_skills.get_for_monster(monster)
        return monster

    def get_all_monsters(self):
        return self.sort(self.monsters.objects)

    def sort(self, monsters):
        return sorted(monsters, key=lambda monster: monster.id)

    def get_evolution_tree(self, monster):
        """ 
        find all evolutions that either come from, or start before this monster
        """
        tree = [monster]
        #before
        prevos_to_check = self.evolutions.get_by_evolves_to(monster.id)
        while prevos_to_check:
            prevo_check = self.get_monster(prevos_to_check.pop().monster_id)
            if prevo_check not in tree:
                tree.append(prevo_check)
                for prevo in self.evolutions.get_by_evolves_to(prevo_check.id):
                    prevos_to_check.append(prevo)

        #after
        evos_to_check = monster.evolutions
        while evos_to_check:
            check_monster = self.get_monster(evos_to_check.pop().evolves_to)
            if check_monster not in tree:
                tree.append(check_monster)
                for evo in check_monster.evolutions:
                    evos_to_check.append(evo)

        return self.sort(tree)


class BaseManager(object):
    identifier = "id"
    can_find_many = False

    nested_dict = False

    def __init__(self, data):
        self.load_data(data)

    @property
    def model(self):
        return None

    def build_obj(self, **kwargs):
        return self.model(**kwargs)

    def load_data(self, data):
        self.objects = []
        if not self.nested_dict:
            for d in data:
                obj = self.build_obj(**d)
                self.objects.append(obj)
        else:
            for key, obj_set in data.iteritems():
                for obj_data in obj_set:
                    obj = self.model(
                        key,
                        **obj_data
                    )
                    self.objects.append(obj)

    def get_by_id(self, id):
        objects =  filter(lambda obj: getattr(obj, self.identifier) == id, self.objects)
        if not self.can_find_many:
            if objects:
                assert(len(objects)==1)# there should only be 1 object with this id
                return objects[0] 

        return objects

class MonsterManager(BaseManager):
    @property
    def model(self):
        return Monster

class ActiveSkillManager(BaseManager):
    identifier = "name"

    @property
    def model(self):
        return ActiveSkill

    def build_obj(self, **skill):
        return  self.model(
                    skill['min_cooldown'],
                    skill['effect'],
                    skill['max_cooldown'],
                    skill['name'],
                )

class ActiveSkill(object):
    def __init__(self, min_cooldown, effect, max_cooldown, name):
        self.min_cooldown = int(min_cooldown)
        self.effect = effect
        self.max_cooldown = int(max_cooldown)
        self.name = name

    def __str__(self):
        return "ActiveSkill: {name}".format(
            name=self.name.encode('utf8')
        )

    def __repr__(self):
        return "<%s>" % str(self)


class Image(object):
    def __init__(self, type, href, size, owner):
        self.type = type
        self.href = href
        self.size = size
        self.owner = owner

    def __str__(self):
        return "Image: {type} for #{id}".format(
                type=self.type,
                id=self.owner.id,
        )

    def __repr__(self):
        return "<%s>" % str(self)

class XpCurve(object):
    def __init__(self, id):
        self.id = id

    @property
    def long_name(self):
        return XpCurveIds[self.id].name

    def __str__(self):
        return "XP Curve {}".format(
            self.long_name,
        )

    def __repr__(self):
        return "<{}>".format(
            str(self)
        )

    def calc_for_level(self, level):
        return  round(self.id * (((level-1.0)/98.0)**2.5))

class FeedXp(object):
    def __init__(self, base_xp):
        self.base_xp = base_xp
        pass

    def __str__(self):
        return "FeedExp {}".format(
            self.base_xp,
        )

    def __repr__(self):
        return "<{}>".format(
            str(self)
        )

    def calc_for_level(self, level):
        return self.base_xp * level


class Element(object):
    def __init__(self, id):
        self.id = id
        pass

    @property
    def long_name(self):
        return ElementIds[self.id].name

    def __str__(self):
        return "Element {}".format(
            self.long_name,
        )

    def __repr__(self):
        return "<{}>".format(
            str(self)
        )

class Type(object):
    def __init__(self, id):
        self.id = id

    @property
    def long_name(self):
        return TypeIds[self.id].name

    def __str__(self):
        return "Type {}".format(
            self.long_name,
        )

    def __repr__(self):
        return "<{}>".format(
            str(self)
        )


class Attribute(object):
    def __init__(self, max, min, scale, owner):
        self.max = int(max)
        self.min = int(min)
        self.scale = int(scale)
        self.owner = owner

    def __str__(self):
        return "Attribute {min}/{max} * {scale}".format(
                min=self.min,
                max=self.max,
                scale=self.scale
        )

    def __repr__(self):
        return "<%s>" % str(self)

    def calc_for_level(self, level):
        lvl_calc = (level-1.0)/(self.owner.max_level-1.0)
        result =  self.min + (self.max - self.min) * lvl_calc ** self.scale
        return round(result)

class Monster(object):
    def __init__(self, **kwargs):
        self.load_data(**kwargs)

    def __str__(self):
        return "#{id} {name} ({rarity})".format(
            id=self.id,
            name=self.name.encode('utf8'),
            rarity=self.rarity*"*",
        )

    def __repr__(self):
        return "<Monster "+str(self)+">"

    def load_data(self, **kwargs):
        self.id = int(kwargs['id'])
        self.version = kwargs['version']

        self.rarity = kwargs['rarity']
        self.max_level = int(kwargs['max_level'])
        self.team_cost = int(kwargs['team_cost'])

        self.feed_xp = FeedXp(kwargs['feed_xp'])
        self.feed_xp_raw = int(kwargs['feed_xp'])

        self.xp_curve = XpCurve(kwargs['xp_curve'])
        self.xp_curve_raw = int(kwargs['xp_curve'])

        self.active_skill = ActiveSkill(0, 'UNSET ACTIVE SKILL', 0, 'UNSET ACTIVE SKILL NAME')
        self.active_skill_name = kwargs['active_skill']

        # self.awoken_skills_name = Awakening(kwargs['awoken_skills'])
        self.awoken_skills = kwargs['awoken_skills']

        self.leader_skill = LeaderSkill('UNSET LEADER SKILL', 'UNSET LEADER SKILL', [0, 0, 0, []])
        self.leader_skill_name = kwargs['leader_skill']

        self.element = Element(kwargs['element'])
        self.element_id = int(kwargs['element'])
        self.element2 = Element(kwargs['element2'])
        self.element2_id = int(kwargs['element2']) if kwargs['element2'] else 0

        self.type = Type(kwargs['type'])
        self.type_id = int(kwargs['type']) if kwargs['type'] else 0
        self.type2 = Type(kwargs['type2'])
        self.type2_id = int(kwargs['type2']) if kwargs['type2'] else 0


        self.hp = Attribute(
            kwargs['hp_max'],
            kwargs['hp_min'],
            kwargs['hp_scale'],
            self,
        )
        self.atk = Attribute(
            kwargs['atk_max'],
            kwargs['atk_min'],
            kwargs['atk_scale'],
            self,
        )
        self.rcv = Attribute(
            kwargs['rcv_max'],
            kwargs['rcv_min'],
            kwargs['rcv_scale'],
            self,
        )

        self.name = kwargs['name']
        self.name_jp = kwargs['name_jp']

        self.image40 = Image(
            40,
            kwargs['image40_href'],
            kwargs['image40_size'],
            self,
        )

        self.image60 = Image(
            60,
            kwargs['image60_href'],
            kwargs['image60_size'],
            self,
        )

        self.jp_only = kwargs['jp_only']

class EvolutionComponent(object):
    def __init__(self, monster_id, count, owner):
        self.monster_id = monster_id
        self.count = count

class Evolution(object):
    def __init__(self, monster_id, is_ultimate, evolves_to, materials):
        self.monster_id = int(monster_id)
        self.is_ultimate = is_ultimate
        self.evolves_to = int(evolves_to)

        self.load_materials(materials)

    def __str__(self):
        return "Evolution: {base} -> {into}".format(
            base=self.monster_id,
            into=self.evolves_to,
        )

    def pretty(self, pad):
        return "Evolution: {base} -> {into}".format(
            base=str(pad.get_monster(self.monster_id)),
            into=str(pad.get_monster(self.evolves_to)),
        )

    def __repr__(self):
        return "<{str}>".format(
            str=str(self)
        )

    def load_materials(self, materials):
        self.materials = []
        for m_id, count in materials:
            material = EvolutionComponent(m_id, count, self)
            self.materials.append(material)

class EvolutionManager(BaseManager):
    identifier = "monster_id"
    can_find_many = True

    nested_dict = True

    @property
    def model(self):
        return Evolution

    def build_obj(self, monster_id, **evo_data):
        return self.model(
            monster_id,
            evo_data['is_ultimate'],
            evo_data['evolves_to'],
            evo_data['materials'],
        )

    def get_by_evolves_to(self, evolves_to):
        objects =  filter(lambda obj: obj.evolves_to == evolves_to, self.objects)
        return objects

class LeaderSkillConstraint(object):
    def __init__(self, const_type, val):
        self.const_type = ConstraintIds[const_type]
        self.load_val(val)

    def __str__(self):
        return "LSContraint: {pretty}".format(
            pretty=self.pretty(),
        )

    def pretty(self):
        return "{eot}:{val}".format(
            eot=self.const_type.value,
            val=self.val.name,
        )

    def load_val(self, val):
        if self.const_type != ConstraintTypes.NoneSet:
            val_enum = ConstraintMap[self.const_type]
            self.val = val_enum[int(val)]
        else:
            self.val = -1

    def __repr__(self):
        return "<{}>".format(str(self))

class LeaderSkillData(object):
    def __init__(self, hp, atk, rcv, *constraints):
        self.hp = hp
        self.atk = atk
        self.rcv = rcv
        self.load_constraints(constraints)

    def __str__(self):
        return "LSData: HPx{hp}/ATKx{atk}/RCVx{rcv} for {cnsts}".format(
            hp=self.hp,
            atk=self.atk,
            rcv=self.rcv,
            cnsts=" ".join([csnt.pretty() for csnt in self.constraints]),
        )

    def load_constraints(self, constraints):
        self.constraints = []
        for csnt in constraints:
            if not csnt:
                lsc = LeaderSkillConstraint('none', -1)
            else:
                lsc = LeaderSkillConstraint(csnt[0], csnt[1])
            self.constraints.append(lsc)

class LeaderSkill(object):
    def __init__(self, name, effect, data=None):
        self.name = name
        self.effect = effect
        self.load_data(data)

    def __str__(self):
        return "LeaderSkill: {name}".format(
            name=self.name.encode('utf8')
        )

    def __repr__(self):
        return "<{}>".format(str(self))

    def load_data(self, data):
        if data:
            self.data = LeaderSkillData(*data)
        else:
            self.data = None


class LeaderSkillManager(BaseManager):
    identifier = "name"

    @property
    def model(self):
        return LeaderSkill

    def build_obj(self, **kwargs):
        return self.model(**kwargs)

    def get_for_monster(self, monster):
        ls = self.get_by_id(monster.leader_skill_name)
        return ls


class Awakening(object):
    def __init__(self, id, name, description):
        self.id = int(id)
        self.name = name
        self.description = description

    def __str__(self):
        return "Awakening: #{id} {name}".format(
            id=self.id,
            name=self.name.encode('utf8'),
        )

    def __repr__(self):
        return "<{str}>".format(
            str=str(self)
        )

class AwakeningManager(BaseManager):
    @property
    def model(self):
        return Awakening

    def build_obj(self, **kwargs):
        return self.model(
            kwargs['id'],
            kwargs['name'],
            kwargs['desc'],
        )

    def get_for_monster(self, monster):
        awakes = []
        for awk_id in monster.awoken_skills:
            awk = self.get_by_id(awk_id)
            awakes.append(awk)
        return awakes
