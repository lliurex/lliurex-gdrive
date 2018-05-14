#!/bin/bash

xgettext --join-existing ../lliurex-gdrive-gui.install/usr/share/lliurex-gdrive/ProfileBox.py -o ./lliurex-gdrive-gui/lliurex-gdrive.pot
xgettext --join-existing ../lliurex-gdrive-gui.install/usr/share/lliurex-gdrive/LliurexGdrive.py -o ./lliurex-gdrive-gui/lliurex-gdrive.pot
xgettext --join-existing ../lliurex-gdrive-gui.install/usr/share/lliurex-gdrive/rsrc/lliurex-gdrive.ui  -o ./lliurex-gdrive-gui/lliurex-gdrive.pot
xgettext --join-existing -L python ../lliurex-gdrive-indicator.install/usr/bin/lliurexGdriveIndicator -o ./lliurex-gdrive-gui/lliurex-gdrive.pot