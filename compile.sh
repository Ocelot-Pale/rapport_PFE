#!/bin/bash
CMD=" latexmk -c main.tex"
CMD+="&& latexmk -xelatex main.tex"
CMD+=" && echo 'cleaning log files...' "
CMD+=" && latexmk -c main.tex"
CMD+=" && rm -f *.bbl && rm *.xml"
CMD+=" && echo 'done.' "
eval $CMD   