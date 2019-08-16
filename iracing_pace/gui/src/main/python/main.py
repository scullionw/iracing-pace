from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtCore import (
    Qt, QThread, QCoreApplication, pyqtSignal
)
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit,
    QFileDialog, QHBoxLayout, QRadioButton, QButtonGroup,
    QSpinBox, QProgressBar, QCheckBox, QMessageBox
)
from pathlib import Path
from iracing_web_api import iRacingClient, LoginFailed
from iracing_pace.lapswarm import LapSwarm, EmptyResults, export_plot, interactive_plot
from iracing_pace import credentials
import sys
import os
from dataclasses import dataclass

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
        self.create_title_box()
        self.create_run_button()
        self.create_progress_bar()

        # Window settings
        self.setLayout(self.layout)
        self.setFixedSize(800, 600)

    def create_credential_boxes(self):
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)

        user_pass = credentials.retrieve('iracing')
        self.email.setPlaceholderText("Email")
        self.password.setPlaceholderText("Password")
        if user_pass is not None:
            username, password = user_pass
            self.email.setText(username)
            self.password.setText(password)

        self.layout.addWidget(self.email)
        self.layout.addWidget(self.password)

    def create_subsession_box(self):
        self.subsession = QLineEdit()
        self.subsession.setPlaceholderText("Subsession ID (ie. 27983466)")
        self.subsession.setToolTip("Same as the split number when hovering on results icon. Also found in URL of results page.")
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
        button_layout = QHBoxLayout()
        self.mode_group = QButtonGroup()

        radio_buttons[0].setChecked(True)
        for index, button in enumerate(radio_buttons):
            button_layout.addWidget(button)
            self.mode_group.addButton(button, index)

        self.layout.addLayout(button_layout)

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
    
    def create_run_button(self):
        run_button = QPushButton('Run!')
        run_button.clicked.connect(self.run)
        self.layout.addWidget(run_button)
        self.layout.setAlignment(run_button, Qt.AlignHCenter)
    
    def create_progress_bar(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)
    
    def query_save_location(self):
        chosen_filename = QFileDialog.getSaveFileName(self, 'Choose file location for pace graph', os.getcwd(), 'PNG (*.png)')[0]
        self.save_location = Path(chosen_filename)

    def warn(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Error!")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()


    def run(self):
        self.progress_bar.setValue(80)

        if self.mode_group.checkedId() == 0:
            self.query_save_location()

        config = WorkerConfig(
            self.subsession.text(),
            self.email.text(),
            self.password.text(),
            self.max_drivers.value(),
            self.outlier_delta.value(),
            self.mode_group.checkedId() == 1,
            self.plot_type_group.checkedId() == 1,
            self.title.text(),
            self.save_location
        )

        self.worker = Worker(config)
        self.worker.finished.connect(lambda: self.progress_bar.setValue(100))
        self.worker.my_signal.connect(self.warn)
        self.worker.start()

    
        
@dataclass
class WorkerConfig:
    subsession: str
    email: str
    password: str
    max_drivers: int
    outlier_delta: int
    interactive: bool
    violin: bool
    title: str
    save_location: Path

class Worker(QThread):

    my_signal = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        if self.config.subsession == "":
            self.my_signal.emit("Please enter a subsession value.")
            return

        try:
            iracing = iRacingClient(self.config.email, self.config.password)
        except LoginFailed:
            self.my_signal.emit("Login failed! Please check username and password.")
            return
        else:
            credentials.persist('iracing', self.config.email, self.config.password)


        try:
            subsession_number = int(self.config.subsession)
        except ValueError:
            self.my_signal.emit("Bad subsession ID format, should contain only numeric values (ie. 27983466)")
            return
        
        results = iracing.subsession_results(subsession_number)

        try:
            swarm = LapSwarm(results, self.config.max_drivers, self.config.outlier_delta)
        except EmptyResults:
            self.my_signal.emit("No subsession results, please check subsession ID.")
            return
        
        ax = swarm.create_plot(self.config.title, self.config.violin)

        if self.config.interactive:
            interactive_plot(ax)
        else:
            file_path = str(self.save_location)
            export_plot(ax, file_path)


if __name__ == '__main__':
    sys.exit(main())