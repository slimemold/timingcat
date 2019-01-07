#!/usr/bin/env bash

WORK_DIR=.pyinstaller
OUT_DIR=out

SCRIPT_DIR=$(dirname $(readlink -e $BASH_SOURCE))
PYINSTALLER_OPTIONS=""

usage() {
    echo "USAGE:"
    echo "    $0 [Options]"
    echo
    echo "Build project into a one-file pyinstaller executable."
    echo
    echo "Options:"
    echo "    -h, --help                  Show this help text"
    echo "    -c, --clean                 Clean pyinstaller build"
    echo "    -o, --out                   Output directory (default=$OUT_DIR)"
}

TEMP=`getopt -o hco: --long help,clean,out:,scour -- "$@"`
if [ $? -ne 0 ]; then
    usage
    exit 0
fi

eval set -- "$TEMP"

while true ; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -c|--clean)
            PYINSTALLER_OPTIONS+=" --clean"
            shift
            ;;
        -o|--out)
            OUT_DIR=$2
            shift 2
            ;;
        --scour)
            rm -rf $WORK_DIR $OUT_DIR
            exit 0
            ;;
        --) shift; break;;
        *) echo "Internal error!" ; exit 3 ;;
    esac
done

pyinstaller --noconfirm --onefile --noconsole \
            --paths $SCRIPT_DIR \
            --specpath $WORK_DIR \
            --workpath $WORK_DIR \
            --distpath $OUT_DIR \
            --add-data $SCRIPT_DIR/resources:resources \
            $PYINSTALLER_OPTIONS \
            sexythyme.py
