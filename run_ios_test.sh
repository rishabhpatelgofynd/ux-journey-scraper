#!/bin/bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer

# Navigate Safari to Amazon before Appium connects
echo "Opening Amazon.in in Safari..."
xcrun simctl openurl booted https://www.amazon.in
sleep 5  # Wait for page to load

cd /Users/rishabhpatel/BayMAAR/packages/ux-journey-scraper

# Clear previous output
rm -rf test_native_ios/

ux-journey crawl --config scrape-config-native-ios-test.yaml --output-dir test_native_ios/
