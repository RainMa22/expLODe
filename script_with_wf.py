import os
import sys
# allow for import of features

sys.path.append(os.path.abspath("."))

from features_wf import interp_workflow0
text = ""
with open(r"{wf_file}") as wf:
    text = wf.read()

# print(text)
interp_workflow0(r"(with (inFile (make-string {inFile})) (with (outFile (make-string {outFile}))"+text+"))")
 