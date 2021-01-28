#!/usr/bin/env python
# coding: utf-8


def no_space_or_error(txt, fieldname=None):
    try:
        if " " in txt:
            errtxt = "space not allowed in field"
            if fieldname:
                errtxt += f" '{fieldname}'"
            raise ValueError(errtxt)
    except TypeError as e:
        if fieldname:
            raise TypeError(f"{fieldname} should be a string") from e
        raise
