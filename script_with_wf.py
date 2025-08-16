import os
import sys
# allow for import of features

sys.path.append(os.path.abspath("."))

from features_wf import interp_workflow0

def main():
    global wf_file, inFile, outFile
    text = ""
    with open(f"{wf_file}") as wf:
        text = wf.read()
    # print(text)
    return interp_workflow0(f"(with (inFile (make-string {inFile})) (with (outFile (make-string {outFile}))"+text+"))")


main()

