WORK_DIR = .pyinstaller
PROJECT_DIR = $(shell pwd)
OUT_DIR ?= out

all: $(OUT_DIR)/sexythyme

clean:
	rm -rf $(WORK_DIR) $(OUT_DIR)

$(OUT_DIR)/sexythyme:
	pyinstaller --noconfirm --onefile --noconsole \
            --paths $(PROJECT_DIR) \
            --specpath $(WORK_DIR) \
            --workpath $(WORK_DIR) \
            --distpath $(OUT_DIR) \
            --add-data $(PROJECT_DIR)/resources:resources \
            --icon=resources/thyme.ico \
            sexythyme.py
