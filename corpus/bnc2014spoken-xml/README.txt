This is the XML downloadable version of the Spoken BNC2014.

Its contents are listed below. 
 

FILES IN THIS DOWNLOAD
======================

VERSION.txt
 - text file containing only a note of the version of the corpus.
 - see version history, below.

spoken/untagged
 - original XML files, including text headers

spoken/tagged
 - tagged speaker files. No headers, and every token is stored in a <w ... > tag.
   The attributes are:
     - pos   : CLAWS6 part-of-speech tag, see http://ucrel.lancs.ac.uk/claws
     - lemma : word lemma (all-lowercase). 
     - class : simplified POS tag ("wordclass"), following the schmee in the BNC1994 World Edition and later. 
     - usas  : USAS semantic tag, see http://ucrel.lancs.ac.uk/usas
   The adjustments to the basic XML format decribed in the manual for CQPweb are utilised here too.

spoken/metadata
 - text and XML files containing corpus metadata and explanations of codes used in text header/speaker tags. 
   Includes:
     - speakerInfo.xml - all the XML for all corpus speakers (repeated in tyhe file headers of tghe texts where they speak
     - bnc2014spoken-speakerdata.tsv, bnc2014spoken-textdata.tsv - all text and speaker metadata, in tabular form
       (can be imported into Excel or other spreadsheet/database program). 
     - metadata-fields-speaker.txt, metadata-fields-text.txt - files which expand the codes used in the XML header tags (and in CQPweb)
     - metadata-cat-codes-speaker.txt, metadata-cat-codes-text.txt  - files which expand the codes used for categories of speakers/texts

BNC2014manual-1.1.pdf
 - corpus manual and user guide.

Spoken-BNC2014-Licence.pdf
 - end-user licence. You agreed to abide by the terms of this licence when you downloaded the corpus. 


VERSION HISTORY
===============

Version 1.1 - Spoken BNC2014 release as downloadable XML
              Manual updated, some minor encoding errors fixed.
              Autumn 2018.

Version 1.0 - Spoken BNC2014 release via https://cqpweb.lancs.ac.uk
              Autumn 2017.

