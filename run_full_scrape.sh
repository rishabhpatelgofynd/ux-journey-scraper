#!/bin/bash
export BROWSERBASE_API_KEY="bb_live_Ku5E73QtwjiimMFR9LHduK-L8sA"
export BROWSERBASE_PROJECT_ID="a6d1f747-d182-44ad-aa9e-8cbe4e0520ff"

ux-journey scrape --brand Amazon --platforms web_desktop,web_mobile,native_android --output-dir amazon_full/ --max-pages 5
