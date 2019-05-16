# Configurable options.
APP_NAME ?= SexyThyme

UNAME := $(shell uname)
WORK_DIR := .pyinstaller
OUT_DIR := dist
PROJECT_DIR := $(shell pwd)

ifeq ($(UNAME), Darwin)
    APP_FILE := $(APP_NAME).app
    ICON_FILE := osx/sexythyme.icns
    PACKAGE_FILE := SexyThyme.zip
endif

all: $(OUT_DIR)/$(PACKAGE_FILE)

clean:
	rm -rf $(WORK_DIR) $(OUT_DIR)

$(OUT_DIR)/$(APP_FILE): *.py osx/* resources/* $(ICON_FILE)
	pyinstaller --noconfirm --onefile --windowed \
            --name $(APP_NAME) \
            --paths $(PROJECT_DIR) \
            --specpath $(WORK_DIR) \
            --workpath $(WORK_DIR) \
            --add-data $(PROJECT_DIR)/resources:resources \
            --osx-bundle-identifier com.5rcc.sexythyme \
            --icon $(ICON_FILE) \
            sexythyme.py

ifeq ($(UNAME), Darwin)
osx/sexythyme.icns: osx/sexythyme.iconset/*
	iconutil -o $@ -c icns osx/sexythyme.iconset

$(OUT_DIR)/$(PACKAGE_FILE): $(OUT_DIR)/$(APP_FILE)
	cd $(OUT_DIR); zip -r $(PACKAGE_FILE) $(APP_FILE)
endif
