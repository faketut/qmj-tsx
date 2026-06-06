// Main paper — Typst source.
//
// Compile: `typst compile paper/main.typ` (output: paper/main.pdf)
// Watch:   `typst watch paper/main.typ`

#set document(
  title: "Quality Minus Junk on TSX Small-Caps",
  author: "Jian Fen",
)
#set page(paper: "us-letter", margin: 1in)
#set par(justify: true, leading: 0.7em)
#set text(font: "New Computer Modern", size: 11pt)
#set heading(numbering: "1.")
#show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em)[
  #set text(weight: "bold", size: 13pt)
  #it.body
]
#show heading.where(level: 2): it => block(above: 1em, below: 0.5em)[
  #set text(weight: "bold", size: 11.5pt)
  #it.body
]
#show link: set text(fill: blue.darken(20%))

#align(center)[
  #text(size: 16pt, weight: "bold")[
    Quality Minus Junk on TSX Small-Caps:\
    A Reproducible Replication and Price-Based Extension
  ]
  #v(0.6em)
  Jian Fen \
  University of Waterloo \
  #datetime.today().display()
]

#v(1em)

#align(center)[
  #block(width: 85%)[
    #set par(justify: true)
    *Abstract.* We replicate the Quality Minus Junk (QMJ) factor of
    Asness, Frazzini, and Pedersen (2019) on Canadian equities using the
    publicly released AQR factor series and extend the framework to TSX
    small-caps with a fundamentals-free quality proxy ("paper-Q")
    constructed from price and return data alone. The paper-Q
    specification trades fundamentals coverage for full reproducibility
    from free data. We report headline returns, risk-adjusted alphas,
    and an extensive robustness battery. All code, data manifests, and
    the build pipeline are open at
    #link("https://github.com/faketut/qmj-tsx")[github.com/faketut/qmj-tsx].
  ]
]

#v(1em)

#include "sections/intro.typ"
#include "sections/data.typ"
#include "sections/methodology.typ"
#include "sections/results.typ"
#include "sections/robustness.typ"
#include "sections/conclusion.typ"

#bibliography("references.bib", style: "chicago-author-date")
