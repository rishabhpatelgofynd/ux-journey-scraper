#!/bin/bash
ux-journey scrape --brand Flipkart --platforms web_desktop,web_mobile --output-dir flipkart_web/ --max-pages 5
ux-journey scrape --brand Amazon --platforms native_android --output-dir amazon_native/ --max-pages 5
