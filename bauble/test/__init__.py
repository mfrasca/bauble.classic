import sys
import unittest

import bauble
import bauble.db as db
from bauble.error import BaubleError
from bauble.prefs import prefs
import bauble.pluginmgr as pluginmgr
from bauble.utils.log import debug

## for sake of testing, just use sqlite3.
uri = 'sqlite:///:memory:'


def init_bauble(uri, create=False):
    try:
        db.open(uri, verify=False)
    except Exception, e:
        print >>sys.stderr, e
        #debug e
    if not bauble.db.engine:
        raise BaubleError('not connected to a database')
    prefs.init()
    pluginmgr.load()
    db.create(create)
    pluginmgr.init(force=True)


def update_gui():
    """
    Flush any GTK Events.  Used for doing GUI testing.
    """
    from gi.repository import Gtk
    while Gtk.events_pending():
        Gtk.main_iteration(block=False)


def check_dupids(filename):
    """
    Return a list of duplicate ids in a glade file
    """
    ids = set()
    duplicates = set()
    import lxml.etree as etree
    tree = etree.parse(filename)
    for el in tree.getiterator():
        elid = el.get('id')
        if elid not in ids:
            ids.add(elid)
        elif elid and elid not in duplicates:
            duplicates.add(elid)
    return list(duplicates)


class BaubleTestCase(unittest.TestCase):

    def setUp(self):
        assert uri is not None, "The database URI is not set"
        init_bauble(uri)
        self.session = db.Session()

    def set_logging_level(self, level, logger='sqlalchemy'):
        logging.getLogger('sqlalchemy').setLevel(level)

    def tearDown(self):
        self.session.close()
        db.metadata.drop_all(bind=db.engine)
        bauble.pluginmgr.commands.clear()
        pluginmgr.plugins.clear()

    # assertIsNone is not available before 2.7
    import sys
    if sys.version_info[:2] < (2, 7):
        def assertIsNone(self, item):
            self.assertTrue(item is None)

