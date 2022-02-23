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

    valid_text = '<p style="color:#30a7e3"><b>{}</b></p>'.format(text)
    invalid_text = '<p style="color:#e33030"><b>{}</b></p>'.format(text)
    label = QtGui.QLabel(valid_text)
    label.setValid = lambda value: label.setText((invalid_text, valid_text)[value])
    return label


def HSeparator():
    """Horizontal Separator."""

    frame = QtGui.QFrame()
    frame.setFrameShape(frame.HLine)
    frame.setFrameShadow(frame.Sunken)
    return frame


class ExtendedSubmitDialog(QtGui.QDialog):

    Select = 0
    New = 1

    def __init__(self, app, message, defaults=None, parent=None):
        super(ExtendedSubmitDialog, self).__init__(parent)

        # Bind appplication
        self.app = app

        # Setup for GlobalSearchWidgets
        self._entity = None
        self._template = None
        self._shot_template = None
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

        # Options
        self.comment = QtGui.QTextEdit()

        # Options Layout
        self.options_layout = QtGui.QFormLayout()
        self.options_layout.addRow(FieldLabel('Comment:'), QtGui.QLabel(''))
        self.options_layout.addRow(self.comment)

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
        layout.addWidget(HSeparator())
        layout.addLayout(self.options_layout)
        layout.addLayout(self.button_layout)
        self.setLayout(layout)

        # Connect
        self.exit_code = QtGui.QDialog.Rejected
        self.submit_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.clicked.connect(self._task_manager.shut_down)
        self.entity_name.textEdited.connect(self._on_entity_name_changed)
        self.entity_selector.entity_activated.connect(self._on_entity_changed)
        self.template_selector.entity_activated.connect(self._on_template_changed)
        self.parent_selector.entity_activated.connect(self._on_parent_changed)
        self.entity_type.currentTextChanged.connect(self._on_entity_type_changed)

        # Window Attributes
        self.setMinimumWidth(400)
        self.setWindowTitle('Submit for ShotGrid review')
        self.setWindowIcon(QtGui.QIcon(app.icon_256))

        if defaults:
            self.set_options(defaults)

    def accept(self):
        if not self.validate():
            # Cancel accept - allow user to fix options...
            return

        self._task_manager.shut_down()
        super(ExtendedSubmitDialog, self).accept()

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

    def _on_entity_changed(self, type, id, name):
        self.set_entity({'type': type, 'id': id, 'code': name})
        label = self.select_tab_layout.labelForField(self.entity_selector)
        label.setValid(True)

    def _on_entity_type_changed(self, entity_type):
        self.update_task_template_filters(entity_type, self.default_template)
        self.update_parent_field(entity_type)

    def _on_entity_name_changed(self, text):
        label = self.new_tab_layout.labelForField(self.entity_name)
        label.setValid(True)

    def set_comment(self, text):
        """Sets the comment field's text."""

        self.comment.setPlainText(text)

    def set_mode(self, mode):
        """Sets the active tab to Select or New.

        Modes can be passed using ExtendedSubmitDialog.Select and New or
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

        if options.get('entity'):
            self.set_entity(options['entity'])

        if options.get('mode'):
            self.set_mode(options['mode'])

        if options.get('entity_name'):
            self.set_entity_name(options['entity_name'])

        if options.get('entity_type'):
            self.set_entity_type(options['entity_type'])
        else:
            self.set_entity_type(self.default_entity_type)

        if options.get('task_template'):
            self.set_task_template(options['task_template'])
        else:
            self.set_task_template(self.default_template)

        if options.get('comment'):
            self.set_comment(options['comment'])

    def get_entity(self):
        if self._entity and self._entity['code'] == self.entity_selector.text():
            return self._entity

    def get_template(self):
        if self._template and self._template['code'] == self.template_selector.text():
            return self._template

    def get_parent(self):
        if self._parent and self._parent['code'] == self.parent_selector.text():
            return self._parent

    def get_options(self):
        """Returns the values of this dialogs options as a dict."""

        return {
            'entity': self.get_entity(),
            'mode': self.tabs.currentIndex(),
            'mode_str': ('Select', 'New')[self.tabs.currentIndex()],
            'entity_name': self.entity_name.text(),
            'entity_type': self.entity_type.currentText(),
            'task_template': self.get_template(),
            'parent': self.get_parent(),
            'comment': self.comment.toPlainText(),
        }

    def validate(self):
        options = self.get_options()
        if options['mode'] == self.Select and not options['entity']:
            label = self.select_tab_layout.labelForField(self.entity_selector)
            label.setValid(False)
            return False

        if options['mode'] == self.New and not options['entity_name']:
            label = self.new_tab_layout.labelForField(self.entity_name)
            label.setValid(False)
            return False

        # Validation is successful, set all labels to Valid
        labels = [
            self.select_tab_layout.labelForField(self.entity_selector),
            self.new_tab_layout.labelForField(self.entity_name),
        ]
        for label in labels:
            label.setValid(True)
        return True