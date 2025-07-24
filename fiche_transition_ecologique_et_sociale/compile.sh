#!/bin/bash
CMD="latexmk -xelatex main.tex"
CMD+=" && echo 'cleaning log files...' "
CMD+=" && latexmk -c main.tex"
CMD+=" && rm -f *.bbl "
CMD+=" && echo 'done.' "
eval $CMD