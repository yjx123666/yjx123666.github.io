# -*- coding: utf-8 -*-
import arcpy

class Toolbox(object):
    def __init__(self):
        self.label = "Test"
        self.alias = "Test"
        self.tools = [TestTool]

class TestTool(object):
    def __init__(self):
        self.label = "Test Tool"
        self.description = "Test"
        self.canRunInBackground = False

    def getParameterInfo(self):
        return []

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        arcpy.AddMessage("Hello")
