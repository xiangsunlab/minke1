import subprocess

import luigi
import luigi.file


class GaussianLogFileTarget(luigi.file.LocalTarget):

    def _is_complete(self):
        with self.open() as stream:
            pass

    def exists(self):
        if not super().exists():
            return False
        
        return self._is_complete()
