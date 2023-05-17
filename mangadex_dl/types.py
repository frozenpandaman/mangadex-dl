import typing

Chapters = typing.NewType("Chapters", list[dict])
Scanlators = typing.NewType("Scanlators", list[dict])
Authors = typing.NewType("Authors", list[dict])
MangaInfo = typing.NewType("MangaInfo", typing.NamedTuple)
Tags = typing.NewType("Tags", typing.NamedTuple)
ParseRange = typing.NewType("ParseRange", dict)
Duplicates = typing.NewType("Duplicates", list[list[dict]])
