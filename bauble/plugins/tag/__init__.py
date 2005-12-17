#
# tag module
#
import os
import gtk
from sqlobject import *
from bauble.plugins import BaublePlugin, BaubleTable, plugins, views, tables
import bauble.paths as paths
import bauble.utils as utils
import bauble


class TagItemGUI:
    '''
    interface for tagging individual items in the results of the SearchView
    '''
    # TODO: close on 'escape'
    def __init__(self, item):
        path = os.path.join(paths.lib_dir(), 'plugins', 'tag')
        self.glade_xml = gtk.glade.XML(path + os.sep + 'tag.glade')
        self.dialog = self.glade_xml.get_widget('tag_item_dialog')
        self.item_data_label = self.glade_xml.get_widget('items_data')
        self.item = item
        self.item_data_label.set_text(str(self.item))            

        button = self.glade_xml.get_widget('new_button')
        button.connect('clicked', self.on_new_button_clicked)
        
        
    def on_new_button_clicked(self, *args):
        '''
        create a new tag name
        '''
        d = gtk.Dialog("Enter a connection name", None,
                       gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                       (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        d.set_default_response(gtk.RESPONSE_ACCEPT)
        d.set_default_size(250,-1)
        entry = gtk.Entry()
        entry.connect("activate", lambda entry: d.response(gtk.RESPONSE_ACCEPT))
        d.vbox.pack_start(entry)
        d.show_all()
        d.run()
        name = entry.get_text()
        d.destroy()
        print name
        if name is not "":
            try: # name already exist
                t = Tag.byTag(name)
            except SQLObjectNotFound: # name doesn't exist
                Tag(tag=name)
                model = self.tag_tree.get_model()
                model.append([False, name])
                _reset_tags_menu()
            

    def on_toggled(self, renderer, path, data=None):
        '''
        add tag to self.item
        '''
        active = not renderer.get_active()
        model = self.tag_tree.get_model()
        iter = model.get_iter(path)
        model[iter][0] = active
        name = model[iter][1]
        if active:
            tag_object(name, self.item)
        else:
            untag_object(name, self.item)
            
                    
    def build_tag_tree_columns(self):
        # the toggle column
        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_toggled)
        renderer.set_property('activatable', True)        
        toggle_column = gtk.TreeViewColumn(None, renderer)        
        toggle_column.add_attribute(renderer, "active", 0)
        
        renderer = gtk.CellRendererText()
        tag_column = gtk.TreeViewColumn(None, renderer, text=1)        
        
        return [toggle_column, tag_column]


    def on_key_released(self, widget, event):
        '''
        on delete remove the currently select tag
        '''
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname != "Delete":
            return        
        model, iter = self.tag_tree.get_selection().get_selected()
        tag = model[iter][1]                
        msg = 'Are you sure you want to delete the tag "%s"?' % tag
        if utils.yes_no_dialog(msg):
            t = Tag.byTag(tag)
            t.destroySelf()
            model.remove(iter)
            _reset_tags_menu()
            view = bauble.app.gui.get_current_view()
            view.refresh_search()
    
    
    def start(self):        
        # we keep restarting the dialog here since the gui was created with
        # glade then the 'new tag' button emits a response we want to ignore
        
        self.tag_tree = self.glade_xml.get_widget('tag_tree')
        
        # remove the columns from the tree
        for c in self.tag_tree.get_columns():
            tag_tree.remove_column(c)
        
        # make the new columns
        columns = self.build_tag_tree_columns()
        for col in columns:
            self.tag_tree.append_column(col)
            
        # create the model    
        model = gtk.ListStore(bool, str)
        item_tags = get_tags(self.item)
        has_tag = False
        for tag in Tag.select():
            if tag in item_tags:
                has_tag = True
            model.append([has_tag, tag.tag])
            has_tag = False
        self.tag_tree.set_model(model)
        
        self.tag_tree.add_events(gtk.gdk.KEY_RELEASE_MASK)
        self.tag_tree.connect("key-release-event", self.on_key_released)
        
        response = self.dialog.run()
        while response != gtk.RESPONSE_OK \
          and response != gtk.RESPONSE_DELETE_EVENT:            
            response = self.dialog.run()
        self.dialog.destroy()
    
        
class Tag(BaubleTable):
    tag = UnicodeCol(alternateID=True)
    objects = MultipleJoin('TaggedObj', joinColumn='tag_id')
    
    def __str__(self):
        return self.tag
    def markup(self):
        return '%s Tag' % self.tag
    
    
class TaggedObj(BaubleTable):
    obj_id = IntCol()
    obj_class = StringCol(length=32)
    tag = ForeignKey('Tag', cascade=True)
    
    def __str__():
        return 'tagged_ibj'
    
            
def untag_object(name, so_obj):
    # TODO: should we loop through objects in a tag to delete
    # the TaggedObject or should we delete tags is they match
    # the tag in TaggedObj.selectBy(obj_class=classname, obj_id=so_obj.id)
    tag = None
    try:
        tag = Tag.byTag(name)
    except SQLObjectNotFound:
        return
    for obj in tag.objects:
        # x = obj
        # y = so_obj
        same = lambda x, y:x.obj_class==y.__class__.__name__ and x.obj_id==y.id        
        if same(obj, so_obj):
            obj.destroySelf()
            
       
def tag_object(name, so_obj):     
    try:
        tag = Tag.byTag(name)
    except SQLObjectNotFound:
        tag = Tag(tag=name)
        
    classname = so_obj.__class__.__name__
    sr = TaggedObj.selectBy(obj_class=classname, obj_id=so_obj.id, tag=tag)
    if sr.count() == 0:
        TaggedObj(obj_class=classname, obj_id=so_obj.id, tag=tag)


def get_tags(so_obj):
    classname = so_obj.__class__.__name__
    tagged_objs = TaggedObj.selectBy(obj_class=classname, obj_id=so_obj.id)
    tags = []
    for obj in tagged_objs:
        tags.append(obj.tag)
    return tags
    

# this should create a table tag_plant or plant_tag something like that,
# but what if we want to dump the database and keep these relations

# also, this wouldn't really be useful unless we could tag multiple types
# of items like species, accessions, plants but how do you we do joins on
# multiple types unless we have a PlantTag, AccessionTag and SpeciesTag
# we could manage 

def _on_add_tag_activated(*args):
    # get the selection from the search view
    # TODO: would be better if we could set the sensitivity of the menu
    # item depending on if something was selected in the search view, this
    # means we need to add more hooks to the search view or include the
    # tag plugin into the search view
    view = bauble.app.gui.get_current_view()
    if 'SearchView' in views and isinstance(view, views['SearchView']):
        items = view.get_selected() # right
        if len(items) == 0:
            msg = 'Nothing selected'
            utils.message_dialog(msg)
            return
        # right now we can only tag a single item at a time, if we did
        # the f-spot style quick tagging then it would be easier to handle
        # multiple tags at a time, we could do it we would just have to find
        # the common tags for each of the selected items and then select them
        # but grey them out so you can see that some of the items have that
        # tag but not all of them
        tagitem = TagItemGUI(items[0]) 
        tagitem.start()
    else:
        msg = 'Not a SearchView'
        utils.message_dialog(msg)
    
    
def _tag_menu_item_activated(widget, tag_name):
    view = bauble.app.gui.get_current_view()
    if 'SearchView' in views and isinstance(view, views['SearchView']):
        view.search('tag=%s' % tag_name)
    
    
_tags_menu_item = None

def _reset_tags_menu():
    tags_menu = gtk.Menu()
    add_tag_item = gtk.MenuItem('Tag Selection')
    add_tag_item.connect('activate', _on_add_tag_activated)
    accel_group = gtk.AccelGroup()
    add_tag_item.add_accelerator("activate", accel_group, ord('T'),
                                   gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
    bauble.app.gui.window.add_accel_group(accel_group)        
    tags_menu.append(add_tag_item)
        
    #manage_tag_item = gtk.MenuItem('Manage Tags')
    #tags_menu.append(manage_tag_item)
    tags_menu.append(gtk.SeparatorMenuItem())
        
    for tag in Tag.select():
        item = gtk.MenuItem(tag.tag)            
        item.connect("activate", _tag_menu_item_activated, tag.tag)
        tags_menu.append(item)

    global _tags_menu_item
    if _tags_menu_item is None:
        _tags_menu_item = bauble.app.gui.add_menu("Tags", tags_menu)
    else:
        _tags_menu_item.remove_submenu()
        _tags_menu_item.set_submenu(tags_menu)
        _tags_menu_item.show_all()
        


class TagPlugin(BaublePlugin):
    
    tables = [Tag, TaggedObj]
    depends = ('SearchViewPlugin',)
    
    @classmethod
    def init(cls):
        if "SearchViewPlugin" in plugins:
            from bauble.plugins.searchview.search import SearchMeta
            from bauble.plugins.searchview.search import SearchView
            
            search_meta = SearchMeta("Tag", ["tag"], "tag")
            SearchView.register_search_meta("tag", search_meta)
            
            def get_objects(tag):                
                kids = []
                for obj in tag.objects:
                    kids.append(eval('tables["%s"].get(%d)' \
                                     % (obj.obj_class, obj.obj_id)))
                return kids
                                
            SearchView.view_meta["Tag"].set(get_objects, None, None)
        
            
    @classmethod
    def create_tables(cls):
        BaublePlugin.create_tables()
        if bauble.app.gui is not None:
            _reset_tags_menu() 
        
        
    @classmethod
    def start(cls):    
        _reset_tags_menu() 
        
        
        
plugin = TagPlugin


#if __name__ == '__main__':
#    # for testing
#    sqlhub.processConnection = connectionForURI("sqlite:///tmp/test.sqlite")
#    sqlhub.processConnection.getConnection()
#
#
#    class Person(SQLObject):
#        name = StringCol()
#        def __str__(self):
#            return self.name      	  	
#
#    class Donkey(SQLObject):
#        name = StringCol()    
#        def __str__(self):
#            return self.name
#        
#    tables = [Person, Donkey, TagCategory, Tag, TagObjId, TagIntermediate]
#    def create_tables():
#        for t in tables:
#            t.dropTable(True)
#            t.createTable()
#    create_tables()
#    
#    p = Person(name='Ted')
#    tag_object('human', p)
#    tag_object('hawaiin', p)
#
#    d = Donkey(name='Crapper')
#    tag_object('hawaiin', d)
#
#    for t in get_tags(p):
#        print str(t)
#        print '----------------'
#        for id in t.ids:
#            print '-- ' + str(id)
#        print '\n'

