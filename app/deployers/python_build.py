"""Deploy redistribuable Python build on the device."""

import requests
from futurelog import FutureLogger

from app.deployers.deployer import Deployer
from app.exceptions.config_exception import InvalidConfiguration
from app.logger import get_logger
from app.settings import CONF
from app.utils import upload_file

LOGGER = get_logger(__name__)
FUTURE_LOGGER = FutureLogger(__name__, CONF.log_level)

LOCAL_ARCHIVE_FILEPATH = "/tmp/python_build.tar.gz"


class PythonBuildDeployer(Deployer):
    archiveURL: str = CONF.python_build_archive_url

    @classmethod
    def download_python_build(cls) -> None:
        """Download the python build from the archive URL."""
        cls.filepath = CONF.python_build_local_directory
        cls._download_python_build()

    @classmethod
    def _download_python_build(cls) -> None:
        """Download the python build from the archive URL."""
        if not cls.archiveURL:
            raise InvalidConfiguration("python build archive URL was not specified")

        archive = requests.get(cls.archiveURL)
        archive.raise_for_status()

        with open(f"{cls.filepath}/{LOCAL_ARCHIVE_FILEPATH}", "wb") as archive_fd:
            for chunk in archive.iter_content(chunk_size=102400):
                archive_fd.write(chunk)

    ##
    # Deploy and checks
    ##

    async def check(self) -> bool:
        """Deploy redistribuable Python build is already on the device."""
        FUTURE_LOGGER.debug(self.hostname, "check python build")
        response = await self.ssh.run("/opt/salt/python/bin/python --version")
        if response.exit_status != 0:
            FUTURE_LOGGER.info(self.hostname, "check python build: failed")
            return False

        FUTURE_LOGGER.debug(self.hostname, "check python build version")
        if CONF.python_build_version not in response.stdout:
            FUTURE_LOGGER.info(
                self.hostname,
                "check python build version: failed, expected %s, got %s",
                CONF.python_build_version,
                response.stdout,
            )
            return False

        return True

    async def deploy(self) -> bool:
        """Deploy redistribuable Python build on the device."""
        uploaded = await upload_file(
            self.hostname,
            self.ssh,
            f"{self.filepath}/{LOCAL_ARCHIVE_FILEPATH}",
            "/tmp/",
            "python_build.tar.gz",
        )
        if not uploaded:
            return False

        # Extract the archive
        FUTURE_LOGGER.debug(self.hostname, "extract python build")
        response = await self.ssh.run("tar -xzf /tmp/python_build.tar.gz -C /opt/salt/")
        if response.exit_status != 0:
            FUTURE_LOGGER.info(self.hostname, "extract python build: failed")
            return False

        # Remove the archive
        FUTURE_LOGGER.debug(self.hostname, "remove python build archive")
        response = await self.ssh.run("rm -f /tmp/python_build/python_build.tar.gz")
        if response.exit_status != 0:
            FUTURE_LOGGER.info(self.hostname, "remove python build archive: failed")
            return False

        return await self.check()
