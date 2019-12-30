# Configurable options.
APP_NAME ?= Timing Cat
APP_NAME_ESCAPED := $(shell echo "${APP_NAME}" | sed -e 's/ /\\ /g')

UNAME := $(shell uname)
WORK_DIR := .pyinstaller
OUT_DIR := dist
PROJECT_DIR := $(shell pwd)
VERSION := $(shell $(PROJECT_DIR)/timingcat.py --version)
BUILD := $(shell date +"%Y%m%d%H%M%S")

ifeq ($(UNAME), Darwin)
    APP_FILE := $(APP_NAME_ESCAPED).app
    ICON_FILE := $(PROJECT_DIR)/osx/timingcat.icns
    PACKAGE_FILE := $(VERSION) b$(BUILD).zip
endif

all: $(OUT_DIR)/$(PACKAGE_FILE)

clean:
	rm -rf $(WORK_DIR) $(OUT_DIR) $(ICON_FILE)

$(OUT_DIR)/$(APP_FILE): *.py osx/* resources/* $(ICON_FILE)
	echo "build = '$(BUILD)'" > "$(PROJECT_DIR)/build.py"
	pyinstaller --noconfirm --onefile --windowed \
            --name "$(APP_NAME)" \
            --paths "$(PROJECT_DIR)" \
            --specpath "$(WORK_DIR)" \
            --workpath "$(WORK_DIR)" \
            --add-data "$(PROJECT_DIR)/resources:resources" \
            --osx-bundle-identifier com.5rcc.timingcat \
            --icon "$(ICON_FILE)" \
            timingcat.py
	rm "$(PROJECT_DIR)/build.py"

ifeq ($(UNAME), Darwin)
$(ICON_FILE): osx/timingcat.iconset/*
	iconutil -o $@ -c icns osx/timingcat.iconset

$(OUT_DIR)/$(PACKAGE_FILE): $(OUT_DIR)/$(APP_FILE)
	cd $(OUT_DIR); zip -r "$(PACKAGE_FILE)" $(APP_FILE)
endif
