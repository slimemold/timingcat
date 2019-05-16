# Configurable options.
APP_NAME ?= SexyThyme

UNAME := $(shell uname)
WORK_DIR := .pyinstaller
OUT_DIR := dist
PROJECT_DIR := $(shell pwd)

ifeq ($(UNAME), Darwin)
    ICON_FILE := osx/sexythyme.icns
endif

all: $(OUT_DIR)/$(APP_NAME)

clean:
	rm -rf $(WORK_DIR) $(OUT_DIR)
	rm $(ICON_FILE)

$(OUT_DIR)/$(APP_NAME): *.py osx/* resources/* $(ICON_FILE)
	pyinstaller --noconfirm --onefile --windowed \
            --name $(APP_NAME) \
            --paths $(PROJECT_DIR) \
            --specpath $(WORK_DIR) \
            --workpath $(WORK_DIR) \
            --add-data $(PROJECT_DIR)/resources:resources \
            --osx-bundle-identifier com.5rcc.sexythyme \
            --icon $(ICON_FILE) \
            sexythyme.py

osx/sexythyme.icns: osx/sexythyme.iconset/*
	iconutil -c icns osx/sexythyme.iconset
