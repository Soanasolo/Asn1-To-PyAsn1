# Asn1-To-PyAsn1
This is a Python script that translates a data structure defined in the ASN1 convention into a [PyAsn1](https://github.com/etingof/pyasn1) code. This code is not meant to be full  

# Prerequisites
This code relies on the Python package [asn1tools](https://github.com/eerimoq/asn1tools) for parsing the ASN1 data structure.
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install this package.

```bash
pip install asn1tools
```  

# Usage
In order to generate the PyAsn1 code from the data structure SourceAsn, execute the below command. It will create a file for each module defined in the ASN1 data structure. 

'''bash 
$ python AsnOneToPyAsnOne.py SourceAsn
'''


