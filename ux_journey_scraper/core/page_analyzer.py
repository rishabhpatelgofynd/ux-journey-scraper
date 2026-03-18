"""
Page analyzer to extract key elements from web pages.
"""
from bs4 import BeautifulSoup


class PageAnalyzer:
    """Extract and analyze page elements (forms, CTAs, navigation, etc.)."""

    async def analyze_page(self, page):
        """
        Analyze a page and extract key elements.

        Args:
            page: Playwright page object

        Returns:
            dict: Page analysis data
        """
        # Get HTML content
        html = await page.content()
        url = page.url
        title = await page.title()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Extract elements
        forms = self._extract_forms(soup)
        ctas = await self._extract_ctas(page)
        navigation = self._extract_navigation(soup)
        buttons = await self._extract_buttons(page)
        links = self._extract_links(soup)

        return {
            'url': url,
            'title': title,
            'html': html,
            'forms': forms,
            'ctas': ctas,
            'navigation': navigation,
            'buttons': buttons,
            'links': links,
            'meta': self._extract_meta(soup)
        }

    def _extract_forms(self, soup):
        """Extract form information."""
        forms = []
        
        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get').upper(),
                'fields': []
            }

            # Extract input fields
            for input_elem in form.find_all(['input', 'select', 'textarea']):
                field = {
                    'type': input_elem.get('type', input_elem.name),
                    'name': input_elem.get('name', ''),
                    'id': input_elem.get('id', ''),
                    'placeholder': input_elem.get('placeholder', ''),
                    'required': input_elem.has_attr('required'),
                    'label': self._find_label_for_input(soup, input_elem)
                }
                form_data['fields'].append(field)

            forms.append(form_data)

        return forms

    def _find_label_for_input(self, soup, input_elem):
        """Find label text for an input element."""
        # Try by 'for' attribute
        input_id = input_elem.get('id')
        if input_id:
            label = soup.find('label', {'for': input_id})
            if label:
                return label.get_text(strip=True)

        # Try parent label
        parent_label = input_elem.find_parent('label')
        if parent_label:
            return parent_label.get_text(strip=True)

        # Try aria-label
        aria_label = input_elem.get('aria-label')
        if aria_label:
            return aria_label

        return ''

    async def _extract_ctas(self, page):
        """Extract Call-To-Action elements."""
        ctas = []

        # Find elements with common CTA text
        cta_texts = [
            'buy now', 'add to cart', 'checkout', 'purchase',
            'sign up', 'register', 'get started', 'try free',
            'subscribe', 'download', 'learn more', 'shop now'
        ]

        for text in cta_texts:
            # Find buttons/links with CTA text
            elements = await page.query_selector_all(
                f'button:has-text("{text}"), a:has-text("{text}"), '
                f'input[type="submit"][value*="{text}"]'
            )

            for elem in elements:
                try:
                    bbox = await elem.bounding_box()
                    cta_data = {
                        'text': await elem.inner_text() if await elem.inner_text() else text,
                        'type': await elem.evaluate('(el) => el.tagName.toLowerCase()'),
                        'position': bbox if bbox else None,
                        'href': await elem.get_attribute('href') if await elem.evaluate('(el) => el.tagName') == 'A' else None
                    }
                    ctas.append(cta_data)
                except:
                    continue

        return ctas

    def _extract_navigation(self, soup):
        """Extract navigation elements."""
        nav_data = {
            'primary_nav': [],
            'breadcrumbs': [],
            'footer_nav': []
        }

        # Primary navigation
        nav_elements = soup.find_all('nav')
        for nav in nav_elements:
            links = nav.find_all('a')
            nav_data['primary_nav'].extend([
                {'text': link.get_text(strip=True), 'href': link.get('href', '')}
                for link in links
            ])

        # Breadcrumbs (common patterns)
        breadcrumb_selectors = [
            {'class': 'breadcrumb'},
            {'class': 'breadcrumbs'},
            {'aria-label': 'breadcrumb'},
            {'id': 'breadcrumb'}
        ]

        for selector in breadcrumb_selectors:
            breadcrumb = soup.find(attrs=selector)
            if breadcrumb:
                links = breadcrumb.find_all('a')
                nav_data['breadcrumbs'].extend([
                    {'text': link.get_text(strip=True), 'href': link.get('href', '')}
                    for link in links
                ])

        # Footer navigation
        footer = soup.find('footer')
        if footer:
            links = footer.find_all('a')
            nav_data['footer_nav'].extend([
                {'text': link.get_text(strip=True), 'href': link.get('href', '')}
                for link in links[:20]  # Limit to first 20
            ])

        return nav_data

    async def _extract_buttons(self, page):
        """Extract button elements with position and size."""
        buttons = []

        button_elements = await page.query_selector_all('button, input[type="button"], input[type="submit"]')

        for button in button_elements[:50]:  # Limit to first 50 buttons
            try:
                text = await button.inner_text()
                bbox = await button.bounding_box()
                
                if bbox:
                    button_data = {
                        'text': text,
                        'position': {
                            'x': int(bbox['x']),
                            'y': int(bbox['y']),
                            'width': int(bbox['width']),
                            'height': int(bbox['height'])
                        },
                        'type': await button.get_attribute('type') or 'button',
                        'disabled': await button.is_disabled()
                    }
                    buttons.append(button_data)
            except:
                continue

        return buttons

    def _extract_links(self, soup):
        """Extract links from the page."""
        links = []
        
        for link in soup.find_all('a', href=True)[:100]:  # Limit to first 100
            links.append({
                'text': link.get_text(strip=True),
                'href': link['href']
            })

        return links

    def _extract_meta(self, soup):
        """Extract meta information."""
        meta = {
            'description': '',
            'keywords': '',
            'viewport': '',
            'og_title': '',
            'og_description': ''
        }

        # Standard meta tags
        desc = soup.find('meta', {'name': 'description'})
        if desc:
            meta['description'] = desc.get('content', '')

        keywords = soup.find('meta', {'name': 'keywords'})
        if keywords:
            meta['keywords'] = keywords.get('content', '')

        viewport = soup.find('meta', {'name': 'viewport'})
        if viewport:
            meta['viewport'] = viewport.get('content', '')

        # Open Graph
        og_title = soup.find('meta', {'property': 'og:title'})
        if og_title:
            meta['og_title'] = og_title.get('content', '')

        og_desc = soup.find('meta', {'property': 'og:description'})
        if og_desc:
            meta['og_description'] = og_desc.get('content', '')

        return meta
