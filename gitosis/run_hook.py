"""
Perform gitosis actions for a git hook.
"""

import errno
import logging
import os
import sys
import shutil

from gitosis import repository
from gitosis import ssh
from gitosis import gitweb
from gitosis import gitdaemon
from gitosis import app
from gitosis import util

def post_update(cfg, git_dir=None):
    if not git_dir:
        git_dir = os.environ.get('GIT_DIR')
        if git_dir is None:
            log.error('Must have GIT_DIR set in enviroment')
            sys.exit(1)

    export = os.path.join(git_dir, 'export')
    try:
        shutil.rmtree(export)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise
    repository.export(git_dir=git_dir, path=export)

def regenerate_keys(cfg):
    authorized_keys = util.getSSHAuthorizedKeysPath(config=cfg)
    ssh.writeAuthorizedKeys(
        path=authorized_keys,
        keydir=cfg.get('gitosis', 'keydir'),
        )

class Main(app.App):
    def create_parser(self):
        parser = super(Main, self).create_parser()
        parser.set_usage('%prog [OPTS] HOOK')
        parser.set_description(
            'Perform gitosis actions for a git hook')
        return parser

    def handle_args(self, parser, cfg, options, args):
        try:
            (hook,) = args
        except ValueError:
            parser.error('Missing argument HOOK.')

        log = logging.getLogger('gitosis.run_hook')
        os.umask(0022)

        if hook == 'post-update':
            log.info('Running hook %s', hook)
            post_update(cfg)
            log.info('Done.')
        elif hook == 'regenerate-keys':
            log.info('Running hook %s', hook)
            regenerate_keys(cfg)
            log.info('Done.')
        else:
            log.warning('Ignoring unknown hook: %r', hook)
