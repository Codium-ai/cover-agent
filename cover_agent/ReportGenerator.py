import difflib
from jinja2 import Template


class ReportGenerator:
    # HTML template with fixed code formatting and dark background for the code block
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Results</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.23.0/themes/prism-okaidia.min.css" rel="stylesheet" />
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 20px;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                box-shadow: 0 2px 3px rgba(0,0,0,0.1);
            }
            th, td {
                border: 1px solid #ddd;
                text-align: left;
                padding: 8px;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .status-pass {
                color: green;
            }
            .status-fail {
                color: red;
            }
            pre {
                background-color: #282c34 !important;
                color: #ffffff !important;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                white-space: pre-wrap;
                font-family: 'Courier New', Courier, monospace;
                font-size: 1.1em;  /* Slightly larger font size */
            }
        </style>
    </head>
    <body>
        <table>
            <tr>
                <th>Status</th>
                <th>Reason</th>
                <th>Exit Code</th>
                <th>Language</th>
                <th>Modified Test File</th>
                <th>Details</th>
            </tr>
            {% for result in results %}
            <tr>
                <td class="status-{{ result.status }}">{{ result.status }}</td>
                <td>{{ result.reason }}</td>
                <td>{{ result.exit_code }}</td>
                <td>{{ result.language }}</td>
                <td>
                    <details>
                        <summary>View Full Code</summary>
                        <pre><code>{{ result.full_diff | safe }}</code></pre>
                    </details>
                </td>
                <td>
                    <details>
                        <summary>View More</summary>
                        <div><strong>STDERR:</strong> <pre><code class="language-{{ result.language|lower }}">{{ result.stderr }}</code></pre></div>
                        <div><strong>STDOUT:</strong> <pre><code class="language-{{ result.language|lower }}">{{ result.stdout }}</code></pre></div>
                        <div><strong>Test Code:</strong> <pre><code class="language-{{ result.language|lower }}">{{ result.test_code }}</code></pre></div>
                        <div><strong>Imports:</strong> <pre><code class="language-{{ result.language|lower }}">{{ result.imports }}</code></pre></div>
                    </details>
                </td>
            </tr>
            {% endfor %}
        </table>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.23.0/prism.min.js"></script>
    </body>
    </html>
    """

    @classmethod
    def generate_full_diff(cls, original, processed):
        """
        Generates a full view of both the original and processed test files, 
        highlighting added, removed, and unchanged lines, showing the full code.

        :param original: String content of the original test file.
        :param processed: String content of the processed test file.
        :return: Full diff string formatted for HTML display, highlighting added, removed, and unchanged lines.
        """
        diff = difflib.ndiff(original.splitlines(), processed.splitlines())

        diff_html = []
        for line in diff:
            if line.startswith('+'):
                diff_html.append(f'<span class="diff-added">{line}</span>')
            elif line.startswith('-'):
                diff_html.append(f'<span class="diff-removed">{line}</span>')
            else:
                diff_html.append(f'<span class="diff-unchanged">{line}</span>')
        return '\n'.join(diff_html)

    @classmethod
    def generate_report(cls, results, file_path):
        """
        Renders the HTML report with given results and writes to a file.

        :param results: List of dictionaries with test results.
        :param file_path: Path to the HTML file where the report will be written.
        """
        # Generate the full diff for each result
        for result in results:
            result['full_diff'] = cls.generate_full_diff(result['original_test_file'], result['processed_test_file'])

        template = Template(cls.HTML_TEMPLATE)
        html_content = template.render(results=results)

        with open(file_path, "w") as file:
            file.write(html_content)
