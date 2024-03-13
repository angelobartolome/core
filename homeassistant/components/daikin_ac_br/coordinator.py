"""Example integration using DataUpdateCoordinator."""

from asyncio import timeout
from datetime import timedelta
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class DaikinACBRCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Daikin_AC_BR",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10),
        )
        self.api = api
        print("DaikinACBRCoordinator.__init__", self.api)

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with timeout(10):
                return await self.hass.async_add_executor_job(self.api.fetch_data)

        except ApiAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")


class ApiAuthError(Exception):
    """Error to indicate there is an API authentication error."""

    def __init__(self, message):
        """Initialize the error."""
        super().__init__(message)


class ApiError(Exception):
    """Error to indicate there is an API error."""

    def __init__(self, message):
        """Initialize the error."""
        super().__init__(message)
