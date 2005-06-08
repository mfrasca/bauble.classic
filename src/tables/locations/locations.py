#
# Locations table definition
#

from sqlobject import *    

class Locations(SQLObject):
    name = "Locations"
    _cacheValue = False

    # should only need either loc_id or site as long as whichever one is 
    # unique, probably site, there is already and internal id
    # what about sublocations, like if the locations were the grounds
    # and the sublocation is the block number
    #loc_id = StringCol(length=20) 
    site = StringCol(length=60, unique=True)
    description = StringCol()

    plant = MultipleJoin("Plants", joinColumn="location_id")
    #plant = ForeignKey('Plants', notNull=True)
    
    def __str__(self): return self.site