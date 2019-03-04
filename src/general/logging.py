import gzip
import os
import shutil
from logging.handlers import TimedRotatingFileHandler


class TimedCompressedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Extended version of TimedRotatingFileHandler that compress logs on rollover.
    """
    def find_last_rotated_file(self):
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(dir_name)
        result = []
        prefix = '{}.20'.format(base_name)
        for file_name in file_names:
            if file_name.startswith(prefix) and not file_name.endswith('.gz'):
                result.append(file_name)
        result.sort()
        return os.path.join(dir_name, result[0])

    def doRollover(self):
        super(TimedCompressedRotatingFileHandler, self).doRollover()

        source = self.find_last_rotated_file()
        dest = '{}.gz'.format(source)
        with open(source, 'rb') as sf:
            with gzip.open(dest, 'wb') as df:
                shutil.copyfileobj(sf, df)
        os.remove(source)
