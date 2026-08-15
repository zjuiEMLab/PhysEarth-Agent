"""Turning a publisher's article into sections PhysEarth can cite.

Three modules, in the order a paper travels through them:

  jats      parse JATS XML into front matter and titled sections
  discover  ask OpenAlex what exists, with its licence and open-access status
  fulltext  fetch the full text of one open-access paper, by DOI only

None of them holds mutable module state. A paper ingested during a conversation lives in
that conversation's session object and nowhere else, because one Studio process serves
every visitor at once.
"""
