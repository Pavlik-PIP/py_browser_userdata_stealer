from collections import namedtuple
from textwrap import TextWrapper

indent = " " * 4
indent_text = TextWrapper(initial_indent=indent, subsequent_indent=indent).fill

Credentials = namedtuple("Credentials", ["url", "username", "password"])


