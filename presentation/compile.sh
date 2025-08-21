#!/bin/bash
CMD=" latexmk -c main_presentation.tex"
CMD+="&& latexmk -xelatex main_presentation.tex"
CMD+=" && echo 'cleaning log files...' "
CMD+=" && latexmk -c main_presentation.tex"
CMD+=" && rm -f *.bbl && rm -f *.nav && rm -f *.snm"
CMD+=" && echo 'done.' "
eval $CMD   