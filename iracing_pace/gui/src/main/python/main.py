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

        # Fields
        self.save_location = None
        layout = QVBoxLayout()


        # Create line edits
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
            
        
        self.subsession = QLineEdit()
        self.subsession.setPlaceholderText("Subsession ID (ie. 27983466)")

        layout.addWidget(self.email)
        layout.addWidget(self.password)
        layout.addWidget(self.subsession)

        # Create setting boxes
        plot_types = [QRadioButton("Swarm Plot"), QRadioButton("Violin Plot")]
        plot_types[0].setChecked(True)  
        button_layout = QHBoxLayout()
        self.plot_type_group = QButtonGroup()

        for i in range(len(plot_types)):
            # Add each radio button to the button layout
            button_layout.addWidget(plot_types[i])
            # Add each radio button to the button group & give it an ID of i
            self.plot_type_group.addButton(plot_types[i], i)
    
        layout.addLayout(button_layout)

        self.interactive = QCheckBox()

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
            layout.addLayout(lo)

        # Create file selection
        self.chosen_file_name = QLabel("Please choose file save location.")
        self.chosen_file_name.setWordWrap(True)
        file_select_button = QPushButton('Select save location')
        file_select_button.clicked.connect(self.query_save_location)
        file_selection_layout = QHBoxLayout()
        file_selection_layout.addWidget(file_select_button)
        file_selection_layout.addWidget(self.chosen_file_name)
        layout.addLayout(file_selection_layout)



        # Launch button
        go_button = QPushButton('Go!')
        go_button.clicked.connect(self.go)
        layout.addWidget(go_button)
        layout.setAlignment(go_button, Qt.AlignHCenter)


        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Window settings
        self.setLayout(layout)
        self.setFixedSize(800, 600)
    
    def query_save_location(self):
        chosen_filename = QFileDialog.getSaveFileName(self, 'Choose file location for pace graph', os.getcwd(), 'PNG (*.png)')[0]
        self.save_location = Path(chosen_filename)
        self.chosen_file_name.setText(self.save_location.name)

    def go(self):
        self.progress_bar.setValue(80)


        iracing = iRacingClient(self.email.text(), self.password.text())
        results = iracing.subsession_results(int(self.subsession.text()))
        swarm = LapSwarm(results, self.max_drivers.value(), self.outlier_delta.value())
        title = self.save_location.stem

        ax = swarm.create_plot(title, False)
        
        if self.interactive.isChecked():
            interactive_plot(ax)
        else:
            file_path = str(self.save_location)
            export_plot(ax, file_path)





        self.progress_bar.setValue(100)

if __name__ == '__main__':
    sys.exit(main())