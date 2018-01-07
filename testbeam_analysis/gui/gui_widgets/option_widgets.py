''' Implements option widgets to set function arguments.

    Options can set numbers, strings and booleans.
    Optional options can be deactivated with the value None.
'''

import collections

from PyQt5 import QtWidgets, QtCore, QtGui
from testbeam_analysis.gui.gui_widgets.sliders import IntSlider, FloatSlider


class OptionSlider(QtWidgets.QWidget):
    """
    Option slider for floats and ints. Shows the value as text and can increase range
    """

    valueChanged = QtCore.pyqtSignal(object)  # Either int or float

    def __init__(self, name, default_value, optional, tooltip, dtype, parent=None):
        super(OptionSlider, self).__init__(parent)

        # Store dtype
        self._dtype = dtype
        self.default_value = default_value
        self.update_tooltip(default_value)

        # Slider with textbox to the right
        layout_2 = QtWidgets.QHBoxLayout()
        slider = IntSlider(QtCore.Qt.Horizontal) if 'int' in self._dtype else FloatSlider(QtCore.Qt.Horizontal)
        self.edit = QtWidgets.QLineEdit()
        self.edit.setAlignment(QtCore.Qt.AlignCenter)
        validator = QtGui.QIntValidator() if 'int' in self._dtype else QtGui.QDoubleValidator()
        self.edit.setValidator(validator)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.edit.setSizePolicy(size_policy)
        layout_2.addWidget(slider)
        layout_2.addWidget(self.edit)

        # Option name with slider below
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QLabel(name)
        if tooltip:
            text.setToolTip(tooltip)
        if optional:
            layout_1 = QtWidgets.QHBoxLayout()
            layout_1.addWidget(text)
            layout_1.addStretch(0)
            check_box = QtWidgets.QCheckBox()
            layout_1.addWidget(check_box)
            layout.addLayout(layout_1)
            check_box.stateChanged.connect(lambda v: self._set_readonly(v == 0))
            self._set_readonly()
        else:
            layout.addWidget(text)
        layout.addLayout(layout_2)

        slider.valueChanged.connect(lambda v: self.edit.setText(str(v)))
        slider.valueChanged.connect(lambda _: self._emit_value())
        self.edit.returnPressed.connect(lambda: slider.setMaximum(max((2 * float(self.edit.text())), 1)))
        self.edit.returnPressed.connect(lambda: slider.setValue(float(self.edit.text())))

        if default_value is not None:
            slider.setMaximum(max((2 * default_value), 1))
            slider.setValue(default_value)
            self.edit.setText(str(slider.value()))  # Needed because set value does not issue a value changed

    def update_tooltip(self, val):
        self.setToolTip('Current value: {}, (default value: {})'.format(val, self.default_value))

    def _set_readonly(self, value=True):

        palette = QtGui.QPalette()
        if value:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.gray)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
        else:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)

        self.edit.setReadOnly(value)
        self.edit.setPalette(palette)
        self._emit_value()

    def _emit_value(self):
        if self.edit.isReadOnly() or not self.edit.text():
            value = float('nan') if self.default_value is None else self.default_value
            self.update_tooltip(value)
            self.valueChanged.emit(value)
        else:
            # Separate options that need int dtypes e.g. range(int) from floats
            value = int(self.edit.text()) if 'int' in self._dtype else float(self.edit.text())
            self.update_tooltip(value)
            self.valueChanged.emit(value)


class OptionText(QtWidgets.QWidget):
    """
    Option text for strings
    """

    valueChanged = QtCore.pyqtSignal('QString')

    def __init__(self, name, default_value, optional, tooltip=None, parent=None):
        super(OptionText, self).__init__(parent)

        self.default_value = default_value
        self.update_tooltip(default_value)

        self.edit = QtWidgets.QLineEdit()
        self.edit.setAlignment(QtCore.Qt.AlignCenter)
        layout = QtWidgets.QVBoxLayout(self)

        text = QtWidgets.QLabel(name)
        if optional:
            layout_1 = QtWidgets.QHBoxLayout()
            layout_1.addWidget(text)
            layout_1.addStretch(0)
            check_box = QtWidgets.QCheckBox()
            layout_1.addWidget(check_box)
            layout.addLayout(layout_1)

            check_box.stateChanged.connect(lambda v: self._set_readonly(v == 0))
            if not default_value:
                check_box.setCheckState(0)
                self._set_readonly(True)
        else:
            layout.addWidget(text)

        if tooltip:
            text.setToolTip(tooltip)

        layout.addWidget(self.edit)

        self.edit.textChanged.connect(lambda: self._emit_value())

        if default_value is not None:
            self.edit.setText(default_value)

    def update_tooltip(self, val):
        self.setToolTip('Current value: {}, (default value: {})'.format(val, self.default_value))

    def _set_readonly(self, value=True):

        palette = QtGui.QPalette()
        if value:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.gray)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
        else:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        self.edit.setPalette(palette)
        self.edit.setReadOnly(value)
        self._emit_value()

    def _emit_value(self):
        if self.edit.isReadOnly():
            value = 'None' if self.default_value is None else self.default_value
            self.update_tooltip(value)
            self.valueChanged.emit(value)
        else:
            self.update_tooltip(self.edit.text())
            self.valueChanged.emit(self.edit.text())


class OptionBool(QtWidgets.QWidget):
    """
    Option bool for booleans
    """

    valueChanged = QtCore.pyqtSignal(object)

    def __init__(self, name, default_value, optional, tooltip=None, parent=None):
        super(OptionBool, self).__init__(parent)

        self.default_value = default_value
        self.update_tooltip(default_value)

        self.rb_t = QtWidgets.QRadioButton('True')
        self.rb_f = QtWidgets.QRadioButton('False')
        layout_b = QtWidgets.QHBoxLayout()
        layout_b.addWidget(self.rb_t)
        layout_b.addWidget(self.rb_f)

        layout = QtWidgets.QVBoxLayout(self)

        text = QtWidgets.QLabel(name)

        if optional:
            layout_1 = QtWidgets.QHBoxLayout()
            layout_1.addWidget(text)
            layout_1.addStretch(0)
            check_box = QtWidgets.QCheckBox()
            layout_1.addWidget(check_box)
            layout.addLayout(layout_1)

            check_box.stateChanged.connect(lambda v: self._set_readonly(v == 0))
            if not default_value:
                check_box.setCheckState(0)
                self._set_readonly(True)
        else:
            layout.addWidget(text)

        layout.addLayout(layout_b)

        self.rb_t.toggled.connect(self._emit_value)

        if tooltip:
            text.setToolTip(tooltip)

        if default_value is not None:
            self.rb_t.setChecked(default_value is True)
            self.rb_f.setChecked(default_value is False)

    def update_tooltip(self, val):
        self.setToolTip('Current value: {}, (default value: {})'.format(val, self.default_value))

    def _set_readonly(self, value=True):

        palette = QtGui.QPalette()
        if value:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.gray)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
        else:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        self.rb_f.setPalette(palette)
        self.rb_t.setPalette(palette)
        self.rb_f.setEnabled(not value)
        self.rb_t.setEnabled(not value)
        self._emit_value()

    def _emit_value(self):
        if not self.rb_t.isEnabled() and not self.rb_f.isEnabled():
            value = 'None' if self.default_value is None else self.default_value
            self.update_tooltip(value)
            self.valueChanged.emit(value)
        else:
            self.update_tooltip(self.rb_t.isChecked())
            self.valueChanged.emit(self.rb_t.isChecked())


class OptionMultiSlider(QtWidgets.QWidget):
    """
    Option sliders for several ints or floats. Shows the value as text and can increase range
    """

    valueChanged = QtCore.pyqtSignal(list)

    def __init__(self, name, labels, default_value, optional, tooltip, dtype, parent=None):
        super(OptionMultiSlider, self).__init__(parent)

        # Store dtype
        self._dtype = dtype
        self.default_value = default_value
        self.update_tooltip(default_value)

        # Check default value
        if default_value is None:  # None is only supported for all values
            default_value = 0.
        if not isinstance(default_value, collections.Iterable):
            default_value = [default_value] * len(labels)
        if len(labels) != len(default_value):
            raise ValueError('Number of default values does not match number of parameters')

        max_val = max((max(default_value) * 2, 1))

        # Option name with sliders below
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QLabel(name)
        if tooltip:
            text.setToolTip(tooltip)
        if optional:  # Values can be unset
            layout_1 = QtWidgets.QHBoxLayout()
            layout_1.addWidget(text)
            layout_1.addStretch(0)
            check_box = QtWidgets.QCheckBox()
            layout_1.addWidget(check_box)
            layout.addLayout(layout_1)
        else:
            layout.addWidget(text)

        # List for edits
        self.edits = []

        # Validator for edits
        validator = QtGui.QIntValidator() if 'int' in self._dtype else QtGui.QDoubleValidator()

        for i, label in enumerate(labels):  # Create one slider per label
            # Slider with textbox to the right
            layout_label = QtWidgets.QHBoxLayout()
            slider = IntSlider(QtCore.Qt.Horizontal) if 'int' in self._dtype else FloatSlider(QtCore.Qt.Horizontal)
            # Text edit
            edit = QtWidgets.QLineEdit()
            edit.setAlignment(QtCore.Qt.AlignCenter)
            edit.setValidator(validator)
            size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            edit.setSizePolicy(size_policy)
            layout_label.addWidget(QtWidgets.QLabel('  ' + label))
            layout_label.addWidget(slider)
            layout_label.addWidget(edit)

            # Crazy shit: lambda late binding has to be prevented here
            # http://docs.python-guide.org/en/latest/writing/gotchas/
            slider.valueChanged.connect(lambda v, e=edit: e.setText(str(v)))
            slider.valueChanged.connect(lambda _: self._emit_value())
            edit.returnPressed.connect(lambda s=slider, e=edit: s.setMaximum(max(float(e.text()) * 2, 1)))
            edit.returnPressed.connect(lambda s=slider, e=edit: s.setValue(float(e.text())))

            slider.setMaximum(max_val)
            slider.setValue(default_value[i])
            edit.setText(str(slider.value())) # Needed because set value does not issue a value changed

            self.edits.append(edit)

            layout.addLayout(layout_label)

        if optional:
            check_box.stateChanged.connect(lambda v: self._set_readonly(v == 0))
            self._set_readonly()
        else:
            self._emit_value()  # FIXME: Why is this necessary to correctly set default value? Else one value is missing

    def update_tooltip(self, val):
        self.setToolTip('Current value: {}, (default value: {})'.format(val, self.default_value))

    def _set_readonly(self, value=True):

        palette = QtGui.QPalette()
        if value:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.gray)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
        else:
            palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
        for edit in self.edits:
            edit.setPalette(palette)
            edit.setReadOnly(value)
        self._emit_value()

    def _emit_value(self):
        if not any([edit.isReadOnly() for edit in self.edits]):
            values = [int(edit.text()) if 'int' in self._dtype else float(edit.text()) for edit in self.edits]
        else:
            values = [None] if self.default_value is None else self.default_value
        self.update_tooltip(values)
        self.valueChanged.emit(values)


class OptionMultiCheckBox(QtWidgets.QWidget):
    """
    Option boxes 2(NxN) or 1(N) dimensions
    """

    valueChanged = QtCore.pyqtSignal(list)
    selectionChanged = QtCore.pyqtSignal(dict)

    def __init__(self, name, labels_x, default_value, optional, tooltip, labels_y=None, parent=None):
        super(OptionMultiCheckBox, self).__init__(parent)

        # Store some values
        self.name = name
        self.selection = None
        self.default_value = default_value
        self.update_tooltip(default_value)

        # Different color palettes to visualize disabled widgets
        self.palette_dis = QtGui.QPalette()  # Disabled
        self.palette_dis.setColor(QtGui.QPalette.Base, QtCore.Qt.gray)
        self.palette_dis.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
        self.palette_en = QtGui.QPalette()  # Enabled
        self.palette_en.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
        self.palette_en.setColor(QtGui.QPalette.Text, QtCore.Qt.black)

        # Dimensions of widgets in x and y
        nx = len(labels_x)
        ny = len(labels_y) if labels_y else 1

        # Check default value and create pre-selection
        if default_value is None:  # None is only supported for all values
            if all('Fit' in label for label in labels_x):
                default_value = [[i if i != j else None for i in range(nx)] for j in range(ny)]
                for col in default_value:
                    col.remove(None)
            elif all('Align' in label for label in labels_x):
                default_value = [range(nx)]
            elif ny == 1:
                default_value = range(nx)
            else:
                default_value = [[None] * ny] * nx

        # Option name name with boxes below
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QLabel(name)
        if tooltip:
            text.setToolTip(tooltip)
        if optional:  # Values can be unset
            layout_1 = QtWidgets.QHBoxLayout()
            layout_1.addWidget(text)
            layout_1.addStretch(0)
            check_box_opt = QtWidgets.QCheckBox()
            layout_1.addWidget(check_box_opt)
            layout.addLayout(layout_1)
        else:
            layout.addWidget(text)

        # Layout for boxes
        layout_iter = QtWidgets.QGridLayout()
        offset = 1 if labels_y else 0

        # Store matrix with checkboxes
        self.check_boxes = []

        for i, label in enumerate(labels_x):
            layout_iter.addWidget(QtWidgets.QLabel(label), 0, i + offset, alignment=QtCore.Qt.AlignCenter)
            tmp = []  # Store check boxes for matrix
            k = 0  # Index to set default values
            for j in range(ny):
                if labels_y and not i:
                    layout_iter.addWidget(QtWidgets.QLabel('  ' + labels_y[j]), j + 1, 0)
                check_box = QtWidgets.QCheckBox()
                # Set default values
                try:
                    if default_value[i][k] == j:
                        check_box.setChecked(True)
                        k += 1
                except (TypeError, IndexError):
                    try:
                        if default_value[i] == i:
                            check_box.setChecked(True)
                    except IndexError:
                        pass
                check_box.stateChanged.connect(self._emit_value)
                if name == 'Align duts':
                    check_box.clicked.connect(lambda: self._evaluate_state())
                if ny == 1:
                    self.check_boxes.append(check_box)
                else:
                    tmp.append(check_box)
                layout_iter.addWidget(check_box, j + 1, i + offset, alignment=QtCore.Qt.AlignCenter)
            if ny != 1:
                self.check_boxes.append(tmp)
        layout.addLayout(layout_iter)

        if name == 'Align duts':
            self._evaluate_state(init=True)

        if optional:
            check_box_opt.stateChanged.connect(lambda v: self._set_readonly(v == 0))
            if name == 'Align duts':
                check_box_opt.stateChanged.connect(lambda: self._evaluate_state(init=True))
            self._set_readonly()

    def update_tooltip(self, val):
        self.setToolTip('Current value: {}, (default value: {})'.format(val, self.default_value))

    def _evaluate_state(self, init=False):

        if init:
            empty_rows = []
            for i in range(len(self.check_boxes)):
                tmp = []
                dim = 0 if isinstance(self.check_boxes[i], QtWidgets.QCheckBox) else len(self.check_boxes[i])
                for j in range(dim):
                    if not self.check_boxes[j][i].isChecked():
                        self.check_boxes[j][i].setDisabled(True)
                        self.check_boxes[j][i].setPalette(self.palette_dis)
                    else:
                        tmp.append(j)

                if not tmp:
                    empty_rows.append(i)

            for row in empty_rows:
                try:
                    self.check_boxes[0][row].setChecked(True)
                except TypeError:
                    self.check_boxes[row].setChecked(True)
        else:
            for i in range(len(self.check_boxes)):
                    if self.sender() in self.check_boxes[i]:
                        sender_col = i
                        sender_row = self.check_boxes[i].index(self.sender())

            for j in range(len(self.check_boxes)):
                if j != sender_col:
                    if self.check_boxes[j][sender_row].isEnabled():
                        self.check_boxes[j][sender_row].setChecked(False)
                        self.check_boxes[j][sender_row].setDisabled(True)
                        self.check_boxes[j][sender_row].setPalette(self.palette_dis)
                    else:
                        self.check_boxes[j][sender_row].setDisabled(False)
                        self.check_boxes[j][sender_row].setPalette(self.palette_en)

    def enable_selection(self, selection=None):

        if selection:
            self.selection = selection

        if self.selection and None not in self.selection and not self._all_disabled():

            # Disable all checkboxes
            for cb in self.check_boxes:
                if isinstance(cb, collections.Iterable):
                    for cb_1 in cb:
                        cb_1.setDisabled(True)
                        cb_1.setPalette(self.palette_dis)
                else:
                    cb.setDisabled(True)
                    cb.setPalette(self.palette_dis)

            # Enable checkboxes in selection
            for i in self.selection.keys():
                if isinstance(self.selection[i], collections.Iterable):
                    for j in self.selection[i]:
                        self.check_boxes[i][j].setEnabled(True)
                        self.check_boxes[i][j].setPalette(self.palette_en)
                else:
                    for j in range(len(self.check_boxes)):
                        try:
                            self.check_boxes[i][j].setEnabled(True)
                            self.check_boxes[i][j].setPalette(self.palette_en)
                        except IndexError:
                            self.check_boxes[i].setEnabled(True)
                            self.check_boxes[i].setPalette(self.palette_en)

            # Uncheck checkboxes which were checked before and are not in selection
            for cb in self.check_boxes:
                if isinstance(cb, collections.Iterable):
                    for cb_1 in cb:
                        if cb_1.isChecked() and not cb_1.isEnabled():
                            cb_1.setChecked(False)
                else:
                    if cb.isChecked() and not cb.isEnabled():
                        cb.setChecked(False)

            self._emit_value()

    def _all_disabled(self):

        states = []
        for i in range(len(self.check_boxes)):
            if isinstance(self.check_boxes[i], collections.Iterable):
                for j in range(len(self.check_boxes[i])):
                    states.append(self.check_boxes[i][j].isEnabled())
            else:
                states.append(self.check_boxes[i].isEnabled())
        return not any(states)

    def _get_values(self):

        values = []
        self.duts_vals = {}
        for i in range(len(self.check_boxes)):
            tmp = []
            if isinstance(self.check_boxes[i], collections.Iterable):

                for j in range(len(self.check_boxes[i])):
                    if self.check_boxes[i][j].isChecked() and self.check_boxes[i][j].isEnabled():
                        tmp.append(j)
            else:
                if self.check_boxes[i].isChecked() and self.check_boxes[i].isChecked():
                    values.append(i)
                    self.duts_vals[i] = i
                    continue
            if tmp:
                values.append(tmp)
                self.duts_vals[i] = tmp

        if not values or self._all_disabled():
            values = [None] if self.default_value is None else self.default_value
            self.duts_vals = {}

        return values

    def _set_readonly(self, value=True):

        for cb in self.check_boxes:
            if isinstance(cb, collections.Iterable):
                for cb_1 in cb:
                    cb_1.setPalette(self.palette_dis if value else self.palette_en)
                    cb_1.setDisabled(value)
            else:
                cb.setPalette(self.palette_dis if value else self.palette_en)
                cb.setDisabled(value)
        if not value:
            self.enable_selection()
        self._emit_value()

    def _emit_value(self):
        values = self._get_values()
        self.update_tooltip(values)
        self.valueChanged.emit(values)
        self.selectionChanged.emit(self.duts_vals)


class OptionMultiSpinBox(QtWidgets.QWidget):
    """
    Option spin boxes 2(NxN) or 1(N) dimensions
    """

    valueChanged = QtCore.pyqtSignal(object)
    selectionChanged = QtCore.pyqtSignal(dict)

    def __init__(self, name, labels_x, default_value, optional, tooltip, labels_y=None, parent=None):
        super(OptionMultiSpinBox, self).__init__(parent)

        # Store some values
        self.name = name
        self.selection = None
        self.default_value = default_value
        self.update_tooltip(default_value)

        # Different color palettes to visualize disabled widgets
        self.palette_dis = QtGui.QPalette()  # Disabled
        self.palette_dis.setColor(QtGui.QPalette.Base, QtCore.Qt.gray)
        self.palette_dis.setColor(QtGui.QPalette.Text, QtCore.Qt.darkGray)
        self.palette_en = QtGui.QPalette()  # Enabled
        self.palette_en.setColor(QtGui.QPalette.Base, QtCore.Qt.white)
        self.palette_en.setColor(QtGui.QPalette.Text, QtCore.Qt.black)

        # Dimensions of widgets in x and y
        nx = len(labels_x)
        ny = len(labels_y) if labels_y else 1

        # Check default value
        if default_value is None:  # None is only supported for all values
            default_value = [[None] * ny] * nx

        # Option name name with boxes below
        layout = QtWidgets.QVBoxLayout(self)
        text = QtWidgets.QLabel(name)
        if tooltip:
            text.setToolTip(tooltip)
        if optional:  # Values can be unset
            layout_1 = QtWidgets.QHBoxLayout()
            layout_1.addWidget(text)
            layout_1.addStretch(0)
            check_box_opt = QtWidgets.QCheckBox()
            layout_1.addWidget(check_box_opt)
            layout.addLayout(layout_1)
        else:
            layout.addWidget(text)

        # Layout for spin boxes
        layout_iter = QtWidgets.QGridLayout()
        offset = 1 if labels_y else 0

        # Matrix with checkboxes
        self.spin_boxes = []

        for i, label in enumerate(labels_x):
            layout_iter.addWidget(QtWidgets.QLabel(label), 0, i + offset, alignment=QtCore.Qt.AlignCenter)
            tmp = []
            for j in range(ny):
                if labels_y and not i:
                    layout_iter.addWidget(QtWidgets.QLabel('  ' + labels_y[j]), j + 1, 0)
                spin_box = QtWidgets.QSpinBox()
                spin_box.setRange(default_value - 1, default_value + 1)  # FIXME: should be any range
                spin_box.setValue(default_value)
                spin_box.valueChanged.connect(self._emit_value)

                if ny == 1:
                    self.spin_boxes.append(spin_box)
                else:
                    tmp.append(spin_box)
                layout_iter.addWidget(spin_box, j + 1, i + offset, alignment=QtCore.Qt.AlignCenter)
            if ny != 1:
                self.spin_boxes.append(tmp)
        layout.addLayout(layout_iter)

        if optional:
            check_box_opt.stateChanged.connect(lambda v: self._set_readonly(v == 0))
            self._set_readonly()

    def update_tooltip(self, val):
        self.setToolTip('Current value: {}, (default value: {})'.format(val, self.default_value))

    def enable_selection(self, selection=None):

        if selection:
            self.selection = selection

        if self.selection and None not in self.selection and not self._all_disabled():

            # Disable all spin boxes
            for sb in self.spin_boxes:
                if isinstance(sb, collections.Iterable):
                    for sb_1 in sb:
                        sb_1.setDisabled(True)
                        sb_1.setPalette(self.palette_dis)
                else:
                    sb.setDisabled(True)
                    sb.setPalette(self.palette_dis)

            # Enable spin boxes in selection
            for i in self.selection.keys():
                if isinstance(self.selection[i], collections.Iterable):
                    for j in self.selection[i]:
                        self.spin_boxes[i][j].setEnabled(True)
                        self.spin_boxes[i][j].setPalette(self.palette_en)
                else:
                    for j in range(len(self.spin_boxes)):
                        try:
                            self.spin_boxes[i][j].setEnabled(True)
                            self.spin_boxes[i][j].setPalette(self.palette_en)
                        except IndexError:
                            self.spin_boxes[i].setEnabled(True)
                            self.spin_boxes[i].setPalette(self.palette_en)

            self._emit_value()

    def _all_disabled(self):

        states = []
        for i in range(len(self.spin_boxes)):
            if isinstance(self.spin_boxes[i], collections.Iterable):
                for j in range(len(self.spin_boxes[i])):
                    states.append(self.spin_boxes[i][j].isEnabled())
            else:
                states.append(self.spin_boxes[i].isEnabled())
        return not any(states)

    def _get_values(self):

        values = []
        self.duts_vals = {}
        for i in range(len(self.spin_boxes)):
            tmp = []
            if isinstance(self.spin_boxes[i], collections.Iterable):
                for j in range(len(self.spin_boxes[i])):
                    if self.spin_boxes[i][j].isEnabled():
                        tmp.append(self.spin_boxes[i][j].value())
            else:
                if self.spin_boxes[i].isEnabled():
                    values.append(self.spin_boxes[i].value())
                    self.duts_vals[i] = i
                    continue
            if tmp:
                values.append(tmp)
                self.duts_vals[i] = tmp

        if not values or self._all_disabled():
            # FIXME: Default value of selection_track_quality=1 needs to be set instead of None when optional
            values = [None] if self.default_value is None else self.default_value
            self.duts_vals = {}

        return values

    def _set_readonly(self, value=True):

        for sb in self.spin_boxes:
            if isinstance(sb, collections.Iterable):
                for sb_1 in sb:
                    sb_1.setPalette(self.palette_dis if value else self.palette_en)
                    sb_1.setDisabled(value)
            else:
                sb.setPalette(self.palette_dis if value else self.palette_en)
                sb.setDisabled(value)
        if not value:
            self.enable_selection()
        self._emit_value()

    def _emit_value(self):
        values = self._get_values()
        self.update_tooltip(values)
        self.valueChanged.emit(values)
        self.selectionChanged.emit(self.duts_vals)
