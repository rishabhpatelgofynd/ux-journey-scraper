#!/bin/bash
set -e

ANDROID_HOME="$HOME/Library/Android/sdk"
export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"

echo "=== Step 1: Boot emulator if not running ==="
BOOTED=$(emulator -list-avds 2>/dev/null | head -1)
RUNNING=$(adb devices 2>/dev/null | grep "emulator" | grep "device" || true)

if [ -z "$RUNNING" ]; then
    echo "Starting emulator: $BOOTED"
    emulator -avd "$BOOTED" -no-snapshot-save &
    EMULATOR_PID=$!
    echo "Waiting for emulator to boot (this takes ~60s)..."
    adb wait-for-device
    # Wait for full boot
    until adb shell getprop sys.boot_completed 2>/dev/null | grep -q "1"; do
        sleep 3
    done
    echo "Emulator ready."
else
    echo "Emulator already running: $RUNNING"
fi

echo ""
echo "=== Step 2: Start Appium if not running ==="
if ! curl -s http://localhost:4723/status > /dev/null 2>&1; then
    echo "Starting Appium..."
    ANDROID_HOME="$ANDROID_HOME" appium --port 4723 &
    APPIUM_PID=$!
    sleep 5
    echo "Appium started."
else
    echo "Appium already running."
fi

echo ""
echo "=== Step 3: Run crawl ==="
cd /Users/rishabhpatel/BayMAAR/packages/ux-journey-scraper
rm -rf test_native_android/

ux-journey crawl --config scrape-config-native-android-test.yaml --output-dir test_native_android/
