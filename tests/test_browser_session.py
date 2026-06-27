from aria.browser.session import _ReadableHTMLParser


def test_readable_html_parser_extracts_title_and_visible_text():
    parser = _ReadableHTMLParser()
    parser.feed(
        """
        <html>
          <head><title>Example Page</title><style>.hidden { color: red; }</style></head>
          <body>
            <h1>Hello ARIA</h1>
            <script>window.bad = true;</script>
            <p>Visible research content.</p>
          </body>
        </html>
        """
    )

    assert parser.title == "Example Page"
    assert "Hello ARIA" in parser.text
    assert "Visible research content." in parser.text
    assert "window.bad" not in parser.text
