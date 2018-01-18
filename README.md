# Data

```
.
├── README.md
├── all_fake.sh
├── bdb
│   ├── verbnet-probcomp-999.bdb
│   └── verbnet.bdb
├── fake (tons of fake data in the form ROWSxCOLs-eNOISE-Nclus)
│   └── img (heatmap images of the fake data ^)
├── gen_fake_data.py (Create the fake data ^^)
├── get_prep_literals.py (Parse literals from VN references for ex matrices)
├── irmdata (data from original irm paper (Kemp 2006))
│   ├── 50animalbindat.mat
│   ├── README_DATASETS
│   ├── alyawarradata.mat
│   ├── dnations.mat
│   ├── irmdata\ (1).tar
│   ├── process.R (Process these .mat files and save into parsed/)
│   └── uml.mat
├── lexpreps.txt (Reference - list of lexical tags that might be prepositions (answer YES/NO))
├── new_vn (verbnet version 3.2)
├── notes.txt (verbnet related scratch nodes)
├── parse_verbnet.py (parse ALL verbnet variants and save into parsed/)
├── parse_verbnet.pyc
├── parsed (parsed data: verbnet, prep literals, irmdata. see project
narrative)
├── transpose_csv.py (transposes verbnet csvs if needed)
├── verbnet.py (toplevel verbnet class)
├── verbnet.pyc
├── vncomponents.py (verbnet components (stringification functionality here))
├── vncomponents.pyc
├── vnerrors.py (programmatic error fixing of verbnet)
├── vnerrors.pyc
├── vnparser.py (parses verbnet (parse_verbnet calls this))
├── vnparser.pyc
├── vnutil.py (utility functions shared among all vn* libraries)
└── vnutil.pyc

6 directories, 375 files
```
