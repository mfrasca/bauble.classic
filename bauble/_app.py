#
# app.py
#
# NOTE: only bauble.py should import this modules

import os, sys, traceback
import gtk
from sqlobject import *
from bauble.plugins import plugins, tools, views, editors
import bauble.utils as utils
from bauble.prefs import prefs
from bauble.utils.log import debug
import datetime
import bauble

DEBUG_SQL = False

class BaubleApp:
    
    conn_name = None
    gui = None
    
    def __init__(self):
        pass

    @staticmethod
    def create_database():
        '''
        create new Bauble database at the current connection
        '''
        # FIXME: for some reason the application locks up when this is called 
        # from gui.on_file_menu_new and an exception is raised, i don't know
        # what is locking it up since on_file_menu_new returns, maybe another
        # loop running somewhere but the app redraws and there is a busy
        # cursor, i also don't understand why tables are still being imported 
        # on error
        bauble.BaubleMetaTable.dropTable(ifExists=True)   
        try:            
            #sqlhub.processConnection.autoCommit = True
            for p in plugins.values():
                p.create_tables()            
            bauble.BaubleMetaTable.createTable()  
            bauble.BaubleMetaTable(name=bauble.BaubleMetaTable.version,
                                   value=str(bauble.version))
        except:
            msg = "Error creating tables. Your database may be corrupt."
            utils.message_details_dialog(msg, traceback.format_exc(),
                                         gtk.MESSAGE_ERROR)
            # should be do a rollback here so that we return to the previous
            # database state, we would first need a begiin at the beginning of 
            # this method for it to work correction i think
        else:
            # create the created timestamp
            t = bauble.BaubleMetaTable(name=bauble.BaubleMetaTable.created, 
                                       value=str(datetime.datetime.now()))
            sqlhub.processConnection.commit()
#        except pysqlite2.dbapi2.OperationalError:
#            msg = "Error creating the database. This sometimes happens " \
#            "when trying to create a SQLite database on a network drive. " \
#            "Try creating the database in a local drive or folder."
#            utils.message_dialog(msg, gtk.MESSAGE_ERROR)

    
    def set_busy(self, busy):
        if self.gui is None:
            return
        self.gui.window.set_sensitive(not busy)
        if busy:
            self.gui.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        else:
            self.gui.window.window.set_cursor(None)
            
            
    def build_connection_uri(self, params):
        template = "%(type)s://%(user)s:%(passwd)s@%(host)s/%(db)s"
        return template % params
                          
                          
    @classmethod
    def open_database(klass, uri, name=None):        
        """
        open a database connection
        """
        #debug(uri) # ** WARNING: this can print your passwd
        try:
            # TODO: should make the global transaction available as
            # bauble.transaction and possible wrap it in a class so
            # we basically make rollback automatically do a begin() and
            # make begin() a NOOP
            #self.db_engine = sqlalchemy.create_engine(uri)
            sqlhub.processConnection = connectionForURI(uri)
            sqlhub.processConnection.getConnection()
            sqlhub.processConnection = sqlhub.processConnection.transaction()
        except Exception, e:
            msg = "Could not open connection.\n\n%s" % str(e)        
            utils.message_details_dialog(msg, traceback.format_exc(), 
                                         gtk.MESSAGE_ERROR)
            return None
                                    
        if name is not None:
            prefs[prefs.conn_default_pref] = name
            prefs.save()
        #return True
    
        # make sure the version information matches or if the bauble
        # table doesn't exists then this may not be a bauble created 
        # database
        warning = "\n\n<i>Warning: If a database does already exists at this "\
                  "connection, creating a new database could corrupt it.</i>"
        try:
            #debug('get version')
            sel = bauble.BaubleMetaTable.selectBy(name=bauble.BaubleMetaTable.version)
            #debug(sel)
            db_version = eval(sel[0].value)
            if db_version[0:2] != bauble.version[0:2]:# compare major and minor
                msg = 'You are using Bauble version %d.%d.%d while the '\
                      'database you have connected to was created with '\
                      'version %d.%d.%d\n\nSome things might not work as '\
                      'or some of your data may become unexpectedly '\
                      'corrupted.'\
                      % (bauble.version[0], bauble.version[1], \
                         bauble.version[2], db_version[0], db_version[1], \
                         db_version[2],)
                utils.message_dialog(msg, gtk.MESSAGE_WARNING)       
                            
            sel = bauble.BaubleMetaTable.selectBy(name=bauble.BaubleMetaTable.created)
            if sel.count() == 0:
                msg = 'The database you have connected to does not have a '\
                      'timestamp for when it was created. This usually means '\
                      'that there was a problem when you created the '\
                      'database.  You like to try to create the database '\
                      'again?' + warning
                if utils.yes_no_dialog(msg):
                    klass.create_database()
                    return klass.open_database(uri, name)
                else:
                    return None
                        
        except Exception:
            debug(traceback.format_exc())
            msg = "The database you have connected to is either empty or " \
                  "wasn't created using Bauble. Would you like to create a " \
                  "create a database at this connection?" + warning
            if utils.yes_no_dialog(msg):
                klass.create_database()
                return klass.open_database(uri, name)
            else:
                return False
    	klass.conn_name = name
        return sqlhub.processConnection
        
        
    def destroy(self, widget, data=None):
        gtk.main_quit()


    def save_state(self):
        # in case we quit before the gui is created
        if hasattr(self, "gui") and self.gui is not None:
            self.gui.save_state()
        prefs.save()
        
        
    def quit(self):
        # TODO: need to sync tables
        #for t in tables.tables.values():
        #    t.sync()
        self.save_state()
        try:
            gtk.main_quit()
        except RuntimeError: # in case main_quit is called before main
            sys.exit(1)
            
    
    def main(self):
        prefs.init() # intialize the preferences

        #import bauble.plugins        
        bauble.plugins.init_plugins() # intialize the plugins      
        
        # open default database on startup
        # import these here to avoid recursive import hell
        
        from bauble.conn_mgr import ConnectionManager#Dialog
        #self.conn = None
        default_conn = prefs[prefs.conn_default_pref]
        while True:            
            cm = ConnectionManager(default_conn)            
            conn_name, uri = cm.start()
            if conn_name is None:
                self.quit()
            if self.open_database(uri, conn_name):
                break
                                
        # now that we have a connection create the gui
        import bauble._gui as gui
    	self.conn_name = conn_name
    	title = "%s %s - %s" % ('Bauble', bauble.version_str, conn_name)        
        self.gui = gui.GUI()
        
        # load the last view open from the prefs
        v = prefs[self.gui.current_view_pref]
        if v is None: # default view is the search view            
            v = str(views["SearchView"])
    
        view_set = False
        for name, view in views.iteritems():
            if v == str(view):
                self.gui.set_current_view(view)
                view_set = True
                # TODO: if this view can't be shown then default to SearchView
                
        if not view_set:
            self.gui.set_current_view(views["SearchView"])
        
        bauble.plugins.start_plugins()
        
        #import profile
        #profile.run('gtk.main()', 'bauble.profile')
        gtk.main()
