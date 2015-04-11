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

