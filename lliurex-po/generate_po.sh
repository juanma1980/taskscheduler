#!/bin/bash

PYTHON_FILES="../scheduler-gui.install/usr/bin/taskScheduler.py ../python3-scheduler.install/usr/share/taskscheduler/*.py"
UI_FILES="../scheduler-gui.install/usr/share/taskScheduler/rsrc/taskScheduler.ui"

mkdir -p taskscheduler/

xgettext $UI_FILES $PYTHON_FILES -o taskscheduler/taskscheduler.pot

