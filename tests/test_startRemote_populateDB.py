import os, sys, logging, datetime, django
print sys.path
sys.path.append(os.path.dirname(os.getcwd()) + "/server")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup() #To avoid the error "django.core.exceptions.AppRegistryNotReady: Models aren't loaded yet."

from services.common import misc, simulation
from services.common.testing import helpers

from services.configuration.jrpc.views import channels as jrpc_channels_if
from services.configuration.jrpc.views import rules as jrpc_rules_if
from services.configuration.jrpc.serializers import serialization as jrpc_keys
from services.scheduling.jrpc.views import groundstations as jrpc_gs_scheduling
from services.scheduling.jrpc.views import spacecraft as jrpc_sc_scheduling
from services.configuration.models import rules, availability, channels
from services.configuration import signals
from services.scheduling.models import operational


def _initDjangoDB():
    """
    This method populates the database with some information to be used
    only for this test.
    """
    __verbose_testing = False

    if not __verbose_testing:
        logging.getLogger('configuration').setLevel(level=logging.CRITICAL)
        logging.getLogger('scheduling').setLevel(level=logging.CRITICAL)

    __sc_1_id = 'humsat-sc'
    __sc_1_tle_id = 'HUMSAT-D'
    __sc_1_ch_1_id = 'humsat-fm'
    __sc_1_ch_1_cfg = {
        jrpc_keys.FREQUENCY_K: '437000000',
        jrpc_keys.MODULATION_K: 'FM',
        jrpc_keys.POLARIZATION_K: 'LHCP',
        jrpc_keys.BITRATE_K: '300',
        jrpc_keys.BANDWIDTH_K: '12.500000000'
    }

    __sc_2_id = 'beesat-sc'
    __sc_2_tle_id = 'BEESAT-2'
    __sc_2_ch_1_id = 'beesat-fm'
    __sc_2_ch_1_cfg = {
        jrpc_keys.FREQUENCY_K: '437000000',
        jrpc_keys.MODULATION_K: 'FM',
        jrpc_keys.POLARIZATION_K: 'LHCP',
        jrpc_keys.BITRATE_K: '300',
        jrpc_keys.BANDWIDTH_K: '12.500000000'
    }

    __gs_1_id = 'gs-la'
    __gs_1_ch_1_id = 'gs-la-fm'
    __gs_1_ch_1_cfg = {
        jrpc_keys.BAND_K:
        'UHF / U / 435000000.000000 / 438000000.000000',
        jrpc_keys.AUTOMATED_K: False,
        jrpc_keys.MODULATIONS_K: ['FM'],
        jrpc_keys.POLARIZATIONS_K: ['LHCP'],
        jrpc_keys.BITRATES_K: [300, 600, 900],
        jrpc_keys.BANDWIDTHS_K: [12.500000000, 25.000000000]
    }
    __gs_1_ch_2_id = 'gs-la-fm-2'
    __gs_1_ch_2_cfg = {
        jrpc_keys.BAND_K:
        'UHF / U / 435000000.000000 / 438000000.000000',
        jrpc_keys.AUTOMATED_K: False,
        jrpc_keys.MODULATIONS_K: ['FM'],
        jrpc_keys.POLARIZATIONS_K: ['LHCP'],
        jrpc_keys.BITRATES_K: [300, 600, 900],
        jrpc_keys.BANDWIDTHS_K: [12.500000000, 25.000000000]
    }

    signals.models.connect_availability_2_operational()
    signals.models.connect_channels_2_compatibility()
    signals.models.connect_compatibility_2_operational()
    signals.models.connect_rules_2_availability()
    #signals.connect_segments_2_booking_tle()

    helpers.init_available()
    helpers.init_tles_database()
    __band = helpers.create_band()

    __usr_1_name = 'crespo'
    __usr_1_pass = 'cre.spo'
    __usr_1_mail = 'crespo@crespo.gal'

    __usr_2_name = 'tubio'
    __usr_2_pass = 'tu.bio'
    __usr_2_mail = 'tubio@tubio.gal'

    # Default values: username=testuser, password=testuser.
    __user_def = helpers.create_user_profile()
    __usr_1 = helpers.create_user_profile(
        username=__usr_1_name, password=__usr_1_pass, email=__usr_1_mail)
    __usr_2 = helpers.create_user_profile(
        username=__usr_2_name, password=__usr_2_pass, email=__usr_2_mail)

    __sc_1 = helpers.create_sc(
        user_profile=__usr_1,
        identifier=__sc_1_id,
        tle_id=__sc_1_tle_id,
    )

    __sc_2 = helpers.create_sc(
        user_profile=__usr_2,
        identifier=__sc_2_id,
        tle_id=__sc_2_tle_id,
    )
    __gs_1 = helpers.create_gs(
        user_profile=__usr_2, identifier=__gs_1_id,
    )

    operational.OperationalSlot.objects.get_simulator().set_debug()
    operational.OperationalSlot.objects.set_debug()

    jrpc_channels_if.gs_channel_create(
        ground_station_id=__gs_1_id,
        channel_id=__gs_1_ch_1_id,
        configuration=__gs_1_ch_1_cfg
    )

    jrpc_rules_if.add_rule(
        __gs_1_id, __gs_1_ch_1_id,
        helpers.create_jrpc_daily_rule(
            starting_time=misc.localize_time_utc(datetime.time(
                hour=8, minute=0, second=0
            )),
            ending_time=misc.localize_time_utc(datetime.time(
                hour=23, minute=55, second=0
            ))
        )
    )

    jrpc_channels_if.sc_channel_create(
        spacecraft_id=__sc_1_id,
        channel_id=__sc_1_ch_1_id,
        configuration=__sc_1_ch_1_cfg
    )

    jrpc_channels_if.sc_channel_create(
        spacecraft_id=__sc_2_id,
        channel_id=__sc_2_ch_1_id,
        configuration=__sc_2_ch_1_cfg
    )

    sc_1_s_slots = jrpc_sc_scheduling.select_slots(
        __sc_1_id, [1, 2]
    )

    sc_2_s_slots = jrpc_sc_scheduling.select_slots(
        __sc_2_id, [3, 4]
    )

    gs_c_slots = jrpc_gs_scheduling.confirm_selections(
        __gs_1_id, [1, 2]
    )

    gs_c_slots = jrpc_gs_scheduling.confirm_selections(
        __gs_1_id, [3, 4]
    )

if __name__ == '__main__':
    _initDjangoDB()
