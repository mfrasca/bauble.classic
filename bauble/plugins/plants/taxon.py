# -*- coding: utf-8 -*-

class Taxon(db.Base):
    """
    :Table name: taxon

    :Columns:
        *epithet*:
        *epithet_author*:

        *hybrid*:
            Hybrid flag

        *cv_group*:
        *trade_name*:

        *label_distribution*:
            UnicodeText
            This field is optional and can be used for the label in case
            str(self.distribution) is too long to fit on the label.

    :Properties:
        *accessions*:

        *vernacular_names*:

        *default_vernacular_name*:

        *synonyms*:

        *distribution*:

    :Constraints:
        The combination of sp, sp_author, hybrid, sp_qual,
        cv_group, trade_name, genus_id
    """
    __tablename__ = 'species'
    __mapper_args__ = {'order_by': ['sp', 'sp_author']}

    parent_id = Column(Integer, ForeignKey('taxon.id'), nullable=True)
    epithet = Column(Unicode(64), index=True)
    rank = Column(Enum('regnum','subregnum','phylum','subphylum',
                       'classis','subclassis','ordo','subordo',
                       'familia','subfamilia','tribus','subtribus',
                       'genus','subgenus','sectio','subsectio',
                       'series','subseries','species','subspecies',
                       'varietas','subvarietas','forma','subforma', 
                       name='taxon_ranks'), index=True)
    sp_author = Column(Unicode(128))

    habit_id = Column(Integer, ForeignKey('habit.id'), default=None)
    habit = relation('Habit', uselist=False, backref='species')

    flower_color_id = Column(Integer, ForeignKey('color.id'), default=None)
    flower_color = relation('Color', uselist=False, backref='species')

    awards = Column(UnicodeText)


class Habit(db.Base):
    __tablename__ = 'habit'

    name = Column(Unicode(64))
    code = Column(Unicode(8), unique=True)

    def __str__(self):
        if self.name:
            return '%s (%s)' % (self.name, self.code)
        else:
            return str(self.code)


class Color(db.Base):
    __tablename__ = 'color'

    name = Column(Unicode(32))
    code = Column(Unicode(8), unique=True)

    def __str__(self):
        if self.name:
            return '%s (%s)' % (self.name, self.code)
        else:
            return str(self.code)


class VernacularName(db.Base):
    """vernacular names associated to a taxon(species). 


    this need not be unique, the same language one vernacular name can
    correspond to several different species. also, one species can have
    several vernacular names, within the same cultural area.

    :Table name: vernacular_name

    :Columns:
        *name*:
            the vernacular name

        *language*:
            a code for a language, optionally followed by a description 
            of the area within the language.
            language is free text and could include something like UK
            or US to identify the origin of the name

        *species_id*:
            key to the species this vernacular name refers to

    :Properties:

    :Constraints:

    """
    __tablename__ = 'vernacular_name'
    name = Column(Unicode(128), nullable=False)
    language = Column(Unicode(128))
    species_id = Column(Integer, ForeignKey('species.id'), nullable=False)
    __table_args__ = (UniqueConstraint('name', 'language',
                                       'species_id', name='vn_index'), {})

    def __str__(self):
        if self.name:
            return self.name
        else:
            return ''


