import sgtk
from sgtk.platform.qt import QtCore, QtGui


task_manager = sgtk.platform.import_framework(
    'tk-framework-shotgunutils',
    'task_manager',
)
shotgun_search_widget = sgtk.platform.import_framework(
    'tk-framework-qtwidgets',
    'shotgun_search_widget',
)


def FieldLabel(text):
    """Blue Label styled to match Comments: from header image."""

    return QtGui.QLabel('<p style="color:#30a7e3"><b>{}</b></p>'.format(text))


def HSeparator():
    """Horizontal Separator."""

    frame = QtGui.QFrame()
    frame.setFrameShape(frame.HLine)
    frame.setFrameShadow(frame.Sunken)
    return frame


class ContextSelectorDialog(QtGui.QDialog):

    Select = 0
    New = 1

    def __init__(self, app, message, defaults=None, parent=None):
        super(ContextSelectorDialog, self).__init__(parent)

        # Bind appplication
        self.app = app

        # Setup for GlobalSearchWidgets
        self._entity = None
        self._template = None
        self._parent = None
        self._task_manager = task_manager.BackgroundTaskManager(
            parent=self,
            start_processing=True,
            max_threads=2,
        )

        # Header
        self.message = QtGui.QLabel(message)
        self.message.setWordWrap(True)
        self.message.setMinimumHeight(24)

        # Select tab
        self.entity_selector = shotgun_search_widget.GlobalSearchWidget(self)
        self.entity_selector.set_searchable_entity_types({
            entity_type: []
            for entity_type in self.supported_entity_types
        })
        self.entity_selector.set_bg_task_manager(self._task_manager)
        self.entity_selector.completer().entity_activated.disconnect(self.entity_selector.clear)

        self.select_tab_layout = QtGui.QFormLayout()
        self.select_tab_layout.addRow(FieldLabel('Entity:'), self.entity_selector)

        self.select_tab = QtGui.QWidget()
        self.select_tab.setLayout(self.select_tab_layout)

        # New Tab
        self.entity_name = QtGui.QLineEdit()

        self.entity_type = QtGui.QComboBox()
        self.entity_type.addItems(self.supported_entity_types)

        self.template_selector = shotgun_search_widget.GlobalSearchWidget(self)
        self.template_selector.set_searchable_entity_types({
            'TaskTemplate': [['entity_type', 'is', self.default_entity_type]],
        })
        self.template_selector.set_bg_task_manager(self._task_manager)
        self.template_selector.completer().entity_activated.disconnect(self.template_selector.clear)

        self.parent_selector = shotgun_search_widget.GlobalSearchWidget(self)
        self.parent_selector.set_bg_task_manager(self._task_manager)
        self.parent_selector.completer().entity_activated.disconnect(self.parent_selector.clear)

        self.new_tab_layout = QtGui.QFormLayout()
        self.new_tab_layout.addRow(FieldLabel('Name:'), self.entity_name)
        self.new_tab_layout.addRow(FieldLabel('Type:'), self.entity_type)
        self.new_tab_layout.addRow(FieldLabel('Template:'), self.template_selector)
        self.new_tab_layout.addRow(FieldLabel('Parent:'), self.parent_selector)

        self.new_tab = QtGui.QWidget()
        self.new_tab.setLayout(self.new_tab_layout)

        # Tabs Widget
        self.tabs = QtGui.QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.select_tab, 'Select')
        self.tabs.addTab(self.new_tab, 'New')

        # Footer
        self.cancel_button = QtGui.QPushButton('Cancel')
        self.submit_button = QtGui.QPushButton('Submit')

        # Layout
        self.button_layout = QtGui.QHBoxLayout()
        self.button_layout.setAlignment(QtCore.Qt.AlignRight)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.submit_button)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.message)
        layout.addWidget(self.tabs)
        layout.addLayout(self.button_layout)
        self.setLayout(layout)

        # Connect
        self.exit_code = QtGui.QDialog.Rejected
        self.submit_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.submit_button.clicked.connect(self._task_manager.shut_down)
        self.cancel_button.clicked.connect(self._task_manager.shut_down)
        self.entity_selector.entity_activated.connect(self._on_entity_changed)
        self.template_selector.entity_activated.connect(self._on_template_changed)
        self.parent_selector.entity_activated.connect(self._on_parent_changed)
        self.entity_type.currentTextChanged.connect(self._on_entity_type_changed)

        # Window Attributes
        self.setMinimumWidth(400)
        self.setWindowTitle('Select Review Context')
        self.setWindowIcon(QtGui.QIcon(app.icon_256))

        if defaults:
            self.set_options(defaults)

    def closeEvent(self, event):
        self._task_manager.shut_down()
        event.accept()

    @property
    def default_template(self):
        return self.app.get_setting('task_template')

    @property
    def default_entity_type(self):
        return self.app.get_setting('shotgun_entity_type')

    @property
    def supported_entity_types(self):
        return sorted(set([self.default_entity_type, 'Sequence', 'Shot']))

    @property
    def entity_parent_fields(self):
        return self.app.get_setting('entity_parent_fields')

    def _on_parent_changed(self, type, id, name):
        self._parent = {'type': type, 'id': id, 'code': name}

    def _on_template_changed(self, type, id, name):
        self._template = {'type': type, 'id': id, 'code': name}

    def _on_entity_type_changed(self, entity_type):
        self.update_task_template_filters(entity_type, self.default_template)
        self.update_parent_field(entity_type)

    def _on_entity_changed(self, type, id, name):
        self.set_entity({'type': type, 'id': id, 'code': name})

    def set_mode(self, mode):
        """Sets the active tab to Select or New.

        Modes can be passed using ContextSelectorDialog.Select and New or
        simply 0 and 1.
        """

        self.tabs.setCurrentIndex(mode)

    def set_entity(self, entity):
        """Set the entity option."""

        entity_name = entity.get('name', entity.get('code', ''))
        entity_type = entity.get('type', 'Sequence')
        self.entity_selector.setText(entity_name)
        self._entity = entity

        self.entity_name.setText(entity_name)
        self.entity_type.setCurrentText(entity_type)
        self.update_task_template_filters(entity_type, self.default_template)

    def set_entity_name(self, entity_name):
        """Set the entity_name option."""
        
        self.entity_name.setText(entity_name)

    def set_entity_type(self, entity_type):
        """
        Set the entity_type option.

        Triggers an update of the task template filters as well.
        """
        
        self.entity_type.setCurrentText(entity_type)
        self.update_task_template_filters(entity_type, self.default_template)
        self.update_parent_field(entity_type)

    def set_task_template(self, template, entity_type=None):
        """
        Set the task_template option using a ShotGrid TaskTemplate or code. 

        Arguments:
            template (dict/str): ShotGrid TaskTemplate dict or code.
            entity_type (str): Optional entity_type lookup for TaskTemplate used
                when template is passed as a string.
        """
        
        if isinstance(template, dict):
            self.template_selector.setText(template.get('name', template.get('code', '')))
            self._template = template
            return
        else:
            entity_type = entity_type or self.entity_type.currentText()
            template = self.app.shotgun.find_one(
                'TaskTemplate',
                [['code', 'is', template], ['entity_type', 'is', entity_type]],
                ['code', 'entity_type']
            )
            if template:
                self.template_selector.setText(template['code'])
                self._template = template
                return

        self.template_selector.clear()
        self._template = None

    def update_parent_field(self, entity_type):
        self._parent = None
        field_info = self.entity_parent_fields.get(entity_type)
        if field_info:
            self.parent_selector.set_searchable_entity_types({field_info['entity_type']: []})
            self.parent_selector.show()
            self.new_tab_layout.labelForField(self.parent_selector).show()
        else:
            self.parent_selector.clear()
            self.parent_selector.hide()
            self.new_tab_layout.labelForField(self.parent_selector).hide()


    def update_task_template_filters(self, entity_type, default=None):
        """
        Updates the task template filters based on entity.

        A default value to apply to the TaskTemplate dialog may be provided.
        """

        self.template_selector.set_searchable_entity_types({
            'TaskTemplate': [["entity_type", "is", entity_type]],
        })
        if default:
            self.set_task_template(default, entity_type)

    def set_options(self, options):
        """Convenience method to set multiple options at once."""

        self.app.log_debug('SETTING ENTITY %s' % options.get('entity'))
        if options.get('entity'):
            self.set_entity(options['entity'])

        self.app.log_debug('SETTING MODE %s' % options.get('mode'))
        if options.get('mode'):
            self.set_mode(options['mode'])

        self.app.log_debug('SETTING ENTITY_NAME %s' % options.get('entity_name'))
        if options.get('entity_name'):
            self.set_entity_name(options['entity_name'])

        self.app.log_debug('SETTING ENTITY_TYPE %s' % options.get('entity_type'))
        if options.get('entity_type'):
            self.set_entity_type(options['entity_type'])
        else:
            self.set_entity_type(self.default_entity_type)

        self.app.log_debug('SETTING TASK_TEMPLATE %s' % options.get('task_template'))
        if options.get('task_template'):
            self.set_task_template(options['task_template'])
        else:
            self.set_task_template(self.default_template)

    def get_options(self):
        """Returns the values of this dialogs options as a dict."""

        return {
            'entity': self._entity,
            'mode': self.tabs.currentIndex(),
            'mode_str': ('Select', 'New')[self.tabs.currentIndex()],
            'entity_name': self.entity_name.text(),
            'entity_type': self.entity_type.currentText(),
            'task_template': self._template,
            'parent': self._parent,
        }