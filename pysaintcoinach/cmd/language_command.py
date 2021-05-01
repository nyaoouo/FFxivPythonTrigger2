import logging

from . import IXivShellCommandMixin
from .. import ex

logger = logging.getLogger('xivshell')


class LanguageCommand(IXivShellCommandMixin):

    def help_lang(self):
        languages = list(map(lambda x: (x[1].name.title().replace('_', ' '), x[1].value),
                             filter(lambda i: i[1] != ex.Language.none and
                                              i[1] != ex.Language.unsupported,
                                    ex.Language.__members__.items())))
        print("""
\tChange the language.

\tAvailable languages:
{0}
""".format('\n'.join(["\t * %-3s = %s" % (x[1], x[0]) for x in languages])))

    def do_lang(self, args: str):
        """
        Change the language.
        """

        if len(args.strip()) == 0:
            logger.info('Current language: %s (%s)',
                        self._realm.game_data.active_language.name.title().replace('_', ' '),
                        self._realm.game_data.active_language.value)
            return False

        valid_languages = filter(lambda i: i != ex.Language.none and
                                           i != ex.Language.unsupported,
                                 ex.Language.__members__.values())

        # For now, let's just accept codes only...
        try:
            language = ex.Language(args.strip().lower())
            if language not in valid_languages:
                logger.error('Unknown language.')
                return False

            self._realm.game_data.active_language = language
            logger.info('Current language changed to: %s (%s)',
                        self._realm.game_data.active_language.name.title().replace('_', ' '),
                        self._realm.game_data.active_language.value)
            return False
        except ValueError as e:
            logger.error('Unknown language.')
            return False
