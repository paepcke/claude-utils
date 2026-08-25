#!/usr/bin/env python3
# ***********************************
# -*- coding: utf-8 -*-
# @Author: Andreas Paepcke
# @Date:   2026-08-25 09:31:30
# @Last Modified by:   Andreas Paepcke
# @Last Modified time: 2026-08-25 09:49:19
# ***********************************

"""
stage_project_files.py

Copies a curated subset of files from a repository into a clean
destination directory, for batch-uploading into a Claude project's
knowledge base (a workaround for GitHub-sync not reliably working
in the project composer).

:param reporoot: path to the root of the source repository
:param filelist: path to a text file listing one repo-relative file
    path per line (blank lines and lines starting with '#' are
    ignored)
:param destdir: path to the directory to copy staged files into;
    created if it does not exist; existing contents are removed first
:param flatten: if given, filenames are flattened into destdir with
    '/' replaced by '__' (avoids collisions when an uploader only
    supports flat multi-file selection rather than folder drops)

Usage:
    python3 stage_files_for_claude.py \\
        --reporoot /path/to/repo \\
        --filelist files_to_stage.txt \\
        --destdir ./staged \\
        [--flatten]
"""

import argparse
import shutil
import sys
from pathlib import Path


class ProjectFileStager:
    '''Stages a curated file list from a repo into a clean upload directory.'''

    def __init__(self, reporoot, filelist, destdir, flatten=False):
        '''
        :param reporoot: root of the source repository
        :param filelist: path to file with one repo-relative path per line
        :param destdir: destination directory for staged copies
        :param flatten: if True, flatten paths with '__' instead of
            preserving directory structure
        '''
        self.reporoot = Path(reporoot).expanduser().resolve()
        self.filelist_path = Path(filelist).expanduser().resolve()
        self.destdir = Path(destdir).expanduser().resolve()
        self.flatten = flatten

    def run(self):
        '''Read the file list, copy each existing file, report results.'''

        if not self.reporoot.is_dir():
            sys.exit(f"Repo root not found or not a directory: {self.reporoot}")
        if not self.filelist_path.is_file():
            sys.exit(f"File list not found: {self.filelist_path}")

        rel_paths = self._read_filelist()

        if self.destdir.exists():
            shutil.rmtree(self.destdir)
        self.destdir.mkdir(parents=True)

        copied = []
        missing = []

        for rel_path in rel_paths:
            src = self.reporoot / rel_path
            if not src.is_file():
                missing.append(rel_path)
                continue

            if self.flatten:
                dest_name = rel_path.replace('/', '__')
                dest = self.destdir / dest_name
            else:
                dest = self.destdir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(src, dest)
            copied.append(rel_path)

        self._report(copied, missing)

    def _read_filelist(self):
        '''
        :return: list of repo-relative path strings, comments/blanks stripped
        '''
        rel_paths = []
        with open(self.filelist_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                rel_paths.append(line)
        return rel_paths

    def _report(self, copied, missing):
        '''
        :param copied: list of successfully copied relative paths
        :param missing: list of relative paths not found under reporoot
        '''
        print(f"Copied {len(copied)} file(s) into {self.destdir}")
        if missing:
            print(f"\nNot found ({len(missing)}) — check paths / reporoot:")
            for rel_path in missing:
                print(f"  {rel_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Stage a curated subset of repo files for Claude "
                     "project upload."
    )
    parser.add_argument('--reporoot', required=True,
                         help="Root directory of the source repository")
    parser.add_argument('--filelist', required=True,
                         help="Text file with one repo-relative file path "
                              "per line")
    parser.add_argument('--destdir', required=True,
                         help="Destination directory for staged copies")
    parser.add_argument('--flatten', action='store_true', default=False,
                         help="Flatten paths with '__' instead of "
                              "preserving directory structure "
                              "(default: preserve structure)")
    args = parser.parse_args()

    stager = ProjectFileStager(
        reporoot=args.reporoot,
        filelist=args.filelist,
        destdir=args.destdir,
        flatten=args.flatten,
    )
    stager.run()


if __name__ == '__main__':
    main()