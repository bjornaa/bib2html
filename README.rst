===========
bib2html.py
===========

Script for converting a bibtex file to an html file with links.

The intended use is to produce a web page of peer-reviewed articles for
a group of authors. It can produce links to the journal web sites and
also pdfs to the articles themselves. The group of authors can be
highlited among their coauthors. For a simple example see, my own
publication list http://www.imr.no/~bjorn/p...


Usage::
    bib2html.py <bibtex-file> [<html-file>]
    bib2html.py (-h | --help)

By default <html-file> = <bibtex-file>.replace('.bib', '.html')


Bibtex considerations
=====================

The input file should be a valid bibtex file that can be handled by
bibtex or biber. However, the script does not contain a full bibtex
parser so a bibtex file may need some clean-up before use.

Limitations
-----------

- Presently only handles articles presently (other entries are
  silently ignored)
- The entries are written to html in the same order as the input,
  no sorting is done.
- Does not handle all LaTeX compound character constructs
- Does not handle mathematics 

The last limitation is fundamental, a different approach using mathjax
or something is needed if the the journal titles contains lot of mathematics.

Sjekk for utilities som kan sortere bibtex filen.

Extensions
----------

The text should be ASCII or utf-8. If utf-8, latex may need
\usepackage[utf8]{inputenc} in the pre-amble (sjekk)

In the author field, the LaTeX convention for scandinavian characters
{\AE}, {\O}, {\AA}, {\ae}, {\o}, {\aa} are allowed. More such
combined characters may be easily added.

For the input to be handled correctly by bibtex, the title field
may need some LaTeX constructs instead of the utf-8 version. The
present list comes from the articles considered so far and may
easily be extended::

   \texit{...} or \emph{...} for italics (e.g Latin names)
   $^{\circ}$ for ° (degree symbol, unicode: \u00B0)
   \&  for ampersand (&)
TODO: parse an external file for these construct, making the list
user extendable without modifying the source code.
   
Arbitrary html code may be passed on to the html file. This is done
by the construction @comment{html: ....} which is ignored by bibtex.

If the entry has a **doi** field or a **url** field, a link is generated.

A non-standard field of **pdf** can be used to provide a link to the
document itself.

A non-standard field of **star_author** can be used to highlite some
of the authors, for instance yourself or authors from a specific
institution or department. It is not necessary to repeat the full
author name, a substring that uniquely determines it is enough.
(presently LaTeX compound characters are not accepted in the
star_author field). TODO: If the star authors are a fixed group of
people, make it possibly to set it once in the file. Also handle the
same format as the author field.

Installation
============

Outside python standard library, the docopt package is requiered.

The script is in a single python source file, which can be deployed
where needed. TODO: make in installable by pip.

The script is made openly available under the ... license.
