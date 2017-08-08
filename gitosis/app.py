import os
import sys
import logging
import optparse
import errno
import ConfigParser

from ConfigParser import NoSectionError, NoOptionError

log = logging.getLogger('gitosis.app')

class CannotReadConfigError(Exception):
    """Unable to read config file"""

    def __str__(self):
        return '%s: %s' % (self.__doc__, ': '.join(self.args))

class ConfigFileDoesNotExistError(CannotReadConfigError):
    """Configuration does not exist"""

class App(object):
    name = None

    def run(class_):
        app = class_()
        return app.main()
    run = classmethod(run)

    def main(self):
        self.setup_basic_logging()
        parser = self.create_parser()
        (options, args) = parser.parse_args()
        cfg = self.create_config(options)
        try:
            self.read_config(options, cfg)
        except CannotReadConfigError, e:
            log.error(str(e))
            sys.exit(1)
        self.read_keydir(options, cfg)

        self.setup_logging(cfg)
        self.handle_args(parser, cfg, options, args)

    def setup_basic_logging(self):
        logging.basicConfig()

    def create_parser(self):
        parser = optparse.OptionParser()
        parser.set_defaults(
            config=os.path.expanduser('~/.gitosis.conf'),
            )
        parser.add_option('--config',
                          metavar='FILE',
                          help='read config from FILE',
                          )

        return parser

    def create_config(self, options):
        cfg = ConfigParser.RawConfigParser()
        return cfg

    def read_config(self, options, cfg):
        try:
            conffile = file(options.config)
        except (IOError, OSError), e:
            if e.errno == errno.ENOENT:
                # special case this because gitosis-init wants to
                # ignore this particular error case
                raise ConfigFileDoesNotExistError(str(e))
            else:
                raise CannotReadConfigError(str(e))
        try:
            cfg.readfp(conffile)
        finally:
            conffile.close()

    def read_keydir(self, options, cfg):
        try:
            keydir = cfg.get('gitosis', 'keydir')
        except (NoSectionError, NoOptionError):
            return

        slugs = [d for d in os.listdir(keydir)
            if os.path.isdir(os.path.join(keydir, d))]

        for slug in slugs:
            section = "group %s" % slug
            cfg.add_section(section)
            slugdir = os.path.join(keydir, slug)
            keys = [os.path.splitext(os.path.basename(f))[0] for f in os.listdir(slugdir)
                if os.path.isfile(os.path.join(slugdir, f))]
            for key in keys:
                cfg.set(section, "members", " ".join(keys))
            cfg.set(section, "writable", slug)

        #cfg.read(configfiles)

    def setup_logging(self, cfg):
        try:
            loglevel = cfg.get('gitosis', 'loglevel')
        except (ConfigParser.NoSectionError,
                ConfigParser.NoOptionError):
            pass
        else:
            try:
                symbolic = logging._levelNames[loglevel]
            except KeyError:
                log.warning(
                    'Ignored invalid loglevel configuration: %r',
                    loglevel,
                    )
            else:
                logging.root.setLevel(symbolic)

    def handle_args(self, parser, cfg, options, args):
        if args:
            parser.error('not expecting arguments')
