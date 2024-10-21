import os
import re
from typing import Literal, Union

from sno_py.filetypes.defaults import filetype_defaults, filetype_icons


class FileType:
    def __init__(self) -> None:
        self.defaults = filetype_defaults

    def guess_filetype(self, file_path, content) -> Union[str, Literal["file"]]:
        filename = os.path.basename(file_path)

        extension_matches = []

        for entry in self.defaults:
            for filetype, patterns in entry.items():
                filename_score = self._calculate_score(
                    patterns.get("pattern"), filename
                )
                if filename_score > 0:
                    extension_matches.append((filetype, patterns, filename_score))
        if not extension_matches:
            return "file"

        content_scores = []
        for filetype, patterns, filename_score in extension_matches:
            if "file_pattern" in patterns:
                content_score = self._calculate_score(patterns["file_pattern"], content)
                content_scores.append((filetype, content_score, filename_score))
            else:
                content_scores.append((filetype, 0.1, filename_score))

        sorted_scores = sorted(content_scores, key=lambda x: (x[1], x[2]), reverse=True)

        result = sorted_scores[0][0]
        return result

    def guess_icon_for_file(self, file_path: str, content: str) -> str:
        filetype = self.guess_filetype(file_path, content)
        return self.get_icon_for_filetype(filetype)

    @staticmethod
    def get_icon_for_filetype(filetype: str) -> str:
        return filetype_icons.get(f"seti-{filetype}", filetype_icons.get("seti-text"))

    def add_filetype(self, filetype, filename_pattern, content_pattern=None):
        new_filetype = {
            filetype: {
                "pattern": filename_pattern,
            }
        }

        if content_pattern:
            new_filetype[filetype]["file_pattern"] = content_pattern

        self.defaults.append(new_filetype)

    def _calculate_score(self, pattern, target) -> int:
        if pattern is None or not target:
            return 0
        if isinstance(pattern, list):
            return max(self._calculate_score(p, target) for p in pattern)
        match = re.search(pattern, target)
        return len(match.group()) if match else 0
