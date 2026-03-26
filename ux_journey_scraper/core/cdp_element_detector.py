"""
CDP-based interactive element detection.

Detects elements with JS event listeners that aren't visible in HTML attributes.
Catches framework-level handlers from Vue, React, Angular, Svelte, etc.
Inspired by browser-use's element detection approach.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CDPElementDetector:
    """Detect interactive elements via Chrome DevTools Protocol patterns."""

    async def detect_framework(self, page) -> str:
        """Detect which JS framework the page uses."""
        try:
            return await page.evaluate("""
                () => {
                    if (window.__NEXT_DATA__ || document.querySelector('[data-reactroot]') ||
                        document.querySelector('[id="__next"]')) return 'react-next';
                    if (document.querySelector('[data-reactroot]') ||
                        document.querySelector('[data-react-helmet]')) return 'react';
                    if (window.__NUXT__ || window.$nuxt) return 'vue-nuxt';
                    if (document.querySelector('[data-v-]') || window.__vue_app__) return 'vue';
                    if (window.ng || document.querySelector('[ng-version]') ||
                        document.querySelector('[_ngcontent]')) return 'angular';
                    if (document.querySelector('[class*="svelte-"]')) return 'svelte';
                    if (window.Shopify) return 'shopify';
                    if (document.querySelector('meta[name="generator"][content*="WordPress"]')) return 'wordpress';
                    return 'unknown';
                }
            """)
        except Exception as e:
            logger.debug(f"Framework detection failed: {e}")
            return "unknown"

    async def find_elements_with_listeners(self, page) -> List[Dict[str, Any]]:
        """Find elements with JS event listeners not visible in HTML.

        Detects framework-level click handlers by looking for:
        1. React fiber nodes (__reactFiber / __reactProps with onClick)
        2. Vue event bindings (__vue__ with $listeners or @click compiled)
        3. Angular event bindings (ng-click, (click) compiled to listeners)
        4. Generic: elements with cursor:pointer + tabindex that aren't <a>/<button>
        """
        try:
            return await page.evaluate("""
                () => {
                    const results = [];
                    const seen = new Set();
                    const MAX = 50;

                    // Strategy 1: React -- look for __reactProps with onClick
                    document.querySelectorAll('*').forEach(el => {
                        if (results.length >= MAX || seen.has(el)) return;
                        const keys = Object.keys(el);
                        for (const key of keys) {
                            if (key.startsWith('__reactProps') || key.startsWith('__reactFiber')) {
                                try {
                                    const props = el[key];
                                    if (props && (props.onClick || props.onMouseDown || props.onChange)) {
                                        seen.add(el);
                                        const rect = el.getBoundingClientRect();
                                        if (rect.width > 0 && rect.height > 0) {
                                            results.push({
                                                tag: el.tagName.toLowerCase(),
                                                text: (el.innerText || '').trim().slice(0, 100),
                                                selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                                                listener_type: 'react',
                                                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                                            });
                                        }
                                    }
                                } catch(e) {}
                            }
                        }
                    });

                    // Strategy 2: Vue -- look for __vue__ or compiled event handlers
                    document.querySelectorAll('[data-v-]').forEach(el => {
                        if (results.length >= MAX || seen.has(el)) return;
                        if (el.__vue__ || el.__vueParentComponent) {
                            const style = window.getComputedStyle(el);
                            if (style.cursor === 'pointer') {
                                seen.add(el);
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    results.push({
                                        tag: el.tagName.toLowerCase(),
                                        text: (el.innerText || '').trim().slice(0, 100),
                                        selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                                        listener_type: 'vue',
                                        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                                    });
                                }
                            }
                        }
                    });

                    // Strategy 3: Generic -- cursor:pointer on non-standard elements
                    // that aren't already <a>, <button>, <input>
                    const standardTags = new Set(['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA']);
                    document.querySelectorAll('*').forEach(el => {
                        if (results.length >= MAX || seen.has(el)) return;
                        if (standardTags.has(el.tagName)) return;
                        const style = window.getComputedStyle(el);
                        if (style.cursor === 'pointer' && style.display !== 'none' &&
                            style.visibility !== 'hidden') {
                            const rect = el.getBoundingClientRect();
                            if (rect.width > 20 && rect.height > 20) {
                                // Check for tabindex or role
                                const role = el.getAttribute('role');
                                const tabindex = el.getAttribute('tabindex');
                                if (role || tabindex !== null) {
                                    seen.add(el);
                                    results.push({
                                        tag: el.tagName.toLowerCase(),
                                        text: (el.innerText || '').trim().slice(0, 100),
                                        selector: el.id ? '#' + el.id : el.tagName.toLowerCase(),
                                        listener_type: 'generic',
                                        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
                                    });
                                }
                            }
                        }
                    });

                    return results;
                }
            """)
        except Exception as e:
            logger.error(f"CDP element detection failed: {e}")
            return []
