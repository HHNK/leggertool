# -*- coding: utf-8 -*-
from __future__ import division

import logging
import os
import urllib2

from PyQt4.QtCore import pyqtSignal, QSettings, QModelIndex, QThread
from PyQt4.QtGui import QWidget, QFileDialog, QComboBox
from PyQt4 import QtCore, QtGui

from legger.utils.read_tdi_results import (
    read_tdi_results, write_tdi_results_to_db, read_tdi_culvert_results,
    write_tdi_culvert_results_to_db)
from legger.utils.theoretical_profiles import create_theoretical_profiles, write_theoretical_profile_results_to_db
from legger.sql_models.legger_views import create_legger_views
from pyspatialite import dbapi2 as dbapi
from legger.sql_models.legger_database import LeggerDatabase
from legger.sql_models.legger import HydroObject
from legger.utils.profile_match_a import doe_profinprof, maaktabellen

log = logging.getLogger(__name__)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class ProfileCalculationWidget(QWidget):#, FORM_CLASS):
    """Dialog for selecting model (spatialite and result files netCDFs)"""
    closingDialog = pyqtSignal()

    def __init__(
            self, parent, iface, polder_datasource, ts_datasource,
            parent_class):
        """Constructor

        :parent: Qt parent Widget
        :iface: QGiS interface
        :polder_datasource: Spatialite polder
        :parent_class: the tool class which instantiated this widget. Is used
             here for storing volatile information
        """
        super(ProfileCalculationWidget, self).__init__(parent)

        self.parent_class = parent_class
        self.iface = iface
        self.polder_datasource = polder_datasource
        self.ts_datasource = ts_datasource

        errormessage = "Kies eerst 3di output (model en netCDF) in de 'Select 3di results' van 3di plugin."
        try:
            self.path_model_db = self.ts_datasource.model_spatialite_filepath
        except:
            self.path_model_db = errormessage
        try:
            self.path_result_db = self.ts_datasource.rows[0].spatialite_cache_filepath().replace('\\', '/')
        except:
            self.path_result_db = errormessage
        try:
            self.path_result_nc = str(self.ts_datasource.rows[0].datasource()) #todo: nog aanpassen/verwijderen?
            self.path_result_nc = self.ts_datasource.rows[0].spatialite_cache_filepath().replace('sqlite1', 'nc')
        except:
            self.path_result_nc = errormessage

        if self.path_model_db is None:
            self.path_model_db = errormessage

        self.setup_ui()


    def closeEvent(self, event):
        """

        :return:
        """
        self.closingDialog.emit()
        self.close()
        event.accept()

    def save_spatialite(self):
        """
        Change active modelsource. Called by combobox when selected
        spatialite changed
        :param nr: integer, nr of item selected in combobox
        """

        self.polder_datasource = self.polderSpatialiteComboBox.currentText()
        self.close()

    def execute_step1(self):
        db = LeggerDatabase(
            {
                'db_path': self.polder_datasource
            },
            'spatialite'
        )
        db.create_and_check_fields()
        session = db.get_session()

        session.query(HydroObject)

        try:
            result = read_tdi_results(
                self.path_model_db,
                self.path_result_db,
                self.path_result_nc,
                self.polder_datasource
            )
            self.feedbackmessage = "Databases zijn gekoppeld."

        except:
            self.feedbackmessage = "Databases zijn niet gekoppeld."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

        try:
            write_tdi_results_to_db(result,
                                    self.polder_datasource)

            con_legger = dbapi.connect(self.polder_datasource)
            create_legger_views(con_legger)

            self.feedbackmessage = self.feedbackmessage+"\n3Di resultaten weggeschreven naar polder database."
        except:
            self.feedbackmessage = self.feedbackmessage+"\n3Di resultaten niet weggeschreven naar polder database."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

        try:
            results = read_tdi_culvert_results(
                self.path_model_db,
                self.path_result_nc,
                self.polder_datasource
            )
            self.feedbackmessage = self.feedbackmessage+"\n3Di culverts ingelezen."
        except:
            self.feedbackmessage = self.feedbackmessage+"\n3Di culverts niet ingelezen."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

        try:
            write_tdi_culvert_results_to_db(results,
                                            self.polder_datasource)
            self.feedbackmessage = self.feedbackmessage+"\n3Di culvert resultaten weggeschreven."
        except:
            self.feedbackmessage = self.feedbackmessage+"\n3Di culvert resultaten niet weggeschreven."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)



    def execute_step2(self):

        try:
            profiles = create_theoretical_profiles(self.polder_datasource)
            self.feedbackmessage = "Profielen zijn berekend."
        except:
            self.feedbackmessage = "Profielen konden niet worden berekend."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

        try:
            write_theoretical_profile_results_to_db(profiles,self.polder_datasource)
            self.feedbackmessage = self.feedbackmessage+("\nProfielen opgeslagen in legger db.")
        except:
            self.feedbackmessage = self.feedbackmessage+("\nProfielen niet opgeslagen in legger database.")
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

    def execute_step3(self):

        con_legger = dbapi.connect(self.polder_datasource)
        maaktabellen(con_legger.cursor())
        con_legger.commit()
        doe_profinprof(con_legger.cursor(), con_legger.cursor())
        con_legger.commit()

        self.feedbacktext.setText("De fit % zijn berekend.")

    def setup_ui(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.information_row = QtGui.QHBoxLayout()
        self.information_row.setObjectName(_fromUtf8("Information row"))
        self.upper_row = QtGui.QHBoxLayout()
        self.upper_row.setObjectName(_fromUtf8("Upper row"))
        self.middle_row = QtGui.QHBoxLayout()
        self.middle_row.setObjectName(_fromUtf8("Middle row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))
        self.feedback_row = QtGui.QHBoxLayout()
        self.feedback_row.setObjectName(_fromUtf8("Feedback row"))
        self.exit_row = QtGui.QHBoxLayout()
        self.exit_row.setObjectName(_fromUtf8("Exit row"))

        # Selected file name and location in information groupbox
        self.polder_filename = QtGui.QLineEdit(self)
        self.polder_filename.setText(self.polder_datasource)
        self.polder_filename.setObjectName(_fromUtf8("polder legger filename"))

        self.model_filename = QtGui.QLineEdit(self)
        self.model_filename.setText(self.path_model_db)
        self.model_filename.setObjectName(_fromUtf8("model filename"))

        self.result_filename = QtGui.QLineEdit(self)
        self.result_filename.setText(self.path_result_nc)
        self.result_filename.setObjectName(_fromUtf8("result filename"))

        self.connection_filename = QtGui.QLineEdit(self)
        self.connection_filename.setText(self.path_result_db)
        self.connection_filename.setObjectName(_fromUtf8("connection filename"))

        # Assembling information groubox
        self.box_info = QtGui.QVBoxLayout()
        self.box_info.addWidget(self.polder_filename) # intro text toevoegen aan box.
        self.box_info.addWidget(self.model_filename)
        self.box_info.addWidget(self.result_filename)
        self.box_info.addWidget(self.connection_filename)

        self.groupBox_info = QtGui.QGroupBox(self)
        self.groupBox_info.setTitle("Bestanden gekozen:")
        self.groupBox_info.setLayout(self.box_info) # box toevoegen aan groupbox
        self.information_row.addWidget(self.groupBox_info)

        # Assembling step 1 row
        self.step1_button = QtGui.QPushButton(self)
        self.step1_button.setObjectName(_fromUtf8("Step1"))
        self.step1_button.clicked.connect(self.execute_step1)
        self.groupBox_step1 = QtGui.QGroupBox(self)
        self.groupBox_step1.setTitle("Step1:")
        self.box_step1 = QtGui.QHBoxLayout()
        self.box_step1.addWidget(self.step1_button)
        self.groupBox_step1.setLayout(self.box_step1) # box toevoegen aan groupbox
        self.upper_row.addWidget(self.groupBox_step1)

        # Assembling step 2 row
        self.step2_button = QtGui.QPushButton(self)
        self.step2_button.setObjectName(_fromUtf8("Step2"))
        self.step2_button.clicked.connect(self.execute_step2)
        self.groupBox_step2 = QtGui.QGroupBox(self)
        self.groupBox_step2.setTitle("Step2:")
        self.box_step2 = QtGui.QHBoxLayout()
        self.box_step2.addWidget(self.step2_button)
        self.groupBox_step2.setLayout(self.box_step2) # box toevoegen aan groupbox
        self.middle_row.addWidget(self.groupBox_step2)

        # Assembling step 3 row
        self.step3_button = QtGui.QPushButton(self)
        self.step3_button.setObjectName(_fromUtf8("Step3"))
        self.step3_button.clicked.connect(self.execute_step3)
        self.groupBox_step3 = QtGui.QGroupBox(self)
        self.groupBox_step3.setTitle("Step3:")
        self.box_step3 = QtGui.QHBoxLayout()
        self.box_step3.addWidget(self.step3_button)
        self.groupBox_step3.setLayout(self.box_step3) # box toevoegen aan groupbox
        self.bottom_row.addWidget(self.groupBox_step3)

        # Assembling feedback row
        self.feedbacktext = QtGui.QTextEdit(self)
        self.feedbackmessage = "Nog geen berekening uitgevoerd"
        self.feedbacktext.setText(self.feedbackmessage)
        self.feedbacktext.setObjectName(_fromUtf8("feedback"))

        self.feedback_row.addWidget(self.feedbacktext)

        # Assembling exit row
        self.cancel_button = QtGui.QPushButton(self)
        self.cancel_button.setObjectName(_fromUtf8("Cancel"))
        self.cancel_button.clicked.connect(self.close)
        self.exit_row.addWidget(self.cancel_button)

        self.save_button = QtGui.QPushButton(self)
        self.save_button.setObjectName(_fromUtf8("Save Database and Close"))
        self.save_button.clicked.connect(self.save_spatialite)
        self.exit_row.addWidget(self.save_button)



        # Lay-out in elkaar zetten.
        self.verticalLayout.addLayout(self.information_row)
        self.verticalLayout.addLayout(self.upper_row)
        self.verticalLayout.addLayout(self.middle_row)
        self.verticalLayout.addLayout(self.bottom_row)
        self.verticalLayout.addLayout(self.feedback_row)
        self.verticalLayout.addLayout(self.exit_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Bereken de profielvarianten van de polder", None)) #todo: maak een merge met de poldernaam.
        self.save_button.setText(_translate("Dialog", "Save Database and Close", None))
        self.step1_button.setText(_translate("Dialog", "Connect polder database to 3Di output", None))
        self.step2_button.setText(_translate("Dialog", "Calculate all the hydraulic suitable variants", None))
        self.step3_button.setText(_translate("Dialog", "Calculate the fit % of the calculated profiles within measured profiles", None))
        self.cancel_button.setText(_translate("Dialog", "Cancel", None))
