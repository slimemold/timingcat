# Configurable options.
APP_NAME ?= SexyThyme

WORK_DIR = .pyinstaller
OUT_DIR = dist
PROJECT_DIR = $(shell pwd)

all: $(OUT_DIR)/$(APP_NAME)

clean:
	rm -rf $(WORK_DIR) $(OUT_DIR)

$(OUT_DIR)/$(APP_NAME):
	pyinstaller --noconfirm --onefile --windowed \
	        --name $(APP_NAME) \
            --paths $(PROJECT_DIR) \
            --specpath $(WORK_DIR) \
            --workpath $(WORK_DIR) \
            --add-data $(PROJECT_DIR)/resources:resources \
            --osx-bundle-identifier com.5rcc.sexythyme \
            sexythyme.py
