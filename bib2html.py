#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""bib2html.py

Convert bibtex files to html

Usage:
    bib2html.py <bibtex-file> [<html-file>]
    bib2html.py (-h | --help)

By default <html-file> = <bibtex-file>.replace('.bib', '.html')

Options:
    -h --help    Show this help text

"""

# ---------------------------------------------------------------
# bib2html.py
# Script for converting a bibtex file to an html file with links
#
# Conventions for bibtex file
#   The bibtex file is a valid bibtex file
#       may need \usepackage[utf8]{inputenc}
#
# Limitations
# - Only handles articles presently (ignores other entry)
# - Must have commas after each field (also last)
# - Does not handle all LaTeX compound character constructs
#
# Extensions
# The following extensions are ignored by bibtex/biber
#
# Text should be in utf-8, possible extensions:
#   author field: scandinavian letters can follow LaTex convention:
#          {\AE}, {\O}, {\AA}, {\ae}, {\o}, {\aa}
#   title field: to be compatible with bibtex use:
#          \texit{...} or \emph{...} for italics (e.g Latin names)
#          $^{\circ}$ for ° (degree, unicode: \u00B0)
#          \&  for ampersand (&)
#
# @comment{html: html-text} passes html-text to the html-file
# Generates link to the document site (by doi or url field)
# Non-standard pdf field generates direct link to the file
# Non-standard star_author field can be used to highlight some of the authors
#    for instance yourself or authors from a specific institution or department
#
# ------------------------------------------------------------------


# ---------------------------------
# Bjørn Ådlandsvik <bjorn@imr.no>
# Institute of Marine Research
# 2015-06-25
# ---------------------------------

from __future__ import unicode_literals, print_function

import sys
import os
import re
import datetime
import codecs

from docopt import docopt


def main():

    # --- Parse command line ---

    args = docopt(__doc__)
    bibtex_file = args['<bibtex-file>']
    if not bibtex_file.endswith('.bib'):
        sys.exit("First argument must have .bib extension")
    html_file = args['<html-file>']
    if html_file is None:
        html_file = bibtex_file.replace('.bib', '.html')

    # --- Init conversion loop ---

    try:
        fid0 = codecs.open(bibtex_file, encoding='utf-8')
    except IOError:
        sys.exit("Can not open: {}".format(bibtex_file))
    fid1 = codecs.open(html_file, mode='w', encoding='utf-8')

    fid1.write(header)
    in_list = False

    # --- scan/write loop ---

    for entry in get_entry(fid0):

        if entry.type == 'html':
            inc = IncludeHTML(entry)
            if in_list:
                in_list = False
                fid1.write('</ol>\n\n')  # stop list + empty line
            inc.write_html(fid1)

        elif entry.type == 'article':
            art = Article(entry)
            if not in_list:
                in_list = True
                fid1.write('\n<ol>\n')  # Start new list
            art.write_html(fid1)

        else:   # Neglect other content
            continue

    # --- Finalize ---

    if in_list:
        fid1.write('</ol>\n\n')  # stop last list + empty line

    fid1.write(footer)
    fid1.close()

# Some unicode constants
en_dash = '\u2013'
degree = '\u00B0'
nbsp = '\u00A0'  # Non-breakable space
beta = '\u03B2'

# regular expression to extract italic text
textit = re.compile(r'\\textit\{(?P<emph_text>.*?)\}')
# regular expression for \emph{...{...}*...}

emph = re.compile('''
            \\\\(emph|textit){                       # \emph{
            (?P<emph_text>([^{}]*{[^{}]*})*.*?)  # (...{...})*...
            }''', re.VERBOSE)               # }


def untex(s):
    """Replace tex constructs with unicode"""
    s = s.replace('$^{\circ}$', degree)
    s = re.sub(emph, '<i>\g<emph_text></i>', s)
    s = s.replace('\&', '&')
    s = s.replace(r'$\beta$', beta)
    s = s.replace(r'{\AE}', 'Æ')
    s = s.replace(r'{\O}', 'Ø')
    s = s.replace(r'{\AA}', 'Å')
    s = s.replace(r'{\ae}', 'æ')
    s = s.replace(r'{\o}', 'ø')
    s = s.replace(r'{\aa}', 'å')

    return s

# -----------------

# Article class


class Article(object):
    "Class for peer reviewed articles"""

    def __init__(self, entry):
        """Create an Article from an entry

        All fields must end with comma, also last
        The entry must have a single "}" on the last line
        """

        lines = iter(entry.lines)

        # First line must be @article{key
        line = next(lines)
        words = line.split()
        self.key = words[0][9:-1]
        self.fields = []

        # Handle the rest of the lines
        for line in lines:
            words = line.split()
            # Read a field in an entry
            if len(words) > 1 and words[1] == '=':  # New entry
                assert words[1] == '=', "Expting a field in an entry"
                keyword = words[0].lower()
                self.fields.append(keyword)
                data = words[2:]
                # Add continuation lines
                while (data == [] or            # new line after =
                       (not ((data[-1][-2:] in ['",', '},']) or
                             (len(data) == 1 and data[0][-1] == ',') or
                             (data[-1] == '}')))):  # final '}'
                    data.extend(next(lines).split())
                field = " ".join(data)   # Make a single string

                # Remove initial delimiter
                if field[0] in ['"', '{']:
                    field = field[1:]
                # Remove trailing delimiter(s)
                if field[-1] == ',':
                    field = field[:-1]
                if field[-1] in ['"', '}']:
                    field = field[:-1]

                # Clean the entry
                if keyword in ["author", "star_author"]:
                    field = field.split(' and ')
                    for i, auth in enumerate(field):
                        field[i] = auth.replace(' ', nbsp)
                        field[i] = untex(field[i])
                elif keyword == "title":
                    field = untex(field)
                    field = field.replace('{', '')
                    field = field.replace('}', '')
                elif keyword == "journal":
                    field = field.replace(r'\&', '&')
                elif keyword == "pages":
                    field = field.replace('-', en_dash)
                    

                # Set the field-attribute
                setattr(self, keyword, field)

            # Not start of field, not continuation,
            # must be a single end brace, ending the article entry
            else:
                assert words == ['}'], (
                        "Article should end with a single end brace")

    def write_html(self, fid):
        """Write entry to a open html file"""

        nbsp = u'\u00A0'   # Unicode, non-breakable space
        indent = 4*' '
        pdfdir = './pdf'

        # Decorate star authors
        authors = self.author[:]  # Work with a copy
        if hasattr(self, "star_author"):
            for i, auth in enumerate(authors):
                # Check if one of star_authors is a substring
                if [star for star in self.star_author if star in auth]:
                    authors[i] = '<span class="selected">' + auth + '</span>'

        # author
        nauthors = len(authors)
        fid.write('<li>\n')
        fid.write(indent + '<span class="author">\n')
        if nauthors == 1:    # No comma
            fid.write(2*indent + '{:s}\n'.format(authors[0]))
        elif nauthors == 2:  # "and" and no comma
            fid.write(2*indent + '{:s}\n'.format(authors[0]))
            fid.write(2*indent + 'and {:s}\n'.format(authors[1]))
        else:  # commas and "and"
            for auth in authors[:-1]:
                fid.write(2*indent + '{:s},\n'.format(auth))
            fid.write(2*indent + 'and {:s}\n'.format(authors[-1]))
        fid.write(indent + '</span>\n')

        # year
        fid.write(indent)
        fid.write('<span class="year">{:s}</span>,\n'.format(self.year))

        # title
        fid.write(indent + '<span class="title">\n')
        fid.write(2*indent + '{:s}\n'.format(self.title))
        fid.write(indent + '</span>\n')

        # journal
        fid.write(indent)
        fid.write('<span class="journal">{:s}</span>,\n'.format(self.journal))

        # volume
        if hasattr(self, "volume"):
            fid.write(indent)
            fid.write('<span class="volume">')
            fid.write(self.volume)
            fid.write('</span>,\n')

        #  pages
        if hasattr(self, "pages"):
            fid.write(indent)
            fid.write('<span class="pages">')
            fid.write(self.pages)
            fid.write('</span>.\n')

        # Optionally, write doi
        if hasattr(self, "doi") and not hasattr(self, "pages"):
            # Write the doi
            fid.write(indent)
            fid.write('<span class="doi">')
            fid.write('doi:%s' % (self.doi,))
            fid.write('</span>,\n')

        # pdf, link bracket
        # Make URL from DOI if needed
        if hasattr(self, "doi") and not hasattr(self, "url"):
            self.url = 'http://dx.doi.org/' + self.doi

        if hasattr(self, "url") or hasattr(self, "pdf"):
            # Opening bracket
            fid.write(indent + '<br>[' + nbsp)
            if hasattr(self, "pdf"):
                fid.write('<a href="%s/%s/%s">' %
                          (pdfdir, self.year, self.pdf))
                fid.write('pdf')
                fid.write('</a>')

            # Write vertical bar
            if hasattr(self, "pdf") and hasattr(self, "url"):
                fid.write(' |\n')
                fid.write(2*indent + '  ')

            if hasattr(self, "url"):
                fid.write('<a href="%s">' % (self.url,))
                fid.write('link')
                fid.write('</a>')

            # Closing bracket
            fid.write(nbsp + ']\n')

        # End item
        fid.write('</li>\n')


class Entry(object):

    def __init__(self, entry_lines):
        self.lines = entry_lines

        w0 = entry_lines[0].split()[0].lower()   # First word
        if w0.startswith("@article{"):
            self.type = 'article'
        elif w0.startswith("@comment{html,"):
            self.type = 'html'
        else:
            self.type = None  # Neglect other types


def get_entry(fid):
    """Generator for reading a bibtex file entry by entry

    Returns an entry as a list of lines
    An entry is consist of some text + all inside greedy matching braces

    """

    # Filter out empty lines
    lines = (line for line in fid if line.split())

    A = []
    enbrace = 0    # Brace level (=0 outside any braces)
    for line in lines:
        A.append(line.rstrip())
        enbrace += line.count("{") - line.count("}")
        if enbrace == 0:
            yield Entry(A)
            A = []

# ------------------------------------------


class IncludeHTML(object):
    """Class for html content that is passed on to the html file"""

    def __init__(self, entry):
        lines = entry.lines[:]
        # Remove @comment{html,
        lines[0] = lines[0][14:]
        # Remove trailing "}"
        lines[-1] = lines[-1][:-1]
        # Join at separate lines
        self.text = "\n".join(lines)

    def write_html(self, fid):
        """Write the text to an open html file"""

        # Separate the text with blank line before and after
        fid.write("\n")
        fid.write(self.text + "\n")
        fid.write("\n")

header = u'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
    "http://www.w3.org/TR/html4/strict.dtd">

<head>
  <meta http-equiv=Content-Type content="text/html; charset=utf-8">
  <title>Oseano</title>
  <style type="text/css">
     span.selected {color: #0040A0}
     span.author {color: #008000}
     span.title {color: #A00000}
     span.journal {font-style: italic}
     span.volume {font-weight: bold}
     li {margin-top: 8px; margin-bottom: 16px}
   </style>
</head>

<body>

'''

footer = '''

</body>
</html>
'''

beta = '\u03B2'


# --------------------------------

if __name__ == '__main__':
    main()
