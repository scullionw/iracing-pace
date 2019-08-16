from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit,
    QFileDialog, QHBoxLayout, QRadioButton, QButtonGroup,
    QSpinBox, QProgressBar, QCheckBox
)
from pathlib import Path
from iracing_web_api import iRacingClient, LoginFailed
from iracing_pace.lapswarm import LapSwarm, EmptyResults, export_plot, interactive_plot
from iracing_pace import credentials
import sys
import os

def main():
    appctxt = ApplicationContext()
    # stylesheet = appctxt.get_resource('styles.qss')
    # appctxt.app.setStyleSheet(open(stylesheet).read())
    appctxt.app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
    return exit_code
    
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.save_location = None
        self.layout = QVBoxLayout()

        self.create_credential_boxes()
        self.create_subsession_box()
        self.create_plot_type_selection()
        self.create_mode_selection()
        self.create_spinbox_settings()
        self.create_file_selection()
        self.create_title_box()
        self.create_go_button()
        self.create_progress_bar()

        # Window settings
        self.setLayout(self.layout)
        self.setFixedSize(800, 600)

    def create_credential_boxes(self):
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        user_pass = credentials.retrieve('iracing')
        if user_pass is None:
            self.email.setPlaceholderText("Email")
            self.password.setPlaceholderText("Password")
        else:
            username, password = user_pass
            self.email.setText(username)
            self.password.setText(password)

        self.layout.addWidget(self.email)
        self.layout.addWidget(self.password)

    def create_subsession_box(self):
        self.subsession = QLineEdit()
        self.subsession.setPlaceholderText("Subsession ID (ie. 27983466)")
        self.layout.addWidget(self.subsession)

    def create_title_box(self):
        self.title = QLineEdit()
        self.title.setPlaceholderText("Enter plot title")
        self.layout.addWidget(self.title)


    def create_plot_type_selection(self):
        radio_buttons = [QRadioButton("Swarm Plot"), QRadioButton("Violin Plot")]
        radio_buttons[0].setChecked(True)  
        button_layout = QHBoxLayout()
        self.plot_type_group = QButtonGroup()

        for index, button in enumerate(radio_buttons):
            button_layout.addWidget(button)
            self.plot_type_group.addButton(button, index)

        self.layout.addLayout(button_layout)

    def create_mode_selection(self):
        radio_buttons = [QRadioButton("Save to file"), QRadioButton("Interactive")]
        slots = [self.file_mode_selected, self.interactive_mode_selected]
        button_layout = QHBoxLayout()
        self.mode_group = QButtonGroup()

        radio_buttons[0].setChecked(True)
        for index, button in enumerate(radio_buttons):
            button.toggled.connect(slots[index])
            button_layout.addWidget(button)
            self.mode_group.addButton(button, index)

        self.layout.addLayout(button_layout)

    def interactive_mode_selected(self, selected):
        if selected:
            self.chosen_file_name.hide()
            self.file_select_button.hide()
            self.title.show()
    
    def file_mode_selected(self, selected):
        if selected:
            self.chosen_file_name.show()
            self.file_select_button.show()
            self.title.hide()

    def create_spinbox_settings(self):
        self.max_drivers = QSpinBox()
        self.max_drivers.setValue(10)
        self.outlier_delta = QSpinBox()
        self.outlier_delta.setValue(3)
        self.yaxis_delta = QSpinBox()
        self.yaxis_delta.setValue(3)

        info = ["Max Drivers", "Outlier Delta", "Y-Axis Delta"]
        options = [self.max_drivers, self.outlier_delta, self.yaxis_delta]
        los = [QHBoxLayout(), QHBoxLayout(), QHBoxLayout()]
        for i, opt, lo in zip(info, options, los):
            lo.addWidget(QLabel(i))
            lo.addWidget(opt)
            self.layout.addLayout(lo)
        
    def create_file_selection(self):
        self.chosen_file_name = QLabel("Please choose file save location.")
        self.chosen_file_name.setWordWrap(True)
        self.file_select_button = QPushButton('Select save location')
        self.file_select_button.clicked.connect(self.query_save_location)
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(self.file_select_button)
        file_selection_layout.addWidget(self.chosen_file_name)
        self.layout.addLayout(file_selection_layout)
    
    def create_go_button(self):
        go_button = QPushButton('Go!')
        go_button.clicked.connect(self.go)
        self.layout.addWidget(go_button)
        self.layout.setAlignment(go_button, Qt.AlignHCenter)
    
    def create_progress_bar(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
    
    def query_save_location(self):
        chosen_filename = QFileDialog.getSaveFileName(self, 'Choose file location for pace graph', os.getcwd(), 'PNG (*.png)')[0]
        self.save_location = Path(chosen_filename)
        self.chosen_file_name.setText(self.save_location.name)


    def go(self):
        self.progress_bar.setValue(80)

        iracing = iRacingClient(self.email.text(), self.password.text())
        results = iracing.subsession_results(int(self.subsession.text()))
        swarm = LapSwarm(results, self.max_drivers.value(), self.outlier_delta.value())

        if self.mode_group.checkedId() == 1:
            title = self.title.text()
            ax = swarm.create_plot(title, self.plot_type_group.checkedId() == 1)
            interactive_plot(ax)
        else:
            if self.save_location is None:
                self.query_save_location()
            
            title = self.save_location.stem
            ax = swarm.create_plot(title, self.plot_type_group.checkedId() == 1)
            file_path = str(self.save_location)
            export_plot(ax, file_path)

        self.progress_bar.setValue(100)

if __name__ == '__main__':
    sys.exit(main())